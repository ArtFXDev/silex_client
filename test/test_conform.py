"""
@author: TD gang

Unit testing functions for the conform actions
"""

import pathlib

import pytest
from pytest_mock import MockFixture

from silex_client.action.action_query import ActionQuery
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.enums import Status

# Run the conform test for each conform types
conform_types = [
    i["name"] for i in Config.get().get_actions("conform") if i["name"] not in ["default", "ass"]
]
file_quantities = [1, 19]




@pytest.mark.parametrize("conform_type", conform_types)
@pytest.mark.parametrize("file_quantity", file_quantities)
def test_execute_conform_action(
    mocker: MockFixture, tmp_path: pathlib.Path, conform_type: str, file_quantity: int
):
    """
    Test the execution of all the commands in the 'conform' action
    """
    action = ActionQuery("conform")
    assert hasattr(action, "buffer")

    mock = mocker.MagicMock()
    mock.__getitem__.side_effect = lambda x: getattr(mock, x)

    output_path = tmp_path / "conform"
    input_path = [
        tmp_path
        / f"unittest_conform{'.' + str(i).zfill(4) if file_quantity > 1 else ''}.{conform_type}"
        for i in range(file_quantity)
    ]
    final_path = [
        tmp_path
        / "unittest_conform"
        / f"conform_unittest_conform{'.' + str(i).zfill(4) if file_quantity > 1 else ''}.{conform_type}"
        for i in range(file_quantity)
    ]

    event_loop = Context.get().event_loop.loop
    mock_future = event_loop.create_future()
    mock_future.set_result(mock)
    output_path_future = event_loop.create_future()
    output_path_future.set_result(output_path)

    # Patch the gazu functions
    mocker.patch(
        "silex_client.commands.build_output_path.gazu.task.get_task",
        return_value=mock_future,
    )
    mocker.patch(
        "silex_client.commands.build_output_path.gazu.files.get_output_type_by_short_name",
        return_value=mock_future,
    )
    mocker.patch(
        "silex_client.commands.build_output_path.gazu.files.build_entity_output_file_path",
        return_value=output_path_future,
    )

    # Set the parameter that are required for the execution
    for path in input_path:
        path.parent.mkdir(exist_ok=True)
        path.touch(exist_ok=True)
    action.set_parameter("setup:get_conform_output:file_paths", input_path)
    future = action.execute(batch=True)

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED
    for path in final_path:
        assert path.exists()
