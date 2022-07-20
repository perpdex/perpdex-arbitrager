import asyncio
import sys
from dataclasses import dataclass
from logging import getLogger
from typing import Optional


class ITargetPosCalculator:
    def target_pos(self) -> float:
        ...


class ISecondaryPosCalculator:
    def target_pos2(self, target_pos1: float) -> float:
        ...


class IPositionChaser:
    async def execute(self, target_size: float):
        ...


@dataclass
class ArbitragerConfig:
    trade_loop_sec: int


class Arbitrager:
    def __init__(
            self,
            config: ArbitragerConfig,
            pos_calculator1: ITargetPosCalculator,
            pos_calculator2: Optional[ISecondaryPosCalculator],
            position_chaser1: IPositionChaser,
            position_chaser2: Optional[IPositionChaser],
    ):
        self._config = config
        self._pos_calculator1 = pos_calculator1
        self._pos_calculator2 = pos_calculator2
        self._position_chaser1 = position_chaser1
        self._position_chaser2 = position_chaser2
        self._logger = getLogger(__name__)

        self._task: asyncio.Task = None

    def health_check(self) -> bool:
        return not self._task.done()

    def start(self):
        self._logger.debug('start')
        self._task = asyncio.create_task(self._trade())

    async def _trade(self):
        self._logger.debug('_trade')
        try:
            while True:
                target_pos1 = self._pos_calculator1.target_pos()

                self._logger.debug('arb loop target_pos1 {}'.format(target_pos1))

                tasks = [self._position_chaser1.execute(target_size=target_pos1)]
                if self._position_chaser2 is not None:
                    target_pos2 = self._pos_calculator2.target_pos(target_pos1)
                    self._logger.debug('target_pos2 {}'.format(target_pos2))
                    tasks.append(self._position_chaser2.execute(target_size=target_pos2))

                await asyncio.gather(*tasks)

                await asyncio.sleep(self._config.trade_loop_sec)
        except BaseException:
            self._logger.error(sys.exc_info())
