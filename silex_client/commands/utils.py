from silex_client.action.command_base import CommandBase


class Log(CommandBase):
    """
    Log the given string
    """

    parameters = [{
        "name": "message",
        "label": "Message",
        "type": str,
        "default": None
    }, {
        "name": "level",
        "label": "Level",
        "type": str,
        "default": "info"
    }]

    @CommandBase.conform_command
    def __call__(self, **kwargs):
        pass
