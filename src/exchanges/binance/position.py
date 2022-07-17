import ccxt
import pybotters


class BinanceRestPositionGetter:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/binance.py
    - https://docs.ccxt.com/en/latest/manual.html#position-structure
    """
    def __init__(self, ccxt_exchange: ccxt.binance, symbol: str):
        self._ccxt_exchange = ccxt_exchange
        self._symbol = symbol
        self._position_type = _position_type(symbol)

    def current_position(self) -> float or int:
        # FIXME: https://github.com/ccxt/ccxt/issues/14384
        # Monkey patching to match the symbol.
        _symbol = self._symbol.replace('USD_PERP', '/USD').replace('USDT', '/USDT')

        positions = self._ccxt_exchange.fetch_positions(symbols=[_symbol])
        if len(positions) == 0:
            return self._position_type(0)
    
        total = 0.0
        for pos in positions:
            base_size = pos['contracts']
            if base_size is None:
                continue
            side_sign = 1 if pos['side'] == 'long' else -1
            total += base_size * side_sign
        return self._position_type(total)


class BinanceWsPositionGetter:
    def __init__(
            self,
            store: pybotters.BinanceDataStore,
            symbol: str):
        
        self._store = store
        self._symbol = symbol
        self._position_type = _position_type(symbol)

        self._current_position = 0

    def current_position(self) -> float or int:
        # [{'s': 'BTCUSDT', 'pa': '0.000', 'ep': '0.0', 'up': '0.00000000', 'mt': 'cross', 'iw': '0', 'ps': 'BOTH'}]
        pos_dicts = self._store.position.find({'s': self._symbol})
        pos = 0.0
        for pos_dict in pos_dicts:
            pos += float(pos_dict['pa'])

        return self._position_type(pos)


def _position_type(symbol: str):
    # linear or spot (Coin)
    if 'USDT' in symbol:
        return float

    # inverse (USD)
    return int
