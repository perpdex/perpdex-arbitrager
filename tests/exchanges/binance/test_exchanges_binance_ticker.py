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


@pytest.mark.parametrize('symbol', [('BTCUSDT'), ('BTCUSD_PERP')])
def test_binance_rest_ticker(symbol):
    default_type = binance.ccxt_default_type(symbol=symbol)
    ccxt_exchange = ccxt.binance({'options': {'defaultType': default_type}})
    ticker = binance.BinanceRestTicker(
        ccxt_exchange=ccxt_exchange,
        symbol=symbol,
        update_limit_sec=0.0001
    )

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0


# symbol:
# - linear:  https://testnet.binancefuture.com/fapi/v1/exchangeInfo
# - inverse: https://testnet.binancefuture.com/dapi/v1/exchangeInfo
@skip_if_secret_not_set
@pytest.mark.asyncio
@pytest.mark.parametrize('symbol, lot_size', [('BTCUSDT', 0.001), ('BTCUSD_PERP', 1)])
async def test_binance_ws_ticker(symbol, lot_size):
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

    ticker = binance.BinanceWsTicker(store=store, symbol=symbol)

    # rarely exectuted on testnet, so trade bymyself
    default_type = binance.ccxt_default_type(symbol=symbol)
    ccxt_exchange = ccxt.binance({
        'apiKey': os.environ['BINANCE_API_KEY'],
        'secret': os.environ['BINANCE_SECRET'],
        'options': {'defaultType': default_type},
    })
    ccxt_exchange.set_sandbox_mode(True)

    orderer = binance.BinanceOrderer(ccxt_exchange=ccxt_exchange)

    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size)

    await asyncio.sleep(2)

    assert ticker.last_price() > 0
    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0

    await client.close()
