from dataclasses import dataclass
import pybotters

import ccxt


@dataclass
class BybitRestPositionGetterConfig:
    api_key: str
    secret: str
    symbol: str
    testnet: bool = False


class BybitRestPositionGetter:
    """
    - https://github.com/ccxt/ccxt/blob/master/python/ccxt/bybit.py
    - https://docs.ccxt.com/en/latest/manual.html#position-structure
    """
    def __init__(self, config: BybitRestPositionGetterConfig):
        self._bybit = ccxt.bybit({
            'apiKey': config.api_key,
            'secret': config.secret,
        })
        self._position_type = _position_type(config.symbol)
        self._config = config

        self._bybit.set_sandbox_mode(config.testnet)

    def current_position(self) -> int:
        positions = self._bybit.fetch_positions(symbols=[self._config.symbol])
        if len(positions) == 0:
            return 0
    
        total = 0.0
        for pos in positions:
            base_size = pos['contracts']
            if base_size is None:
                continue
            side_sign = 1 if pos['side'] == 'long' else -1
            total += base_size * side_sign
        return self._position_type(total)


@dataclass
class BybitWsPositionGetterConfig:
    symbol: str


class BybitWsPositionGetter:
    def __init__(
            self,
            store: pybotters.BybitInverseDataStore or pybotters.BybitUSDTDataStore,
            config: BybitWsPositionGetterConfig):

        self._store = store
        self._config = config
        self._position_type = _position_type(config.symbol)

        self._current_position = 0

    def current_position(self) -> float or int:
        pos_dict = self._store.position.one(self._config.symbol)
        pos_dict2 = self._store.position.both(self._config.symbol)
        print('----------', self._config.symbol)
        print(pos_dict)
        print(pos_dict2)

        if pos_dict is None or pos_dict['side'] is None:
            pos = 0.0
        else:
            side_int = 1 if pos_dict['side'] == 'Buy' else -1
            size_with_sign = float(pos_dict['size']) * side_int
            pos = size_with_sign

        return self._position_type(pos)


def _position_type(symbol: str):
    # linear or spot (Coin)
    if 'USDT' in symbol:
        return float

    # inverse (USD)
    return int
