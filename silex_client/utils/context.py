"""
@author: TD gang

Context variables that is meant to be shared across all the modules
Do not instanciate the Context class, use the already instanciated variable context instead
"""

import importlib
import os

from silex_client.utils.config import Config
from silex_client.utils.log import logger


class Context:
    """
    Singleton like class that keeps track of the current context
    """

    _metadata = {}

    def __init__(self):
        self.config = Config()
        self.is_outdated = True

    @property
    def metadata(self):
        """
        Lazy loaded property that updates when the is_outdated attribute is set to True
        """
        # Lazy load the context's metadata
        if self.is_outdated:
            self.is_outdated = False
            self.update_dcc()
            self.update_task()
            self.update_project()
            self.update_user()
            self.update_entity()

        return self._metadata

    @metadata.setter
    def metadata(self, data):
        """
        Set the _metadata private attribute.
        This should not be used unless for test purposes, let the metadata update utself instead
        """
        self._metadata = data

    def update_metadata(self, data):
        """
        Merge the provided dict with the current metadata
        This should not be used unless for test purposes, let the metadata update utself instead
        """
        self._metadata.update(data)

    def update_dcc(self):
        """
        Update the metadata's dcc key using rez environment variable
        """
        request = os.getenv("REZ_USED_REQUEST", "")
        if "maya" in request:
            self._metadata["dcc"] = "maya"
            logger.info("Setting maya as dcc context")
        elif "houdini" in request:
            self._metadata["dcc"] = "houdini"
            logger.info("Setting houdini as dcc context")
        elif "nuke" in request:
            self._metadata["dcc"] = "nuke"
            logger.info("Setting nuke as dcc context")
        elif "blender" in request:
            self._metadata["dcc"] = "blender"
            logger.info("Setting blender as dcc context")
        else:
            logger.critical("No supported dcc detected")
            self.is_outdated = True

    def update_task(self):
        """
        Update the metadata's task key using the filesystem
        """
        # TODO: Get the current task from filesystem
        self._metadata["task"] = "modeling"

    def update_project(self):
        """
        Update the metadata's project key using the filesystem
        """
        # TODO: Get the current project from the filesystem
        self._metadata["project"] = "TEST_PIPE"

    def update_user(self):
        """
        Update the metadata's user key using authentification
        """
        # TODO: Get the current user from the database using authentification
        self._metadata["user"] = "slambin"

    def update_entity(self):
        """
        Update the metadata's entity related keys using the filesystem
        """
        # Clear the current entity
        for entity in ["sequence", "shot", "asset"]:
            if entity in self._metadata:
                self._metadata.pop(entity)
        # Get the current entity
        # TODO: Get the current entity from the filesystem
        self._metadata["entity"] = "shot"
        self._metadata["sequence"] = 50
        self._metadata["shot"] = 120

    def get_action(self, action_name):
        """
        Return a list of modules to execute for an action
        """

        config_metadata = self.metadata
        config_metadata["action"] = action_name
        action = self.config.resolve_config(**config_metadata)

        return action

    def execute_action(self, action_name):
        """
        Create and execute a list of modules according to
        the given action name and the context data
        """
        action = self.get_action(action_name)
        for item in action.values():
            for command in item:
                # Skip in no module path is given
                if "command" not in command:
                    continue
                # Import the given module
                split = command["command"].split(".")
                package = importlib.import_module(
                    f"silex_client.{command['command'].replace('.' + split[-1], '')}"
                )
                module = getattr(package, split[-1])

                # If some parameters where given pass them when calling the module
                if "parm" in command:
                    module(**(command["parm"]))
                else:
                    module()


context = Context()
