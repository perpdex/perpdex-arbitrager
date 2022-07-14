import os
import pytest
from src.exchanges import binance


skip_if_secret_not_set = pytest.mark.skipif(
    (
        os.environ.get('BINANCE_API_KEY') is None) or (
        os.environ.get('BINANCE_SECRET') is None
    ),
    reason='binance secret not set (maybe run in CI)'
)


def test_binance_rest_ticker():
    ticker = binance.BinanceLinearRestTicker(
        config=binance.BinanceLinearRestTickerConfig(
            symbol='BTC/USDT',
            update_limit_sec=0.0001
        )
    )

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0


@skip_if_secret_not_set
def test_binance_rest_position_getter():
    getter = binance.BinanceLinearRestPositionGetter(
        config=binance.BinanceLinearRestPositionGetterConfig(
            api_key=os.environ["BINANCE_API_KEY"],
            secret=os.environ["BINANCE_SECRET"],
            symbol='BTC/USDT',
        )
    )
    # configuration for testnet
    _set_leverageBrackets(getter._binance, symbol='BTC/USDT')
    getter._binance.set_sandbox_mode(True)

    assert type(getter.current_position()) is float


@skip_if_secret_not_set
def test_binance_orderer():
    orderer = binance.BinanceLinearOrderer(
        config=binance.BinanceLinearOrdererConfig(
            api_key=os.environ["BINANCE_API_KEY"],
            secret=os.environ["BINANCE_SECRET"],
        )
    )
    # configuration for testnet
    orderer._binance.set_sandbox_mode(True)

    getter = binance.BinanceLinearRestPositionGetter(
        config=binance.BinanceLinearRestPositionGetterConfig(
            api_key=os.environ["BINANCE_API_KEY"],
            secret=os.environ["BINANCE_SECRET"],
            symbol='BTC/USDT',
        )
    )
    # configuration for testnet
    _set_leverageBrackets(getter._binance, symbol='BTC/USDT')
    getter._binance.set_sandbox_mode(True)

    # long
    pos0 = getter.current_position()
    orderer.post_market_order(symbol='BTC/USDT', side_int=1, size=0.1)
    pos1 = getter.current_position()

    assert pos0 + 0.1 == pytest.approx(pos1)

    # short
    orderer.post_market_order(symbol='BTC/USDT', side_int=-1, size=0.1)
    pos2 = getter.current_position()

    assert pos1 - 0.1 == pytest.approx(pos2)

    # teardown
    if pos2 == pytest.approx(0):
        return
    orderer.post_market_order(symbol='BTC/USDT',
                              side_int=1 if pos2 < 0 else -1,
                              size=abs(pos2))


def _set_leverageBrackets(ccxt_binance, symbol: str):
    """
    not supported on testnet. copy & paste BTC/USDT pair result of mainnet
    https://binance-docs.github.io/apidocs/delivery/en/#notional-bracket-for-pair-user_data
    """
    if symbol == 'BTC/USDT':
        """
        getter = BinanceLinearRestPositionGetter(...)
        getter.current_position()
        getter._binance.options['leverageBrackets']['BTC/USDT']
        """
        ccxt_binance.options['leverageBrackets'] = [['0', '0.004'],
                                                    ['50000', '0.005'],
                                                    ['250000', '0.01'],
                                                    ['1000000', '0.025'],
                                                    ['10000000', '0.05'],
                                                    ['20000000', '0.1'],
                                                    ['50000000', '0.125'],
                                                    ['100000000', '0.15'],
                                                    ['200000000', '0.25'],
                                                    ['300000000', '0.5']]
    else:
        raise ValueError(f"{symbol=} not supported")
