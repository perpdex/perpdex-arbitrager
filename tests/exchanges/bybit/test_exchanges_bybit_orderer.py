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
@pytest.mark.parametrize('symbol, lot_size', [('BTCUSD', 1), ('BTCUSDT', 0.0010)])
def test_bybit_orderer(symbol, lot_size):
    orderer = bybit.BybitOrderer(
        config=bybit.BybitOrdererConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
        )
    )
    # configuration for testnet
    orderer._bybit.set_sandbox_mode(True)

    getter = bybit.BybitRestPositionGetter(
        config=bybit.BybitRestPositionGetterConfig(
            api_key=os.environ["BYBIT_API_KEY"],
            secret=os.environ["BYBIT_SECRET"],
            symbol=symbol,
        )
    )
    # configuration for testnet
    getter._bybit.set_sandbox_mode(True)

    # long
    pos0 = getter.current_position()
    orderer.post_market_order(symbol=symbol, side_int=1, size=lot_size)
    pos1 = getter.current_position()

    assert pos0 + lot_size == pytest.approx(pos1)

    # short
    orderer.post_market_order(symbol=symbol, side_int=-1, size=lot_size)
    pos2 = getter.current_position()

    assert pos1 - lot_size == pytest.approx(pos2)

    # teardown
    if pos2 == pytest.approx(0):
        return
    orderer.post_market_order(symbol=symbol,
                              side_int=1 if pos2 < 0 else -1,
                              size=abs(pos2))
