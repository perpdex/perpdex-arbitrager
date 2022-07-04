import json
import os
import time

import web3

# Perpdex uses 96 bit for fractional number
Q96: int = ...
MAX_INT: int = int(web3.constants.MAX_INT, base=16)


class PerpdexTickerConfig:
    update_limit_sec: float = 0.5


class PerpdexTicker:
    def __init__(self, w3, config: PerpdexTickerConfig):
        self._w3 = w3
        self._config = config

        self._market_contract = _get_contract_from_perpdex_dir(w3, 'PerpdexMarket.json')

        self._mark_price
        self._last_ts = 0.0

    def bid_price(self):
        return self._get_mark_price()

    def ask_price(self):
        return self._get_mark_price()

    def last_price(self):
        return self._get_mark_price()

    def _get_mark_price(self) -> float:
        if time.time() - self._last_ts >= self._config.update_limit_sec:
            self._mark_price = self._market_contract.functions.getMarkPriceX96().call() / Q96
        return self._mark_price


class PerpdexOrderer:
    def __init__(self, w3):
        self._w3 = w3

        self._exchange_contract = _get_contract_from_perpdex_dir(w3, 'PerpdexExchange.json')

    def post_market_order(self, symbol: str, side_int: int, size: float):
        market = _symbol_to_market_address(symbol)

        tx_hash = self._exchange_contract.functions.trade(dict(
            trader=self._w3.eth.default_account.address,
            market=market,
            is_base_to_quote=side_int < 0,
            is_exact_input=side_int < 0,
            amount=size,
            oppositeAmountBound=0,
            deadline=MAX_INT,
        )).transact()
        self._w3.eth.wait_for_transaction_receipt(tx_hash)


class PerpdexPositionGetterConfig:
    symbol: str


class PerpdexPositionGetter:
    def __init__(self, w3, config: PerpdexPositionGetterConfig):
        self._w3 = w3
        self._config = config
    
        self._exchange_contract = _get_contract_from_perpdex_dir(w3, 'PerpdexExchange.json')

    def current_position(self):
        market = _symbol_to_market_address(self._config.symbol)
        base_share = self._perpdex_exchange.functions.getOpenPositionShare(dict(
            trader=self._w3.eth.default_account.address,
            market=market,
        )).call()
        return base_share


def _symbol_to_market_address(symbol: str) -> str:
    ret = _get_abi_json_from_perpdex_dir(f'PerpdexMarket{symbol}.json')
    return ret['address']


def _get_abi_json_from_perpdex_dir(filename: str):
    filepath = os.path.join(
        os.environ['PERPDEX_ABI_JSON_DIRPATH'], filename)
    with open(filepath) as f:
        ret = json.load(f)
    return ret


def _get_contract_from_perpdex_dir(w3, filename: str):
    abi = _get_abi_json_from_perpdex_dir(filename)
    contract = w3.eth.contract(
        address=abi['address'],
        abi=abi['abi'],
    )
    return contract
