import asyncio
import sys
from dataclasses import dataclass
from logging import getLogger
from typing import Optional


class ITargetPosCalculator:
    def target_pos(self) -> float:
        ...


class IPositionChaser:
    async def execute(self, target_size: float):
        ...


class ILiquidityRebalancer:
    def rebalance(self):
        ...


@dataclass
class ArbitragerConfig:
    trade_loop_sec: int
    rebalance_loop_sec: int
    inverse: bool


class Arbitrager:
    def __init__(
            self,
            config: ArbitragerConfig,
            target_pos_calculator: ITargetPosCalculator,
            position_chaser1: IPositionChaser,
            position_chaser2: Optional[IPositionChaser],
            liquidity_rebalancer: ILiquidityRebalancer,
    ):
        self._config = config
        self._target_pos_calculator = target_pos_calculator
        self._position_chaser1 = position_chaser1
        self._position_chaser2 = position_chaser2
        self._liquidity_rebalancer = liquidity_rebalancer
        self._logger = getLogger(__class__.__name__)

        self._task_t: asyncio.Task = None

    def health_check(self) -> bool:
        return (not self._task_m.done()) and (not self._task_t.done())

    def start(self):
        self._logger.debug('start')
        self._task_t = asyncio.create_task(self._trade())
        self._task_m = asyncio.create_task(self._rebalance())

    async def _trade(self):
        self._logger.debug('_trade')
        try:
            while True:
                target_pos = self._target_pos_calculator.target_pos()
                self._logger.debug('arb loop target_pos {}'.format(target_pos))

                tasks = [self._position_chaser1.execute(target_size=target_pos)]
                if self._position_chaser2 is not None:
                    target_pos2 = self._calc_target_pos2(target_pos)
                    self._logger.debug('target_pos2 {}'.format(target_pos2))
                    tasks.append(self._position_chaser2.execute(target_size=target_pos2))
                await asyncio.gather(*tasks)

                await asyncio.sleep(self._config.trade_loop_sec)
        except BaseException:
            self._logger.error(sys.exc_info(), exc_info=True)

    async def _rebalance(self):
        self._logger.debug('_rebalance')
        try:
            while True:
                self._liquidity_rebalancer.rebalance()
                await asyncio.sleep(self._config.rebalance_loop_sec)
        except BaseException:
            self._logger.error(sys.exc_info(), exc_info=True)

    def _calc_target_pos2(self, target_pos):
        # TODO: convert share to amount
        if self._config.inverse:
            raise Exception('not implemented')
        else:
            return -target_pos
