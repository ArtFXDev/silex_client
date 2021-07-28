from silex_client.action.command_base import CommandBase


class PromptFile(CommandBase):
    """
    Ask for a file to the user and store it in the action buffer
    """

    parameters = [{
        "name": "file_path",
        "label": "File path",
        "type": str,
        "default": None
    }]

    @CommandBase.conform_command
    def __call__(self, **kwargs):
        pass


class PublishFile(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = [{
        "name": "file_path",
        "label": "File path",
        "type": str,
        "default": None
    }, {
        "name": "description",
        "label": "Description",
        "type": str,
        "default": "No description"
    }, {
        "name": "name",
        "label": "Name",
        "type": str,
        "default": "untitled"
    }, {
        "name": "task",
        "label": "Task",
        "type": int,
        "default": None
    }]

    @CommandBase.conform_command
    def __call__(self, **kwargs):
        pass
