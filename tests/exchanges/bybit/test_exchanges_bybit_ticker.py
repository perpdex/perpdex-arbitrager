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


@pytest.mark.parametrize('symbol', ['BTCUSD', 'BTCUSDT'])
def test_bybit_rest_ticker(symbol):
    ticker = bybit.BybitRestTicker(
        config=bybit.BybitRestTickerConfig(
            symbol=symbol,
            update_limit_sec=0.0001
        )
    )

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0


@skip_if_secret_not_set
@pytest.mark.asyncio
@pytest.mark.parametrize('symbol, lot_size', (('BTCUSD', 10), ('BTCUSDT', 0.001)))
async def test_bybit_ws_ticker(symbol, lot_size):
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

    ticker = bybit.BybitWsTicker(
        store=store,
        config=bybit.BybitWsTickerConfig(
            symbol=symbol,
        )
    )

    # rarely exectuted on testnet, so trade bymyself
    orderer = bybit.BybitOrderer(
        config=bybit.BybitOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    orderer._bybit.set_sandbox_mode(True)
    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size)

    await asyncio.sleep(2)

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0

    await client.close()
