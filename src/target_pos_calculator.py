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

        unit_lot = self._position_getter.unit_leverage_lot()
        max_lot_size = self._config.max_leverage * unit_lot
        min_rebalance_pos_diff = unit_lot * self._config.min_rebalance_spread_diff / self._config.max_spread

        target_pos = max_lot_size * min(1, spread / self._config.max_spread)
        if abs(target_pos - current_pos) < min_rebalance_pos_diff:
            target_pos = current_pos

        return target_pos


class IPriceGetter:
    def last_price(self) -> float:
        ...


class IdentitySecondaryPosCalculator:
    def target_pos2(self, target_pos1: float or int) -> float or int:
        return target_pos1 * -1


class QuoteToBaseSecondaryPosCalculator:
    def __init__(self, price_getter: IPriceGetter, position_type: callable = float):
        self._price_getter = price_getter
        self._position_type = position_type

    def target_pos2(self, target_pos1_quote: float) -> float or int:
        pos = target_pos1_quote / self._price_getter.last_price()
        return self._position_type(pos) * -1


class BaseToQuoteSecondaryPosCalculator:
    def __init__(self, price_getter: IPriceGetter, position_type: callable = int):
        self._price_getter = price_getter
        self._position_type = position_type

    def target_pos2(self, target_pos1_base: float) -> float or int:
        pos = self._price_getter.last_price() * target_pos1_base
        return self._position_type(pos) * -1
