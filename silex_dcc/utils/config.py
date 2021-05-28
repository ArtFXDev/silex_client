import os

import yaml


class Config(dict):
    """
    Utility class that lazy load the configuration files on demand
    """
    def __init__(self, config_root_path=None):
        if not config_root_path:
            config_root_path = os.getenv("SILEX_DCC_CONFIG")
        self.config_root = config_root_path.replace(os.sep, '/')

    def resolve_config(self,
                       file,
                       action,
                       task,
                       project=None,
                       user=None,
                       **kwargs):

        layers = [action, task]
        config = {"post": [], "action": [], "pre": []}

        config_path = f"{self.config_root}/{file}.yml"
        # Loop over all the layers
        with open(config_path, "r") as config_file:
            config_yaml = yaml.load(config_file, Loader=yaml.FullLoader)

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

                    commands = config_yaml[key]
                    # Loop over all the command in this section
                    for command in commands:
                        # If the command has no name append it without conditions
                        if "name" not in command:
                            config[key].append(command.copy())
                            continue

                        # If a command with the same name already exist
                        match = [
                            index for index, cmd in enumerate(config[key])
                            if "name" in cmd and cmd["name"] == command["name"]
                        ]
                        if len(match) > 0:
                            config[key][match[0]] = command.copy()
                        else:
                            # Add the command to the config
                            config[key].append(command.copy())

        return config
