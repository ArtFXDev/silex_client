"""
@author: TD gang

Singleton-like class that keeps track of the current context
This class should not be instanciated use the already instanciated object from this module
or use the get() static method
"""

from __future__ import annotations

import copy
import os
import sys
import uuid
from typing import Any, Dict, Optional
from concurrent import futures

from rez import resolved_context
import gazu

from silex_client.action.action_query import ActionQuery
from silex_client.core.event_loop import EventLoop
from silex_client.network.websocket import WebsocketConnection
from silex_client.resolve.config import Config
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.utils.log import logger


class Context:
    """
    Singleton-like class that keeps track of the current context
    This class should not be instanciated use the already instanciated object from this module
    or use the get() static method

    :ivar config: Used to resolve configuration files, using the context's variables
    :ivar is_outdated: When this is true, the properties will recompute themselves when queried
    """

    def __init__(self):
        self.config: Config = Config()
        self._metadata: Dict[str, Any] = {"name": None, "uuid": str(uuid.uuid1())}
        self.is_outdated: bool = True
        self.running_actions: Dict[str, ActionQuery] = {}
        self._rez_context: resolved_context.ResolvedContext = (
            resolved_context.ResolvedContext.get_current()
        )

        self.event_loop: EventLoop = EventLoop()
        self.ws_connection: WebsocketConnection = WebsocketConnection(
            self.event_loop, self.metadata
        )

        self.event_loop.start()
        self.ws_connection.start()

        gazu.set_host("http://localhost/api")
        future_login = self.event_loop.register_task(
            gazu.log_in("admin@example.com", "mysecretpassword")
        )
        futures.wait([future_login])

    @staticmethod
    def get() -> Context:
        """
        Return a globaly instanciated context. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "context")

    @property
    def rez_context(self) -> resolved_context.ResolvedContext:
        """
        Return the associated rez context, gets it if None is associated
        """
        if self._rez_context is None:
            self._rez_context = resolved_context.ResolvedContext.get_current()
            self.is_outdated = True

        return self._rez_context

    @rez_context.setter
    def rez_context(self, rez_context: resolved_context.ResolvedContext):
        self._rez_context = rez_context
        self.is_outdated = True

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Lazy loaded property that updates when the is_outdated attribute is set to True
        """
        # Lazy load the context's metadata
        if self.is_outdated:
            self.is_outdated = False
            self.update_dcc()
            self.update_user()
            self.update_entities()
            self._metadata["pid"] = os.getpid()

        return self._metadata

    @metadata.setter
    def metadata(self, data: Dict[str, Any]) -> None:
        """
        Set the _metadata private attribute.
        This should not be used unless for test purposes, let the metadata update itself instead
        """
        if "PYTEST_CURRENT_TEST" not in os.environ:
            logger.error(
                "Could not set context metadata: Context::metadata.setter is for testing purpose only"
            )
            return
        self._metadata = data

    def update_metadata(self, data: Dict[str, Any]) -> None:
        """
        Merge the provided dict with the current metadata
        This should not be used unless for test purposes, let the metadata update itself instead
        """
        if "PYTEST_CURRENT_TEST" not in os.environ:
            logger.error(
                "Could not update context metadata: Context::update_metadata is for testing purpose only"
            )
            return
        self._metadata.update(data)

    def initialize_metadata(self, data: Dict[str, Any]) -> None:
        """
        Apply the given dict to the metadata, only if the value was not set already
        """
        for key, value in data.items():
            self._metadata.setdefault(key, value)

    def update_dcc(self) -> None:
        """
        Update the metadata's dcc key using rez environment variable
        """
        request = os.getenv("REZ_USED_REQUEST", "")
        # TODO: Get the list of DCCs from a centralised database or config
        handled_dcc = [
            "maya",
            "houdini",
            "nuke",
            "unreal",
            "substance",
            "mari",
            "clarisse",
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

    def update_entities(self) -> None:
        """
        Update the metadata's key like project, shot, task...
        """
        # TODO: Check the each entity  exists on the database
        self._metadata["project"] = str(self.get_ephemeral_version("project")) or None

        self._metadata["asset"] = str(self.get_ephemeral_version("asset")) or None

        # The sequence and the shot needs to be converted from string to integer
        for indexed_entity in ["sequence", "shot"]:
            version = self.get_ephemeral_version(indexed_entity)
            if version:
                try:
                    self._metadata[indexed_entity] = int(str(version))
                except TypeError:
                    logger.error("Skipping context's %s: invalid index", indexed_entity)
                    self._metadata[indexed_entity] = None
            else:
                self._metadata[indexed_entity] = None

        self._metadata["task"] = str(self.get_ephemeral_version("task")) or None

    def update_user(self) -> None:
        """
        Update the metadata's user key using authentification
        """
        # TODO: Get the current user from the database using authentification
        self._metadata["user"] = None

    @property
    def name(self) -> str:
        """Get the name stored in the context's metadata"""
        return self.metadata["dcc"]

    @name.setter
    def name(self, value: str) -> None:
        """Set the name stored in the context's metadata"""
        self._metadata["name"] = value

    @property
    def dcc(self) -> Optional[str]:
        """Read only value of the current dcc"""
        return self.metadata.get("dcc")

    @property
    def project(self) -> Optional[str]:
        """Read only value of the current project"""
        return self.metadata.get("project")

    @property
    def asset(self) -> Optional[str]:
        """Read only value of the current asset"""
        return self.metadata.get("asset")

    @property
    def sequence(self) -> Optional[int]:
        """Read only value of the current sequence"""
        return self.metadata.get("sequence")

    @property
    def shot(self) -> Optional[int]:
        """Read only value of the current shot"""
        return self.metadata.get("shot")

    @property
    def task(self) -> Optional[str]:
        """Read only value of the current task"""
        return self.metadata.get("task")

    @property
    def entity(self) -> Optional[str]:
        """Compute the type of the lowest set entity"""
        if self.asset is not None:
            return "asset"
        if self.shot is not None:
            return "shot"
        if self.sequence is not None:
            return "sequence"

        return None

    @property
    def user(self) -> Optional[str]:
        """Read only value of the current user"""
        return self.metadata.get("user")

    @property
    def is_valid(self) -> bool:
        """
        Check if the silex context is synchronised with the rez context
        """
        for ephemeral in self.rez_context.resolved_ephemerals:
            entity_name = ephemeral.name.lstrip(".")
            if entity_name not in ["task", "asset", "shot", "sequence"]:
                continue

            # The silex context is checking if the queried entity really exists on the database
            # If if doesn't, the entity is set to None
            if getattr(self, entity_name) is None:
                logger.warning(
                    "Invalid silex context: The entity %s is not set", entity_name
                )
                return False

            # If the rez context has changed, the silex context might be desynchronised
            if getattr(self, entity_name) != self.get_ephemeral_version(entity_name):
                logger.warning(
                    "Invalid silex context: The entity %s is not on the right version",
                    entity_name,
                )
                return False

        return True

    def get_ephemeral_version(self, name: str) -> str:
        """
        Get the version number of a rez ephemeral package by its name
        Ephemerals are used mostly to represent entities like task, shot, project...
        """
        if self.rez_context is None:
            return ""

        name = f".{name}"
        try:
            ephemeral = next(
                x for x in self.rez_context.resolved_ephemerals if x.name == name
            )
            versions = ephemeral.range.to_versions()[0]
            return versions[0] if versions else ""
        except StopIteration:
            return ""

    def get_action(self, action_name: str) -> ActionQuery:
        """
        Return an ActionQuery object initialized with this context
        """

        metadata_snapshot = ReadOnlyDict(copy.deepcopy(self.metadata))
        action_query = ActionQuery(
            action_name,
            self.config,
            self.event_loop,
            self.ws_connection,
            metadata_snapshot,
        )

        self.running_actions[action_query.buffer.uuid] = action_query
        return action_query


context = Context()
