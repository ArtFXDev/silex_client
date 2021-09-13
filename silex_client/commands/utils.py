from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger


class Log(CommandBase):
    """
    Log the given string
    """

    parameters = {
        "message": {
            "label": "Message",
            "type": str,
            "value": None
        },
        "level": {
            "label": "Level",
            "type": str,
            "value": "info"
        }
    }

    @CommandBase.conform_command()
    def __call__(self, parameters: dict, variables: dict,
                 context_metadata: dict):
        try:
            getattr(logger, parameters["level"])(parameters["message"])
        except ValueError:
            logger.warning("Invalid log level")
