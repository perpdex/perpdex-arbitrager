from dataclasses import dataclass
import numpy as np


class ISpreadGetter:
    def spread(self) -> float:
        ...


class IPositionGetter:
    def current_position(self) -> float:
        ...


@dataclass
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

        assert config.open_threshold > config.close_threshold > 0
        assert config.threshold_step > 0
        assert config.lot_size > 0

    def target_pos(self) -> float:
        spread = self._spread_getter.spread()
        current_pos = self._position_getter.current_position()

        target_pos = current_pos

        # close all pos when close threshold satisfied
        if current_pos < 0 and spread > -self._config.close_threshold:
            target_pos = 0.0
        elif current_pos > 0 and spread < self._config.close_threshold:
            target_pos = 0.0

        # open when abs(spread) > op_thresh
        if abs(spread) > self._config.open_threshold:
            n_lot = np.ceil(
                (
                    abs(spread) - self._config.open_threshold
                ) / self._config.threshold_step
            )
            pos = n_lot * self._config.lot_size * np.sign(spread)

            # stay current_pos if already opened more than pos
            if spread >= 0:
                target_pos = max(pos, target_pos)
            else:
                target_pos = min(pos, target_pos)

        return target_pos
