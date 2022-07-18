import asyncio
import os

import pytest
from src.exchanges import bybit

skip_if_secret_not_set = pytest.mark.skipif(
    (
        os.environ.get('BYBIT_API_KEY') is None) or (
        os.environ.get('BYBIT_SECRET') is None
    ),
    reason='bybit secret not set (maybe run in CI)'
)


@skip_if_secret_not_set
@pytest.mark.parametrize('symbol, position_type', [('BTCUSD', int), ('BTCUSDT', float)])
def test_bybit_rest_position_getter(symbol, position_type):
    getter = bybit.BybitRestPositionGetter(
        config=bybit.BybitRestPositionGetterConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
            symbol=symbol,
            testnet=True,
        )
    )
    # configuration for testnet
    getter._bybit.set_sandbox_mode(True)

    assert type(getter.current_position()) is position_type


@pytest.mark.asyncio
@skip_if_secret_not_set
@pytest.mark.parametrize('symbol, lot_size', [('BTCUSD', 1), ('BTCUSDT', 0.0010)])
async def test_bybit_ws_position_getter(symbol, lot_size):
    if 'USDT' in symbol:
        client, store = await bybit.start_bybit_ws_linear(
            api_key=os.environ['BYBIT_API_KEY'],
            secret=os.environ['BYBIT_SECRET'],
            symbols=[symbol],
            testnet=True,
        )
    else:
        client, store = await bybit.start_bybit_ws_inverse(
            api_key=os.environ['BYBIT_API_KEY'],
            secret=os.environ['BYBIT_SECRET'],
            symbols=[symbol],
            testnet=True,
        )

    try:
        await asyncio.wait_for(store.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        print('asyncio.wait_for(store.wait(), timeout=1.0) timeout')

    getter = bybit.BybitWsPositionGetter(
        store=store,
        config=bybit.BybitWsPositionGetterConfig(
            symbol=symbol,
        )
    )

    orderer = bybit.BybitOrderer(
        config=bybit.BybitOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    orderer._bybit.set_sandbox_mode(True)
    try:
        orderer._bybit.set_position_mode(hedged=False, symbol=symbol)
    except BaseException:
        ...

    pos = getter.current_position()

    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    await asyncio.sleep(0.100)
    assert getter.current_position() == pos + lot_size

    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size)
    await asyncio.sleep(0.100)
    assert getter.current_position() == pos

    if pos == 0:
        return

    orderer.post_market_order(symbol=symbol, side_int=1 if pos < 0 else -1, size=abs(pos))
    await asyncio.sleep(0.100)
    assert getter.current_position() == 0
