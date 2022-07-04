import pytest
from src.target_pos_calculator import (TargetPosCalculator,
                                       TargetPosCalculatorConfig)


@pytest.mark.parametrize(
    ids=[
        # spread == 0
        "no pos, spread == 0 : stay 0",
        "pos 10, spread == 0 : to 0",
        "pos -10, spread == 0 : to 0",

        # spread > 0

        # pos == 0
        "no pos, spread > 0, spread < close_threshold : stay 0",
        "no pos, spread > 0, close_threshold < spread < open_threshold : stay 0",
        "no pos, spread > 0, spread == open_threshold : stay 0",
        "no pos, spread > 0, open_threshold < spread : open to lot_size",
        "no pos, spread > 0, open_threshold << spread : open more",

        # pos > 0
        "pos 10, spread > 0, spread < close_threshold : to 0",
        "pos 10, spread > 0, close_threshold < spread < open_threshold : stay 10",
        "pos 10, spread > 0, spread == open_threshold : stay 10",
        "pos 10, spread > 0, open_threshold < spread : open to lot_size",
        "pos 10, spread > 0, open_threshold << spread : add more",

        "pos 7(abs pos < lot_size), spread > 0, spread < close_threshold : to 0",
        "pos 7(abs pos < lot_size), spread > 0, close_threshold < spread < open_threshold : stay 7",
        "pos 7(abs pos < lot_size), spread > 0, spread == open_threshold : stay 7",
        "pos 7(abs pos < lot_size), spread > 0, open_threshold < spread : open to lot_size",
        "pos 7(abs pos < lot_size), spread > 0, open_threshold << spread : add more",

        # pos < 0
        "pos -10, spread > 0, spread < close_threshold : to 0",
        "pos -10, spread > 0, close_threshold < spread < open_threshold : to 0",
        "pos -10, spread > 0, spread == open_threshold : to 0",
        "pos -10, spread > 0, open_threshold < spread : open lot_size",
        "pos -10, spread > 0, open_threshold << spread : add more",

        "pos -7(abs pos < lot_size), spread > 0, spread < close_threshold : to 0",
        "pos -7(abs pos < lot_size), spread > 0, close_threshold < spread < open_threshold : to 0",
        "pos -7(abs pos < lot_size), spread > 0, spread == open_threshold : to 0",
        "pos -7(abs pos < lot_size), spread > 0, open_threshold < spread : open to lot_size",
        "pos -7(abs pos < lot_size), spread > 0, open_threshold << spread : add more",

        # spread < 0

        # pos == 0
        "no pos, spread < 0, -close_threshold < spread : stay 0",
        "no pos, spread < 0, -open_threshold < spread < -close_threshold : stay 0",
        "no pos, spread < 0, spread == -open_threshold : stay 0",
        "no pos, spread < 0, spread < -open_threshold : open",
        "no pos, spread < 0, spread << -open_threshold : open more",

        # pos > 0
        "pos 10, spread < 0, -close_threshold < spread : to 0",
        "pos 10, spread < 0, -open_threshold < spread < -close_threshold : to 0",
        "pos 10, spread < 0, spread == -open_threshold : to 0",
        "pos 10, spread < 0, spread < -open_threshold : open to -lot_size",
        "pos 10, spread < 0, spread << -open_threshold : open more",

        "pos 7(abs pos < lot_size), spread < 0, -close_threshold < spread : to 0",
        "pos 7(abs pos < lot_size), spread < 0, -open_threshold < spread < -close_threshold : to 0",
        "pos 7(abs pos < lot_size), spread < 0, spread == -open_threshold : to 0",
        "pos 7(abs pos < lot_size), spread < 0, spread < -open_threshold : open to -lot_size",
        "pos 7(abs pos < lot_size), spread < 0, spread << -open_threshold : open more",

        # pos < 0
        "pos -10, spread < 0, -close_threshold < spread : to 0",
        "pos -10, spread < 0, -open_threshold < spread < -close_threshold : stay -10",
        "pos -10, spread < 0, spread == -open_threshold : stay -10",
        "pos -10, spread < 0, spread < -open_threshold : open to -lot_size",
        "pos -10, spread < 0, spread << -open_threshold : open more",

        "pos -7(abs pos < lot_size), spread < 0, -close_threshold < spread : to 0",
        "pos -7(abs pos < lot_size), spread < 0, -open_threshold < spread < -close_threshold : stay -7",
        "pos -7(abs pos < lot_size), spread < 0, spread == -open_threshold : stay -7",
        "pos -7(abs pos < lot_size), spread < 0, spread < -open_threshold : open to -lot_size",
        "pos -7(abs pos < lot_size), spread < 0, spread << -open_threshold : open more",
    ],
    argnames="current_position, spread, open_threshold, close_threshold, threshold_step, lot_size, expected",
    argvalues=[
        # spread == 0
        (0.0, 0.0, 0.5, 0.2, 0.1, 10.0, 0.0),
        (10.0, 0.0, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-10.0, 0.0, 0.5, 0.2, 0.1, 10.0, 0.0),

        # spread > 0 & pos == 0
        (0.0, 0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, 0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, 0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, 0.51, 0.5, 0.2, 0.1, 10.0, 10.0),
        (0.0, 0.71, 0.5, 0.2, 0.1, 10.0, 30.0),

        # spread > 0 & pos > 0
        (10.0, 0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (10.0, 0.3, 0.5, 0.2, 0.1, 10.0, 10.0),
        (10.0, 0.5, 0.5, 0.2, 0.1, 10.0, 10.0),
        (10.0, 0.51, 0.5, 0.2, 0.1, 10.0, 10.0),
        (10.0, 0.71, 0.5, 0.2, 0.1, 10.0, 30.0),
        
        (7.0, 0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (7.0, 0.3, 0.5, 0.2, 0.1, 10.0, 7.0),
        (7.0, 0.5, 0.5, 0.2, 0.1, 10.0, 7.0),
        (7.0, 0.51, 0.5, 0.2, 0.1, 10.0, 10.0),
        (7.0, 0.71, 0.5, 0.2, 0.1, 10.0, 30.0),

        # spread > 0 & pos < 0
        (-10.0, 0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-10.0, 0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-10.0, 0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-10.0, 0.51, 0.5, 0.2, 0.1, 10.0, 10.0),
        (-10.0, 0.71, 0.5, 0.2, 0.1, 10.0, 30.0),
        
        (-7.0, 0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-7.0, 0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-7.0, 0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-7.0, 0.51, 0.5, 0.2, 0.1, 10.0, 10.0),
        (-7.0, 0.71, 0.5, 0.2, 0.1, 10.0, 30.0),

        # spread < 0 & pos == 0
        (0.0, -0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, -0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, -0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (0.0, -0.51, 0.5, 0.2, 0.1, 10.0, -10.0),
        (0.0, -0.71, 0.5, 0.2, 0.1, 10.0, -30.0),

        # spread < 0 & pos > 0
        (10.0, -0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (10.0, -0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (10.0, -0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (10.0, -0.51, 0.5, 0.2, 0.1, 10.0, -10.0),
        (10.0, -0.71, 0.5, 0.2, 0.1, 10.0, -30.0),
        
        (7.0, -0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (7.0, -0.3, 0.5, 0.2, 0.1, 10.0, 0.0),
        (7.0, -0.5, 0.5, 0.2, 0.1, 10.0, 0.0),
        (7.0, -0.51, 0.5, 0.2, 0.1, 10.0, -10.0),
        (7.0, -0.71, 0.5, 0.2, 0.1, 10.0, -30.0),

        # spread < 0 & pos < 0
        (-10.0, -0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-10.0, -0.3, 0.5, 0.2, 0.1, 10.0, -10.0),
        (-10.0, -0.5, 0.5, 0.2, 0.1, 10.0, -10.0),
        (-10.0, -0.51, 0.5, 0.2, 0.1, 10.0, -10.0),
        (-10.0, -0.71, 0.5, 0.2, 0.1, 10.0, -30.0),
        
        (-7.0, -0.1, 0.5, 0.2, 0.1, 10.0, 0.0),
        (-7.0, -0.3, 0.5, 0.2, 0.1, 10.0, -7.0),
        (-7.0, -0.5, 0.5, 0.2, 0.1, 10.0, -7.0),
        (-7.0, -0.51, 0.5, 0.2, 0.1, 10.0, -10.0),
        (-7.0, -0.71, 0.5, 0.2, 0.1, 10.0, -30.0),
    ],
)
def test_target_pos_calculator_target_pos(
        current_position,
        spread,
        open_threshold,
        close_threshold,
        threshold_step,
        lot_size,
        expected,
        mocker):

    # mock dependencies
    mocked_position_getter = mocker.MagicMock()
    mocked_position_getter.current_position.return_value = current_position

    mocked_spread_getter = mocker.MagicMock()
    mocked_spread_getter.spread.return_value = spread

    pos_calculator = TargetPosCalculator(
        spread_getter=mocked_spread_getter,
        position_getter=mocked_position_getter,
        config=TargetPosCalculatorConfig(
            open_threshold=open_threshold,
            close_threshold=close_threshold,
            threshold_step=threshold_step,
            lot_size=lot_size,
        )
    )
    assert pos_calculator.target_pos() == expected
