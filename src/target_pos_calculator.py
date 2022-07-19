from dataclasses import dataclass


class ISpreadGetter:
    def spread(self) -> float:
        ...


class IPositionGetter:
    def current_position(self) -> float:
        ...

    def unit_leverage_lot(self) -> float:
        ...


@dataclass
class TargetPosCalculatorConfig:
    max_spread: float
    min_rebalance_spread_diff: float
    max_leverage: float


class TargetPosCalculator:
    def __init__(
            self,
            spread_getter: ISpreadGetter,
            position_getter: IPositionGetter,
            config: TargetPosCalculatorConfig):
        self._spread_getter = spread_getter
        self._position_getter = position_getter
        self._config = config

        assert config.max_spread > config.min_rebalance_spread_diff > 0
        assert config.max_leverage > 0

    def target_pos(self) -> float:
        spread = self._spread_getter.spread()
        current_pos = self._position_getter.current_position()
        max_lot_size = self._config.max_leverage * self._position_getter.unit_leverage_lot()

        target_pos = max_lot_size * min(1, spread / self._config.max_spread)
        if abs(target_pos - current_pos) < self._config.min_rebalance_spread_diff:
            target_pos = current_pos

        return target_pos
