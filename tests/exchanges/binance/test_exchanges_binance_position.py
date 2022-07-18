import asyncio
import os

import ccxt
import pytest
from src.exchanges import binance

skip_if_secret_not_set = pytest.mark.skipif(
    (
        os.environ.get('BINANCE_API_KEY') is None) or (
        os.environ.get('BINANCE_SECRET') is None
    ),
    reason='binance secret not set (maybe run in CI)'
)


@skip_if_secret_not_set
@pytest.mark.parametrize('symbol, position_type', [('BTCUSDT', float), ('BTCUSD_PERP', int)])
def test_binance_rest_position_getter(symbol, position_type):
    default_type = binance.ccxt_default_type(symbol=symbol)
    ccxt_exchange = ccxt.binance({
        'apiKey': os.environ['BINANCE_API_KEY'],
        'secret': os.environ['BINANCE_SECRET'],
        'options': {'defaultType': default_type},
    })
    ccxt_exchange.set_sandbox_mode(True)
    binance._set_leverageBrackets(ccxt_exchange, symbol)

    getter = binance.BinanceRestPositionGetter(
        ccxt_exchange=ccxt_exchange,
        symbol=symbol,
    )

    assert type(getter.current_position()) is position_type


@skip_if_secret_not_set
@pytest.mark.asyncio
@pytest.mark.parametrize('symbol, lot_size', [('BTCUSDT', 0.001), ('BTCUSD_PERP', 1)])
async def test_binance_ws_position_getter(symbol, lot_size):
    if 'USDT' in symbol:
        client, store = await binance.start_binance_ws_linear(
            api_key=os.environ['BINANCE_API_KEY'],
            secret=os.environ['BINANCE_SECRET'],
            symbols=[symbol],
            testnet=True,
        )
    else:
        client, store = await binance.start_binance_ws_inverse(
            api_key=os.environ['BINANCE_API_KEY'],
            secret=os.environ['BINANCE_SECRET'],
            symbols=[symbol],
            testnet=True,
        )

    try:
        await asyncio.wait_for(store.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        print('asyncio.wait_for(store.wait(), timeout=1.0) timeout')

    getter = binance.BinanceWsPositionGetter(
        store=store,
        symbol=symbol,
    )

    default_type = binance.ccxt_default_type(symbol=symbol)
    ccxt_exchange = ccxt.binance({
        'apiKey': os.environ['BINANCE_API_KEY'],
        'secret': os.environ['BINANCE_SECRET'],
        'options': {'defaultType': default_type},
    })
    ccxt_exchange.set_sandbox_mode(True)
    binance._set_leverageBrackets(ccxt_exchange, symbol)

    orderer = binance.BinanceOrderer(ccxt_exchange=ccxt_exchange)
    try:
        orderer._binance.set_position_mode(hedged=False, symbol=symbol)
    except BaseException:
        ...

    pos = getter.current_position()

    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    await asyncio.sleep(0.100)
    pos1 = getter.current_position()
    assert pos1 == pos + lot_size

    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size * 2)
    await asyncio.sleep(0.100)
    pos2 = getter.current_position()
    assert pos2 == pos1 - lot_size * 2

    if pos2 == 0:
        return

    orderer.post_market_order(symbol=symbol, side_int=1 if pos2 < 0 else -1, size=abs(pos2))
    await asyncio.sleep(0.100)
    assert getter.current_position() == 0
