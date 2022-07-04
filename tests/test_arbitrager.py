import asyncio

import pytest
from src.arbitrager import Arbitrager, ArbitragerConfig


@pytest.mark.asyncio
async def test_arbitrager(mocker):
    target_pos = 10

    mocked_target_pos_calculator = mocker.MagicMock()
    mocked_target_pos_calculator.target_pos.return_value = target_pos

    mocked_chaser1 = mocker.MagicMock()
    mocked_chaser1.execute.return_value = asyncio.Future()

    mocked_chaser2 = mocker.MagicMock()
    mocked_chaser2.execute.return_value = asyncio.Future()

    arb = Arbitrager(
        target_pos_calculator=mocked_target_pos_calculator,
        position_chaser1=mocked_chaser1,
        position_chaser2=mocked_chaser2,
        config=ArbitragerConfig(trade_loop_sec=1),
    )

    # assert health check ok
    arb.start()
    assert arb.health_check() is True

    # force revert the running task
    arb._task.cancel()
    try:
        await arb._task
    except asyncio.CancelledError:
        pass

    # assert health check ng
    assert arb.health_check() is False
