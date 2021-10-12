"""
@author: TD gang

Override of the default loader to be able to create custom tags in YAML files,
like !include or !inherit
"""

import json
import os
from typing import Dict, IO, Any, Union, Callable

import yaml

from silex_client.resolve.merge import merge_data
from silex_client.utils.log import logger


class Loader(yaml.SafeLoader):
    """
    Override of the default loader to be able to create custom tags in YAML files,
    like !include or !inherit
    """

    def __init__(self, stream: IO, path: Union[tuple, list] = ("/",)) -> None:
        # Get the list of the path to look for any included file from context
        self.search_path = list(path)

        try:
            # Add the path of the file in the search path
            self.search_path.insert(0, os.path.split(stream.name)[0])
        except AttributeError:
            # Add the current working directory if there is not file path
            self.search_path.insert(0, os.path.curdir)

        super().__init__(stream)

    def _get_node_data(self, node: yaml.Node) -> Any:
        """
        Construct data from node, call the apropriate constructor for the given node
        """
        # Mapp the node types to their contructors
        mapping: Dict[type, Callable[[Any], Any]] = {
            yaml.ScalarNode: self.construct_scalar,
            yaml.SequenceNode: self.construct_sequence,
            yaml.MappingNode: self.construct_mapping,
        }
        # Find the corresponding constructor
        for node_type, handler in mapping.items():
            if isinstance(node, node_type):
                # Call the constructor
                try:
                    # If the constructor can be used recursively there is a deep argument
                    return handler(node, deep=True)  # type: ignore
                except TypeError:
                    # If not there is no deep argument
                    return handler(node)

        # Error if no handler has been used
        logger.error("Unhandled syntax for given node in yaml config")
        return {}

    def _construct_kwargs(self, node: yaml.Node, keys: Union[tuple, list] = ()) -> dict:
        """
        Construct data from node, allow to handle multiple types of data
        in a custom statement
        """
        if not keys:
            return {}

        node_data = self._get_node_data(node)

        # Handle the different type of returned data from the node
        construct_kwargs = {}
        if isinstance(node_data, dict):
            # Handle dictionary data
            construct_kwargs = {
                key: value for key, value in node_data.items() if key in keys
            }
        elif isinstance(node_data, list):
            # Handle list data
            for index, value in enumerate(node_data):
                try:
                    construct_kwargs[keys[index]] = value
                except IndexError:
                    break
        else:
            construct_kwargs[keys[0]] = node_data

        return construct_kwargs

    def _import_file(self, file: str) -> Any:
        """
        Find a file using the search_path and load it
        """
        # Find the file in the list of search path
        filename = ""
        for path in self.search_path:
            resolved_path = os.path.abspath(os.path.join(str(path), file))
            if os.path.isfile(resolved_path):
                filename = resolved_path
                logger.debug("Found imported config at %s", filename)
                break

        if not filename:
            logger.error("Could not resolve config, the file %s does not exist", file)
            return None

        # Get the file type to load it correctly
        extension = os.path.splitext(filename)[1].lstrip(".")
        # Load and return the included file
        with open(filename, "r", encoding="utf-8") as import_data:
            if extension in ("yaml", "yml"):
                return yaml.load(import_data, Loader)
            if extension == "json":
                return json.load(import_data)

            return "".join(import_data.readlines())

    def include(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !include statement
        The result will be the included data only, the node's data is replaced
        """
        # Handle any type of node
        include_kwargs = self._construct_kwargs(node, ("file", "key"))

        # Find the file in the list of search path
        if "file" not in include_kwargs:
            logger.error("No file given for !include statement in yaml config")
            return None

        include_data = self._import_file(include_kwargs["file"])

        # If the file is a yaml or json and a key has been specified,
        # return the content of that key in the file
        if include_data is not dict or "key" not in include_kwargs:
            return include_data

        include_keys = include_kwargs["key"].split(".")
        try:
            for include_key in include_keys:
                include_data = include_data[include_key]
            return include_data
        except (KeyError, TypeError):
            logger.warning(
                "The given key could not be found in the included file %s",
                include_kwargs["file"],
            )
            return include_data

    def inherit(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !inherit statement
        The result will be the merged data between the inherited data and the node's data
        """
        # Handle any type of node
        inherit_kwargs = self._construct_kwargs(node, ("parent", "key"))

        # Get node data
        node_data = self._get_node_data(node)
        # Remove the kwargs from the data
        for key in inherit_kwargs.keys():
            if isinstance(node_data, dict):
                del node_data[key]
            elif isinstance(node_data, list):
                del node_data[0]

        # Get the inherited file data
        if "parent" not in inherit_kwargs:
            logger.error("No file given for !inherit statement in yaml config")
            return None
        inherit_data = self._import_file(inherit_kwargs["parent"])

        # If the file is a yaml or json and a key has been specified,
        # return the content of that key in the file
        if isinstance(inherit_data, dict) and "key" in inherit_kwargs:
            inherit_keys = inherit_kwargs["key"].split(".")
            try:
                for inherit_key in inherit_keys:
                    inherit_data = inherit_data[inherit_key]
            except (KeyError, TypeError):
                logger.warning(
                    "The given key could not be found in the inherited file %s",
                    inherit_kwargs["file"],
                )
                return node_data

        # Merge the two data
        if type(inherit_data) is not type(node_data):
            logger.warning(
                "The node and the inherited node are not the same time, skipping inheritance for yaml config %s",
                inherit_kwargs["parent"],
            )
            return node_data

        return merge_data(node_data, inherit_data)


# Set the include method as a handler for the !include statement
Loader.add_constructor("!include", Loader.include)
Loader.add_constructor("!inherit", Loader.inherit)
