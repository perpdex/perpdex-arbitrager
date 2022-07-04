
class IPositionGetter:
    def current_position(self) -> float:
        pass


class ITaker:
    def post_market_order(
            self,
            symbol: str,
            side_int: int,
            size: float) -> str:
        pass


class TargetTakePositionerConfig:
    symbol: str


class TargetTakePositioner:
    def __init__(
            self,
            config: TargetTakePositionerConfig,
            position_getter: IPositionGetter,
            taker: ITaker) -> None:
        self._config = config
        self._position_getter = position_getter
        self._taker = taker

    async def execute(self, target_size: float):
        current_pos = self._position_getter.current_position()

        diff = target_size - current_pos
        if diff == 0:
            return

        side_int = int(diff > 0)
        self._taker.post_market_order(
            symbol=self._config.symbol,
            side_int=side_int,
            side=abs(diff),
        )


# TODO: implement maker ver.


class IMaker:
    def post_limit_order(
            self,
            symbol: str,
            side_int: int,
            size: float,
            price: float) -> str:
        pass

    def cancel_limit_order(self, order_id: str):
        pass


class TargetMakePositioner:
    def __init__(
            self,
            position_getter: IPositionGetter,
            maker: IMaker) -> None:
        self._position_getter = position_getter
        self._maker = maker

        self._current_order_id: str = None

    async def execute(self, target_size: float):
        current_pos = self._position_getter.current_position()

        diff = target_size - current_pos
        if diff == 0:
            return

        side_int = int(diff > 0)
        if self._current_order_id:
            self._maker.cancel_limit_order(order_id=self._current_order_id)

        self._current_order_id = self._maker.post_limit_order(
            side_int=side_int, size=abs(diff), price=None)
