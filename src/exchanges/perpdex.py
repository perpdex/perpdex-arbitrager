from logging import getLogger
import time
from dataclasses import dataclass, field
from typing import Optional
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
    max_slippage: Optional[float] = None
    tx_options: dict = field(default_factory=dict)


class PerpdexOrderer:
    def __init__(self, w3, config: PerpdexOrdererConfig):
        self._w3 = w3
        self._config = config
        self._logger = getLogger(__name__)

        self._exchange_contract = get_contract_from_abi_json(
            w3,
            config.exchange_contract_abi_json_filepath,
        )

        self._symbol_to_market_contract: dict = {}
        for filepath in config.market_contract_abi_json_filepaths:
            contract = get_contract_from_abi_json(w3, filepath)
            symbol = contract.functions.symbol().call()
            self._symbol_to_market_contract[symbol] = contract

    def post_market_order(self, symbol: str, side_int: int, size: float):
        self._logger.info('post_market_order symbol {} side_int {} size {}'.format(
            symbol, side_int, size))

        assert side_int != 0

        if symbol not in self._symbol_to_market_contract:
            raise ValueError(f"market address not initialized: {symbol=}")

        # get market address from symbol string
        market_contract = self._symbol_to_market_contract[symbol]
        share_price = market_contract.functions.getShareMarkPriceX96().call() / Q96
        self._logger.debug('share_price {}'.format(share_price))

        # calculate amount with decimals from size
        amount = int(size * (10 ** DECIMALS))

        retry_count = 32
        for i in range(retry_count):
            if self._config.max_slippage is None:
                opposite_amount_bound = 0 if (side_int < 0) else MAX_UINT
            else:
                opposite_amount_bound = int(_calc_opposite_amount_bound(
                    side_int > 0, amount, share_price, self._config.max_slippage
                ))

            self._logger.debug('amount {} opposite_amount_bound {}'.format(amount, opposite_amount_bound))

            method_call = self._exchange_contract.functions.trade(dict(
                trader=self._w3.eth.default_account,
                market=market_contract.address,
                isBaseToQuote=(side_int < 0),
                isExactInput=(side_int < 0),  # same as isBaseToQuote
                amount=amount,
                oppositeAmountBound=opposite_amount_bound,
                deadline=_get_deadline(),
            ))

            try:
                method_call.estimateGas()
            except Exception as e:
                if i == retry_count - 1:
                    raise
                amount = int(amount / 2)
                self._logger.debug(f'estimateGas raises {e=} retrying')
                continue

            tx_hash = method_call.transact(self._config.tx_options)
            self._w3.eth.wait_for_transaction_receipt(tx_hash)
            break


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

    def unit_leverage_lot(self) -> float:
        account_value = self._exchange_contract.functions.getTotalAccountValue(
            self._w3.eth.default_account,
        ).call() / (10 ** DECIMALS)
        share_price = self._market_contract.functions.getShareMarkPriceX96().call() / Q96
        return account_value / share_price


@dataclass
class PerpdexLiquidityRebalancerConfig:
    market_contract_abi_json_filepath: str
    exchange_contract_abi_json_filepath: str
    target_leverage: float
    rebalance_ratio: float
    max_slippage: float = 1.0
    tx_options: dict = field(default_factory=dict)


class PerpdexLiquidityRebalancer:
    def __init__(self, w3, config: PerpdexLiquidityRebalancerConfig):
        self._w3 = w3
        self._config = config

        assert 0 < config.rebalance_ratio <= 1
        assert 0 < config.target_leverage
        assert 0 < config.max_slippage <= 1

        self._market_contract = get_contract_from_abi_json(
            w3,
            config.market_contract_abi_json_filepath,
        )
        self._exchange_contract = get_contract_from_abi_json(
            w3,
            config.exchange_contract_abi_json_filepath,
        )

        self._logger = getLogger(__class__.__name__)

    def rebalance(self):
        self._remove_liquidity()
        self._add_liquidity()

    def _remove_liquidity(self):
        liquidity = self._get_liquidity()
        liquidity_to_remove = int(liquidity * self._config.rebalance_ratio)
        if liquidity_to_remove == 0:
            self._logger.info("skip rebalancer removeLiquidity because liquidity to remove is zero")
            return

        if self._config.max_slippage == 1.0:
            min_base = 0
            min_quote = 0
        else:
            liq_base, liq_quote = self._market_contract.functions.getLiquidityValue(liquidity_to_remove).call()
            min_base = int(liq_base * (1 - self._config.max_slippage))
            min_quote = int(liq_quote * (1 - self._config.max_slippage))

        self._logger.debug(
            "rebalancer removeLiquidity (liquidity, minBase, minQuote) = ({}, {}, {}))".format(
                liquidity_to_remove, min_base, min_quote))
        method_call = self._exchange_contract.functions.removeLiquidity(dict(
            trader=self._w3.eth.default_account,
            market=self._market_contract.address,
            liquidity=liquidity_to_remove,
            minBase=min_base,
            minQuote=min_quote,
            deadline=_get_deadline(),
        ))

        try:
            method_call.estimateGas()
        except Exception as e:
            self._logger.info("rebalancer removeLiquidity estimateGas failed: {}".format(e))
            return

        tx_hash = method_call.transact(self._config.tx_options)
        self._w3.eth.wait_for_transaction_receipt(tx_hash)

    def _add_liquidity(self):
        account_value = self._exchange_contract.functions.getTotalAccountValue(
            self._w3.eth.default_account,
        ).call()

        share_price = self._market_contract.functions.getShareMarkPriceX96().call() / Q96

        target_quote = int(account_value * (self._config.target_leverage / 2))
        target_base = int(target_quote / share_price)

        liquidity = self._get_liquidity()
        liq_base, liq_quote = self._market_contract.functions.getLiquidityValue(liquidity).call()

        base = target_base - liq_base
        quote = target_quote - liq_quote

        if base <= 0 or quote <= 0:
            self._logger.info("Skip rebalancer addLiquidity (base, quote) = ({}, {})".format(base, quote))
            return

        min_base = int(base * (1 - self._config.max_slippage))
        min_quote = int(quote * (1 - self._config.max_slippage))

        self._logger.debug(
            "rebalancer addLiquidity (base, quote, minBase, minQuote) = ({}, {}, {}, {})".format(
                base, quote, min_base, min_quote))
        tx_hash = self._exchange_contract.functions.addLiquidity(dict(
            market=self._market_contract.address,
            base=base,
            quote=quote,
            minBase=min_base,
            minQuote=min_quote,
            deadline=_get_deadline(),
        )).transact(self._config.tx_options)
        self._w3.eth.wait_for_transaction_receipt(tx_hash)

    def _get_liquidity(self):
        liquidity, _, _ = self._exchange_contract.functions.getMakerInfo(
            self._w3.eth.default_account,
            self._market_contract.address,
        ).call()
        return liquidity


def _get_deadline():
    return int(time.time()) + 2 * 60


def _calc_opposite_amount_bound(is_long, share, share_price, slippage):
    opposite_amount_center = share * share_price
    if is_long:
        return opposite_amount_center * (1 + slippage)
    else:
        return opposite_amount_center * (1 - slippage)
