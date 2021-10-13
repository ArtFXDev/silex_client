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
from typing import Any, Dict, KeysView, ValuesView, ItemsView
from concurrent import futures

import gazu
import gazu.client
import gazu.shot
import gazu.task
import gazu.files

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

        self.event_loop: EventLoop = EventLoop()
        self.event_loop.start()

        gazu.set_host("http://172.16.2.52:8080/api")
        # TODO: Get the auth token from the silex-server, this is temporary
        future_login = self.event_loop.register_task(
            gazu.log_in("admin@example.com", "mysecretpassword")
        )
        futures.wait([future_login])

        self.ws_connection: WebsocketConnection = WebsocketConnection(
            self.event_loop, self.metadata
        )
        self.ws_connection.start()

    @staticmethod
    def get() -> Context:
        """
        Return a globaly instanciated context. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "context")

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in ["user", "name"]:
            logger.error(
                "Could not set the context metadata %s: This value is read only", key
            )
            return

        self._metadata[key] = value

    def __getitem__(self, key) -> Any:
        return self.metadata.get(key)

    def __contains__(self, item: str) -> bool:
        return item in self.metadata

    def keys(self) -> KeysView[str]:
        return self.metadata.keys()

    def values(self) -> ValuesView[Any]:
        return self.metadata.values()

    def items(self) -> ItemsView[str, Any]:
        return self.metadata.items()

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Lazy loaded property that updates when the is_outdated attribute is set to True
        """
        # Lazy load the context's metadata
        if self.is_outdated:
            ping_future = self.event_loop.register_task(gazu.client.host_is_valid())
            if ping_future.result():
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
        software_future = self.event_loop.register_task(gazu.files.all_softwares())
        handled_dcc = [software["name"] for software in software_future.result()]
        request = os.getenv("REZ_USED_REQUEST", "")

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
        if "SILEX_TASK_ID" in os.environ:
            context_future = self.event_loop.register_task(
                self.resolve_context(os.environ["SILEX_TASK_ID"])
            )
            resolved_context = context_future.result()
            self._metadata.update(resolved_context)

    def update_user(self) -> None:
        """
        Update the metadata's user key using authentification
        """
        user_future = self.event_loop.register_task(gazu.client.get_current_user())
        user = user_future.result()
        self._metadata["user"] = user.get("full_name")
        self._metadata["user_email"] = user.get("email")

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

    @staticmethod
    async def resolve_context(task_id: str) -> Dict[str, str]:
        """
        Guess all the context from the task id, by making requests on the zou api
        """
        resolved_context: Dict[str, str] = {}
        try:
            task = await gazu.task.get_task(task_id)
        except ValueError:
            logger.error("Could not resolve the context: The task ID is invalid")
            return resolved_context

        resolved_context["task"] = task["name"]
        resolved_context["task_id"] = task["id"]
        resolved_context["task_type"] = task["task_type"]["name"]
        resolved_context["project"] = task["project"]["name"]
        resolved_context["project_id"] = task["project"]["id"]

        resolved_context["silex_entity_type"] = task["entity_type"]["name"].lower()

        if task["entity_type"]["name"].lower() == "shot":
            resolved_context["shot"] = task["entity"]["name"]
            resolved_context["shot_id"] = task["entity"]["id"]

            sequence = await gazu.shot.get_sequence(task["entity"]["parent_id"])
            resolved_context["sequence"] = sequence["name"]
            resolved_context["sequence_id"] = sequence["id"]

        else:
            resolved_context["asset"] = task["entity"]["name"]
            resolved_context["asset_id"] = task["entity"]["id"]

        return resolved_context


context = Context()
