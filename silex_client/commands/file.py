from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger


class PublishFile(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "file_path": {
            "name": "file_path",
            "label": "File path",
            "type": str,
            "value": None
        },
        "description": {
            "name": "description",
            "label": "Description",
            "type": str,
            "value": "No description"
        },
        "name": {
            "name": "name",
            "label": "Name",
            "type": str,
            "value": "untitled"
        },
        "task": {
            "name": "task",
            "label": "Task",
            "type": int,
            "value": None
        }
    }

    @CommandBase.conform_command
    def __call__(self, parameters: dict, variables: dict, environment: dict):
        logger.info("Publishing file(s) %s", parameters["file_path"])
