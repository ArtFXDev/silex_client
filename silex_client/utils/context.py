from __future__ import annotations
import os
import sys

from rez import resolved_context

from silex_client.action.action_query import ActionQuery
from silex_client.utils.config import Config
from silex_client.network.websocket import WebsocketConnection
from silex_client.utils.log import logger


class Context:
    """
    Data class that keeps track of the current context
    This class should not be instanciated use the already instanciated object from this module
    or use the get() static method

    :ivar config: Used to resolve configuration files, using the context's variables
    :ivar is_outdated: When this is true, the properties will recompute themselves when queried
    """

    _metadata = {}

    def __init__(self, ws_url: str = "ws://localhost:8080"):
        self.config = Config()
        self._metadata = {}
        self.is_outdated = True
        self._rez_context = resolved_context.ResolvedContext.get_current()

        url = WebsocketConnection.parameters_to_url(ws_url, self.metadata)
        self.ws_connection = WebsocketConnection(url)

    @staticmethod
    def get() -> Context:
        """
        Return a globaly instanciated context. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "context")

    @property
    def rez_context(self):
        if self._rez_context is None:
            self._rez_context = resolved_context.ResolvedContext.get_current()
            self.is_outdated = True

        return self._rez_context
    
    @rez_context.setter
    def rez_context(self, rez_context: resolved_context.ResolvedContext):
        self._rez_context = rez_context
        self.is_outdated = True


    @property
    def metadata(self) -> dict:
        """
        Lazy loaded property that updates when the is_outdated attribute is set to True
        """
        # Lazy load the context's metadata
        if self.is_outdated:
            self.is_outdated = False
            self.update_dcc()
            self.update_user()
            self.update_entities()

        return self._metadata

    @metadata.setter
    def metadata(self, data: dict) -> None:
        """
        Set the _metadata private attribute.
        This should not be used unless for test purposes, let the metadata update utself instead
        """
        self._metadata = data

    def update_metadata(self, data: dict) -> None:
        """
        Merge the provided dict with the current metadata
        This should not be used unless for test purposes, let the metadata update utself instead
        """
        self._metadata.update(data)

    def update_dcc(self) -> None:
        """
        Update the metadata's dcc key using rez environment variable
        """
        request = os.getenv("REZ_USED_REQUEST", "")
        # TODO: Get the list of DCCs from a centralised database or config
        handled_dcc = [
            "maya", "houdini", "nuke", "unreal", "substance", "mari",
            "clarisse"
        ]
        # Look for dcc in rez request
        self._metadata["dcc"] = None
        for dcc in handled_dcc:
            if dcc in request:
                self._metadata["dcc"] = dcc
                logger.info("Setting %s as dcc context", dcc)
                break
        # Handle the case where no DCC has been found
        if self._metadata["dcc"] is None:
            logger.debug("No supported dcc detected")
            self.is_outdated = True

    def update_entities(self) -> None:
        """
        Update the metadata's key like project, shot, task...
        """
        # TODO: Check the each entity  exists on the database
        self._metadata["project"] = str(self.get_ephemeral_version("project")) or None
        self._metadata["asset"] = str(self.get_ephemeral_version("asset")) or None
        sequence = self.get_ephemeral_version("sequence")
        if sequence and str(sequence).isdigit():
            self._metadata["sequence"] = int(sequence)
        elif sequence:
            logger.error("Skipping context's sequence: invalid index")
            self._metadata["sequence"] = None
        else:
            self._metadata["sequence"] = None
        shot = self.get_ephemeral_version("shot")
        if shot and str(shot).isdigit():
            self._metadata["shot"] = int(shot)
        elif shot:
            logger.error("Skipping context's shot: invalid index")
            self._metadata["shot"] = None
        else:
            self._metadata["shot"] = None
        self._metadata["task"] = str(self.get_ephemeral_version("task")) or None

    def update_user(self) -> None:
        """
        Update the metadata's user key using authentification
        """
        # TODO: Get the current user from the database using authentification
        self._metadata["user"] = "slambin"

    @property
    def project(self):
        return self.metadata["project"]

    @property
    def asset(self):
        return self.metadata["asset"]

    @property
    def sequence(self):
        return self.metadata["sequence"]

    @property
    def shot(self):
        return self.metadata["shot"]

    @property
    def task(self):
        return self.metadata["task"]

    @property
    def entity(self):
        if self.asset is not None:
            return "asset"
        elif self.shot is not None:
            return "shot"
        elif self.sequence is not None:
            return "sequence"
        else:
            return None

    def get_ephemeral_version(self, name: str) -> str:
        """
        Get the version number of a rez ephemeral package by its name
        Ephemerals are used mostly to represent entities like task, shot, project...
        """
        if self.rez_context is None:
            return ""

        name = f".{name}"
        try:
            ephemeral = next(x for x in self.rez_context.resolved_ephemerals if x.name == name)
            versions = ephemeral.range.to_versions()[0]
            return versions[0] if versions else ""
        except StopIteration:
            return ""

    def get_action(self, action_name: str) -> ActionQuery:
        """
        Return an ActionQuery object initialized with this context
        """

        return ActionQuery(action_name, self.ws_connection, self.config,
                           self.metadata)


context = Context()
