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


def test_bybit_inverse_rest_ticker():
    ticker = bybit.BybitInverseRestTicker(
        config=bybit.BybitInverseRestTickerConfig(
            symbol='BTCUSD',
            update_limit_sec=0.0001
        )
    )

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0


@pytest.mark.asyncio
@skip_if_secret_not_set
async def test_bybit_inverse_ws_ticker():
    ticker = bybit.BybitInverseWebsocketTicker(
        config=bybit.BybitInverseWebsocketTickerConfig(
            symbol='BTCUSD',
            testnet=True,
        )
    )
    ticker.start()

    await asyncio.sleep(2)

    # rarely exectuted on testnet, so trade bymyself
    orderer = bybit.BybitInverseOrderer(
        config=bybit.BybitInverseOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    orderer._bybit.set_sandbox_mode(True)
    orderer.post_market_order(symbol='BTCUSD', side_int=1, size=10)
    orderer.post_market_order(symbol='BTCUSD', side_int=-1, size=10)

    await asyncio.sleep(2)

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0
       

@skip_if_secret_not_set
def test_bybit_inverse_rest_position_getter():
    getter = bybit.BybitInverseRestPositionGetter(
        config=bybit.BybitInverseRestPositionGetterConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
            symbol='BTCUSD',
        )
    )
    # configuration for testnet
    getter._bybit.set_sandbox_mode(True)

    assert type(getter.current_position()) is int


@pytest.mark.asyncio
@skip_if_secret_not_set
async def test_bybit_inverse_websocket_position_getter():
    getter = bybit.BybitInverseWebsocketPositionGetter(
        config=bybit.BybitInverseWebsocketPositionGetterConfig(
            api_key=os.environ['BYBIT_API_KEY'],
            secret=os.environ['BYBIT_SECRET'],
            symbol='BTCUSD',
            testnet=True,
        )
    )
    await asyncio.sleep(2)

    orderer = bybit.BybitInverseOrderer(
        config=bybit.BybitInverseOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    orderer._bybit.set_sandbox_mode(True)

    pos = getter.current_position()

    orderer.post_market_order(symbol='BTCUSD', side_int=1, size=10)
    await asyncio.sleep(0.100)
    assert getter.current_position() == pos + 10

    orderer.post_market_order(symbol='BTCUSD', side_int=-1, size=10)
    await asyncio.sleep(0.100)
    assert getter.current_position() == pos

    if pos == 0:
        return

    orderer.post_market_order(symbol='BTCUSD', side_int=1 if pos < 0 else -1, size=abs(pos))
    await asyncio.sleep(0.100)
    assert getter.current_position() == 0

    getter.finish()


@skip_if_secret_not_set
def test_bybit_inverse_orderer():
    orderer = bybit.BybitInverseOrderer(
        config=bybit.BybitInverseOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    # configuration for testnet
    orderer._bybit.set_sandbox_mode(True)

    getter = bybit.BybitInverseRestPositionGetter(
        config=bybit.BybitInverseRestPositionGetterConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
            symbol='BTCUSD',
        )
    )
    # configuration for testnet
    getter._bybit.set_sandbox_mode(True)

    # long
    pos0 = getter.current_position()
    orderer.post_market_order(symbol='BTCUSD', side_int=1, size=100)
    pos1 = getter.current_position()

    assert pos0 + 100 == pytest.approx(pos1)

    # short
    orderer.post_market_order(symbol='BTCUSD', side_int=-1, size=100)
    pos2 = getter.current_position()

    assert pos1 - 100 == pytest.approx(pos2)

    # teardown
    if pos2 == pytest.approx(0):
        return
    orderer.post_market_order(symbol='BTCUSD',
                              side_int=1 if pos2 < 0 else -1,
                              size=abs(pos2))
