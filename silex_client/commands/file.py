import os

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.utils.context import Context


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
        }
    }

    @CommandBase.conform_command
    def __call__(self, parameters: dict, variables: dict, environment: dict) -> None:
        context_data = Context.get().metadata

        if context_data.get("project") is None:
            logger.error("Could not publish %s, the current context has not project", parameters["name"])
            return
        publish_path = os.path.join(context_data["project"], parameters["name"])

        logger.info("Publishing file(s) %s to %s", parameters["file_path"], "path")
