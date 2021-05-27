import os

import yaml


class Config(dict):
    """
    Utility class that lazy load the configuration files on demand
    """
    def __init__(self):
        config_root_path = os.getenv("SILEX_DCC_CONFIG")
        self.config_root = config_root_path.replace(os.sep, '/')

    def resolve_config(self,
                       dcc,
                       action,
                       task,
                       project=None,
                       user=None,
                       **kwargs):

        layers = [action, task, project, user]
        config = {"post": [], "action": [], "pre": []}

        config_path = f"{self.config_root}/{dcc}.yml"
        # Loop over all the layers
        with open(config_path, "r") as config_file:
            config_yaml = yaml.load(config_file, Loader=yaml.FullLoader)

            # If no name is given for this layer just skip it
            for layer in layers:
                if not layer:
                    continue

                config_yaml = config_yaml[layer]

                # Loop over pre, action, post
                for key, item in config.items():
                    commands = config_yaml[key]
                    if not commands:
                        continue
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

        print(config)
