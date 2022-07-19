import json
from logging import getLogger
import time
from dataclasses import dataclass
from ..contracts.utils import get_contract_from_abi_json

import web3

Q96: int = 0x1000000000000000000000000  # same as 1 << 96
MAX_UINT: int = int(web3.constants.MAX_INT, base=16)
DECIMALS: int = 18


@dataclass
class PerpdexContractTickerConfig:
    market_contract_abi_json_filepath: str
    update_limit_sec: float = 0.5


class PerpdexContractTicker:
    def __init__(self, w3, config: PerpdexContractTickerConfig):
        self._w3 = w3
        self._config = config

        self._market_contract = get_contract_from_abi_json(
            w3,
            config.market_contract_abi_json_filepath,
        )

        self._mark_price = 0.0
        self._last_ts = 0.0

    def bid_price(self):
        return self._get_mark_price()

    def ask_price(self):
        return self._get_mark_price()

    def last_price(self):
        return self._get_mark_price()

    def _get_mark_price(self) -> float:
        if time.time() - self._last_ts >= self._config.update_limit_sec:
            price_x96 = self._market_contract.functions.getMarkPriceX96().call()
            self._mark_price = price_x96 / Q96
        return self._mark_price


@dataclass
class PerpdexOrdererConfig:
    market_contract_abi_json_filepaths: list
    exchange_contract_abi_json_filepath: str


class PerpdexOrderer:
    def __init__(self, w3, config: PerpdexOrdererConfig):
        self._w3 = w3
        self._config = config
        self._logger = getLogger(__name__)

        self._exchange_contract = get_contract_from_abi_json(
            w3,
            config.exchange_contract_abi_json_filepath,
        )

        self._symbol_to_market_address: dict = {}
        for filepath in config.market_contract_abi_json_filepaths:
            contract = get_contract_from_abi_json(w3, filepath)
            symbol = contract.functions.symbol().call()
            self._symbol_to_market_address[symbol] = contract.address

    def post_market_order(self, symbol: str, side_int: int, size: float):
        self._logger.info('post_market_order symbol {} side_int {} size {}'.format(
            symbol, side_int, size))

        assert side_int != 0

        if symbol not in self._symbol_to_market_address:
            raise ValueError(f"market address not initialized: {symbol=}")

        # get market address from symbol string
        market = self._symbol_to_market_address[symbol]

        # calculate amount with decimals from size
        amount = int(size * (10 ** DECIMALS))

        tx_hash = self._exchange_contract.functions.trade(dict(
            trader=self._w3.eth.default_account,
            market=market,
            isBaseToQuote=(side_int < 0),
            isExactInput=(side_int < 0),  # same as isBaseToQuote
            amount=amount,
            oppositeAmountBound=0 if (side_int < 0) else MAX_UINT,
            deadline=_get_deadline(),
        )).transact()
        self._w3.eth.wait_for_transaction_receipt(tx_hash)


@dataclass
class PerpdexPositionGetterConfig:
    market_contract_abi_json_filepath: str
    exchange_contract_abi_json_filepath: str


class PerpdexPositionGetter:
    def __init__(self, w3, config: PerpdexPositionGetterConfig):
        self._w3 = w3
        self._config = config

        self._market_contract = get_contract_from_abi_json(
            w3,
            config.market_contract_abi_json_filepath,
        )
        self._exchange_contract = get_contract_from_abi_json(
            w3,
            config.exchange_contract_abi_json_filepath,
        )

    def current_position(self) -> float:
        base_share = self._exchange_contract.functions.getPositionShare(
            self._w3.eth.default_account,
            self._market_contract.address,
        ).call()
        return base_share / (10 ** DECIMALS)


def _get_deadline():
    return int(time.time()) + 2 * 60
