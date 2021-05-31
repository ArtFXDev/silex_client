import os

import yaml


class Config():
    """
    Utility class that lazy load and resolve the configurations on demand
    """
    def __init__(self, config_root_path=None, default_config=None):
        # Initialize the root of all the config files
        if not config_root_path:
            config_root_path = os.getenv("SILEX_CLIENT_CONFIG")
        self.config_root = config_root_path.replace("/", os.sep).replace(
            "\\", os.sep)
        # Initialize the name of the default config file
        if not default_config:
            default_config = "default"
        self.default_config = default_config

    def resolve_config(self,
                       dcc,
                       action,
                       task,
                       project=None,
                       user=None,
                       **kwargs):
        """
        Create a config by inheritance in the order : action, task 
        By reading the files in the order : default, dcc, project, user
        """

        files = [(self.default_config, ""), (dcc, "dcc"), (project, "project"),
                 (user, "user")]
        layers = [action, task]
        config = {"post": [], "action": [], "pre": []}

        # Loop over all the files
        for file in files:
            # Skip if no name for the file was given
            if not file[0]:
                continue
            config_path = os.path.join(self.config_root, "action", file[1],
                                       f"{file[0]}.yml")

            with open(config_path, "r") as config_file:
                config_yaml = yaml.load(config_file, Loader=yaml.FullLoader)

                # Loop over all the layers
                for layer in layers:
                    # stop if the current layer name wasn't provided or the given layer does not exist
                    if not layer or layer not in config_yaml or not config_yaml[
                            layer]:
                        break

                    config_yaml = config_yaml[layer]

                    # Loop over pre, action, post
                    for key, item in config.items():
                        # Skip if the layer does not provide any commands for this key
                        if key not in config_yaml or not config_yaml[key]:
                            continue

                        # Merge the command set of the layer in to the config's command set
                        self._combine_commands(config[key], config_yaml[key])

        return config

    def _combine_commands(self, commands_a, commands_b):
        """
        Merge the set of commands_b into the set of commands_a by replacing the one that has the same name and appending the new ones
        """
        for command in commands_b:
            # If the command has no name append it without conditions
            if "name" not in command:
                commands_a.append(command.copy())
                continue

            # Find the commands that have the same name
            match = [
                index for index, cmd in enumerate(commands_a)
                if "name" in cmd and cmd["name"] == command["name"]
            ]
            # If a command with the same name already exist
            if len(match) > 0:
                commands_a[match[0]] = command.copy()
            else:
                # Add the command to the config
                commands_a.append(command.copy())
