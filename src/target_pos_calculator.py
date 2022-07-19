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

        # close all pos when close threshold satisfied
        target_pos = 0.0
        if current_pos < 0 and spread > -self._config.close_threshold:
            target_pos = 0.0
        elif current_pos > 0 and spread < self._config.close_threshold:
            target_pos = 0.0
        else:
            target_pos = current_pos
        
        # open when abs(spread) > op_thresh
        if abs(spread) > self._config.open_threshold:
            n_lot = np.ceil(
                (
                    abs(spread) - self._config.open_threshold
                ) / self._config.threshold_step
            )
            pos = n_lot * self._config.lot_size * np.sign(spread)

            if spread >= 0:
                target_pos = max(pos, target_pos)
            else:
                target_pos = min(pos, target_pos)

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
