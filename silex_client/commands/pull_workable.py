from __future__ import annotations

import logging
import os
import pathlib
import re
import typing
from typing import Any, Dict
import gazu.files
import fileseq


import asyncio
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.commands.build_work_path import BuildWorkPath
from silex_client.utils import command_builder
from silex_client.core.context import Context
from silex_client.utils.files import expand_path
from silex_client.utils.log import flog
from silex_client.utils.parameter_types import TaskFileParameterMeta, TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


def cast(typ, val):
    return val

ExtensioToDcc = {
    ".hip": "houdini",
    ".hipnc":"houdini",
    ".ma":"maya",
    ".mb":"maya",
    ".nk":"nuke",
    ".blend":"blender"
}
class SelectPull(BuildWorkPath):
    """
    Select the file to pull into the current work directory
    """

    parameters = {
        "publish": {
            "label": "Select a publish",
            "type": TaskFileParameterMeta(),
            "value": None,
            "tooltip": "Select a submiter in the list",
        },
        "prompt": {
            "label": "Prompt if publish exists",
            "type": bool,
            "value": False,
            "hide": True,
        },
        "mode": {
            "label": "File template mode",
            "type": str,
            "value": "output",
            "hide": True,
        },
    }

    required_metadata = ["project_file_tree"]

    @staticmethod
    def skip_next_command(action_query):
        # TODO: Use a skip at the level of the step to do this
        action_query.commands[action_query.current_command_index + 1].skip = True

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        publish: pathlib.Path = parameters["publish"]
        prompt: bool = parameters["prompt"]
        mode: str = parameters["mode"]
        mode_templates = Context.get()["project_file_tree"].get(mode)

        # Get The TaskID ===========================================================================================
        taskId = os.environ["SILEX_TASK_ID"]


        # Build the work path =======================================================================================
        task = await gazu.task.get_task(action_query.context_metadata["task_id"])

        extensionList: list [str] = parameters["publish"].suffixes
        extension = ''.join(map(str,extensionList))


        async def work_and_full_path(version: int) -> tuple[str, str]:
            work_path: str = await gazu.files.build_working_file_path(
                task, software=None, revision=version, sep=os.path.sep
            )
            full_path = f"{work_path}{extension}"
            return work_path, full_path

        # Build the work path
        initial_version = 1
        version = initial_version
        work_path, full_path = await work_and_full_path(initial_version)

        existing_sequences = fileseq.findSequencesOnDisk(os.path.dirname(full_path))

        # Change to the good version ===================================================================================
        matching_sequence = None
        for sequence in existing_sequences:
            # Check if the filename is present in any of the file sequences
            if pathlib.Path(full_path) in [
                pathlib.Path(path) for path in sequence
            ]:
                # Set the version to the latest of that sequence
                last_version = sequence.frameSet()[-1] + 1

                # If the version is greater, use that
                if last_version > version:
                    version = last_version
                    matching_sequence = sequence

        # We also increment when an existing sequence was found
        if parameters["increment"]:
            version += 1

        if version != initial_version:
            # Rebuild the file path again with the new version
            _, full_path = await work_and_full_path(version)


        publishes = [publish]
        if not publish.is_dir():
            publish = publish.parent
        else:
            publishes = list(publish.iterdir())

        # get the associated dcc to extension ==========================================================================

        dcc = ExtensioToDcc[extension]

        # Create command to launch dcc =============================================================================

        project = cast(str, action_query.context_metadata["project"]).lower()
        launch_cmd = command_builder.CommandBuilder(
            f"silex launch {dcc}",
            rez_packages=[f"silex_{dcc}", project],
            delimiter=" ",
            dashes="--",
        )
        launch_cmd.param("task-id")
        launch_cmd.value(taskId)
        launch_cmd.param("file")
        launch_cmd.value(str(parameters["publish"]))
        launch_cmd.param("action")
        launch_cmd.value('rename')

        print(launch_cmd)

        os.system(str(launch_cmd))








        """# This is for publishes, to allow the user to skip the pull or not before publish
        if all(file.exists() for file in publishes) and publishes and prompt:
            response = await self.prompt_user(
                action_query,
                {
                    "pull_info": ParameterBuffer(
                        name="pull_info",
                        label="Pull Info",
                        type=TextParameterMeta(color="info"),
                        value=f"A publish at {publish} already exists",
                    ),
                    "pull_bool": ParameterBuffer(
                        name="pull_info",
                        label="Do you want to backup the current version in your work folder ?",
                        type=bool,
                        value=False,
                    ),
                },
            )
            if not response["pull_bool"]:
                self.skip_next_command(action_query)
                return
        elif prompt:
            self.skip_next_command(action_query)
            return

        if mode_templates is None:
            raise Exception(
                "The given mode does not exists in the current project file tree"
            )

        # Extract informations about the file to pull and build a new path in the work folder
        # from these informations.
        expanded_path = expand_path(publish)
        flog.info(expanded_path["Name"])
        work_folder = pathlib.Path(full_path).parent
        flog.info(work_folder)
        pull_path = (
            work_folder
            / "publish_backup"
            / expanded_path["OutputType"]
            / expanded_path["Name"]
        )
        os.makedirs(pull_path, exist_ok=True)
        versions = [
            child.name
            for child in pull_path.iterdir()
            if re.match(r"^v\d+$", child.name)
        ]
        versions.sort()
        version = "v001"
        if versions:
            version = "v" + str(int(versions[-1].lstrip("v")) + 1).zfill(3)

        flog.info({"pull_dst": pull_path / version, "pull_src": publishes})"""
