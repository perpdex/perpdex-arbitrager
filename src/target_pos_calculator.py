import numpy as np


class ISpreadGetter:
    def spread(self) -> float:
        pass


class IPositionGetter:
    def current_position(self) -> float:
        pass


class TargetPosCalculatorConfig:
    open_threshold: float
    close_threshold: float
    threshold_step: float
    lot_size: float


class TargetPosCalculator:
    def __init__(
            self,
            spread_getter: ISpreadGetter,
            position_getter: IPositionGetter,
            config: TargetPosCalculatorConfig):
        self._spread_getter = spread_getter
        self._position_getter = position_getter
        self._config = config

    def target_pos(self):
        spread = self._spread_getter.spread()
        current_pos = self._position_getter.current_position()

        # pos_open
        n_lot = np.ceil(
            (
                abs(spread) - self._config.open_threshold
            ) / self._config.threshold_step
        )
        n_lot = max(0, n_lot)

        target_pos_op = max(
            n_lot * self._config.lot_size,
            abs(current_pos)
        ) * np.sign(spread)

        # pos_close
        target_pos_cl = 0 if abs(spread) < self._config.close_threshold else current_pos

        # target_pos = current_post + diff_op + diff_cl
        # diff_op = target_pos_op - current_pos
        # diff_cl = target_pos_cl - current_pos
        return target_pos_op + target_pos_cl - current_pos
