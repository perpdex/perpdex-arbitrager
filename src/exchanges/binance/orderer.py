import ccxt


class BinanceOrderer:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py
    - https://docs.ccxt.com/en/latest/manual.html#order-structure
    """
    def __init__(self, ccxt_exchange: ccxt.binance):
        self._ccxt_exchange = ccxt_exchange

    def post_market_order(self, symbol: str, side_int: int, size: float) -> dict:
        side = _to_side_str(side_int)
        size = _cast_size(size, symbol)
        return self._ccxt_exchange.create_order(symbol, 'market', side, size)

    def post_limit_order(self, symbol: str, side_int: int, size: float, price: float) -> dict:
        side = _to_side_str(side_int)
        size = _cast_size(size, symbol)
        return self._ccxt_exchange.create_order(symbol, 'limit', side, size, price)

    def cancel_limit_order(self, symbol: str, order_id: str) -> dict:
        return self._ccxt_exchange.cancel_order(order_id)


def _cast_size(size: float, symbol: str):
    # linear or spot (Coin)
    if 'USDT' in symbol:
        return float(size)

    # inverse (USD)
    return int(size)


def _to_side_str(side_int: int):
    if side_int > 0:
        return 'buy'
    if side_int < 0:
        return 'sell'
    raise ValueError
