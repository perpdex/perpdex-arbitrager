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
@pytest.mark.parametrize('symbol, lot_size', [('BTCUSDT', 0.001), ('BTCUSD_PERP', 1)])
def test_binance_orderer(symbol, lot_size):
    default_type = binance.ccxt_default_type(symbol=symbol)
    ccxt_exchange = ccxt.binance({
        'apiKey': os.environ['BINANCE_API_KEY'],
        'secret': os.environ['BINANCE_SECRET'],
        'options': {'defaultType': default_type},
    })
    ccxt_exchange.set_sandbox_mode(True)
    binance._set_leverageBrackets(ccxt_exchange, symbol)

    orderer = binance.BinanceOrderer(ccxt_exchange=ccxt_exchange)
    getter = binance.BinanceRestPositionGetter(
        ccxt_exchange=ccxt_exchange,
        symbol=symbol,
    )

    # long
    pos0 = getter.current_position()
    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    pos1 = getter.current_position()

    assert pos0 + lot_size == pytest.approx(pos1)

    # short
    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size * 2)
    pos2 = getter.current_position()

    assert pos1 - lot_size * 2 == pytest.approx(pos2)

    # teardown
    if pos2 == pytest.approx(0):
        return
    orderer.post_market_order(symbol=symbol,
                              side_int=1 if pos2 < 0 else -1,
                              size=abs(pos2))
