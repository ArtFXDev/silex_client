from silex_client.action.command_base import CommandBase


class CheckDbFileSystemSync(CommandBase):
    """
    Check if the file system and the database are sync
    """

    parameters = [{
        "name": "db_entity",
        "label": "Database entity",
        "type": dict,
        "default": None
    }, {
        "name": "file_path",
        "label": "File path",
        "type": str,
        "default": None
    }]

    @CommandBase.conform_command
    def __call__(self, **kwargs):
        pass
