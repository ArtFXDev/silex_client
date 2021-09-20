from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger


class CheckDbFileSystemSync(CommandBase):
    """
    Check if the file system and the database are sync
    """

    parameters = {
        "db_entity": {
            "name": "db_entity",
            "label": "Database entity",
            "type": dict,
            "value": None
        },
        "file_path": {
            "name": "file_path",
            "label": "File path",
            "type": str,
            "value": None
        }
    }

    @CommandBase.conform_command()
    def __call__(self, parameters: dict, variables: dict,
                 context_metadata: dict):
        logger.info("Checking if file %s and entity %s both exists",
                    parameters["file_path"], parameters["db_entity"])
