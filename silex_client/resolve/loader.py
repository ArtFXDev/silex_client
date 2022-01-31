"""
@author: TD gang

Override of the default loader to be able to create custom tags in YAML files,
like !include or !inherit
"""

import os
from pathlib import Path
from typing import IO, Any, Callable, Dict, List, Union

import jsondiff
import yaml

from silex_client.action.connection import ConnectionOut, ConnectionIn
from silex_client.utils.log import logger


class Loader(yaml.SafeLoader):
    """
    Override of the default loader to be able to create custom tags in YAML files,
    like !include or !inherit
    """

    def __init__(self, stream: IO, path: Path, paths: List[Path] = None) -> None:
        if paths is None:
            paths = [Path("/"), Path(os.path.curdir)]

        parent = path.parent
        # Get the current category
        self.current_category = parent.name
        # Get the search paths
        self.search_paths = paths
        # Get only the next search path from the current one
        if parent in paths:
            path_index = paths.index(parent.parent)
            self.search_paths = paths[path_index:]

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
            # Handle single value data
            construct_kwargs[keys[0]] = node_data

        return construct_kwargs

    def _import_file(self, file: str, category: str = None) -> Any:
        """
        Find a file using the search_path and load it
        """
        if category is None:
            category = self.current_category

        # If the path is not relative look one level deeper into the paths
        if file.startswith("."):
            file = file[1:]
        else:
            self.search_paths = self.search_paths[1:]
        # Find the file in the list of search path
        from silex_client.resolve.config import Config

        config = Config([str(path) for path in self.search_paths])
        return config.resolve_action(file, category)

    def inherit(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !inherit statement
        The result will be the merged data between the inherited data and the node's data
        """
        # Handle any type of node
        inherit_kwargs = self._construct_kwargs(node, ("parent", "key", "category"))

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
            logger.error("No parent given for !inherit statement in yaml config")
            return None
        inherit_data = self._import_file(
            inherit_kwargs["parent"], inherit_kwargs.get("category")
        )

        if "key" not in inherit_kwargs:
            inherit_kwargs["key"] = inherit_kwargs["parent"].lstrip(".")

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
                    inherit_kwargs["key"],
                )
                return node_data

        # Merge the two data
        if type(inherit_data) is not type(node_data):
            logger.warning(
                "The node and the inherited node are not the same time, skipping inheritance for yaml config %s",
                inherit_kwargs["parent"],
            )
            return node_data

        return jsondiff.patch(inherit_data, node_data)

    def connect_out(self, node: yaml.Node) -> ConnectionOut:
        """
        Contructor function to handle the !connect-out statement
        The result will be a ConnectionOut object that will tell the ActionQuery object
        to get the result from an other buffer
        """
        return ConnectionOut(node.value)

    def connect_in(self, node: yaml.Node) -> ConnectionIn:
        """
        Same as connect_out but returns a ConnectionIn object
        """
        return ConnectionIn(node.value)


# Set the include method as a handler for the !include statement
Loader.add_constructor("!inherit", Loader.inherit)
Loader.add_constructor("!connect-out", Loader.connect_out)
Loader.add_constructor("!connect-in", Loader.connect_in)
