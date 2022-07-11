import asyncio
from dataclasses import dataclass


class ITargetPosCalculator:
    def target_pos(self) -> float:
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
            target_pos_calculator: ITargetPosCalculator,
            position_chaser1: IPositionChaser,
            position_chaser2: IPositionChaser,
    ):
        self._config = config
        self._target_pos_calculator = target_pos_calculator
        self._position_chaser1 = position_chaser1
        self._position_chaser2 = position_chaser2

        self._task: asyncio.Task = None
    
    def health_check(self) -> bool:
        return not self._task.done()

    def start(self):
        self._task = asyncio.create_task(self._trade())

    async def _trade(self):
        while True:
            target_pos = self._target_pos_calculator.target_pos()

            await asyncio.gather(
                self._position_chaser1.execute(target_size=target_pos),
                self._position_chaser2.execute(target_size=target_pos * -1)
            )

            await asyncio.sleep(self._config.trade_loop_sec)
