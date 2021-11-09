from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import gazu.project
import gazu.task
import gazu.files
import os


class FileStructure(CommandBase):
    """
    Copy file and override if necessary
    """

    

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        projects = await gazu.project.all_open_projects()

        for project in projects:

            tasks = await gazu.task.all_tasks_for_project(project)

            if not tasks:
                return

            for task in tasks:

                working_path = await gazu.files.build_working_file_path(
                    task = task
                )

                working_path_work = os.path.dirname(working_path)
                working_path_work = working_path_work.replace('/', f'{os.path.sep}')
                decompo = working_path_work.split(os.path.sep)

                os.makedirs(working_path_work,exist_ok=True)

                if decompo[3] == "shots":
                    try:
                        sequ_path = f'{os.path.join(*decompo[:3])}{os.path.sep}sequences{os.path.sep}{decompo[4]}{os.path.sep}{decompo[6]}{os.path.sep}work'
                        os.makedirs(sequ_path,exist_ok=True)
                    except:
                        logger.info('Could not create the sequence folder')

                rushes = f'{os.path.join(*decompo[:3])}{os.path.sep}rushes'
                os.makedirs(rushes,exist_ok=True)