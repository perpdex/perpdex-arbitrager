import asyncio


class ITargetPosCalculator:
    def target_pos(self) -> float:
        pass


class IPositioner:
    async def execute(self, target_size: float):
        pass


class ArbitragerConfig:
    trade_loop_sec: int


class Arbitrager:
    def __init__(
            self,
            config: ArbitragerConfig,
            target_pos_calculator: ITargetPosCalculator,
            positioner1: IPositioner,
            positioner2: IPositioner,
    ):
        self._config = config
        self._target_pos_calculator = target_pos_calculator
        self._positioner1 = positioner1
        self._positioner2 = positioner2

        self._task: asyncio.Task = None
    
    def health_check(self) -> bool:
        return not self._task.done()

    def start(self):
        self._task = asyncio.create_task(self._trade())

    async def _trade(self):
        while True:
            target_pos = self._target_pos_calculator.target_pos()

            await asyncio.gather(
                self._positioner1.execute(target_size=target_pos),
                self._positioner2.execute(target_size=target_pos * -1)
            )

            await asyncio.sleep(self._config.trade_loop_sec)
