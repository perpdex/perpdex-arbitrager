from src.exchanges import binance


def test_binance_rest_ticker():
    ticker = binance.BinanceRestTicker(
        config=binance.BinanceRestTickerConfig(
            symbol='BTC/USD',
            update_limit_sec=0.0001
        )
    )

    assert ticker.bid_price() > 0
    assert ticker.ask_price() > 0
    assert ticker.last_price() > 0
