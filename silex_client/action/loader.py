"""
@author: TD gang

Custom YAML loader to load action config files
"""

import os
from typing import Any, IO, Dict, List, Tuple

import json
import yaml

from silex_client.utils.log import logger


class Loader(yaml.SafeLoader):
    """
    Override of the default loader to be able to create custom constructors
    """
    def __init__(self, stream: IO, path: Tuple[str, ...] = ("/", )) -> None:
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
        mapping = {
            yaml.ScalarNode: self.construct_scalar,
            yaml.SequenceNode: self.construct_sequence,
            yaml.MappingNode: self.construct_mapping
        }
        # Find the corresponding constructor
        for node_type, handler in mapping.items():
            if isinstance(node, node_type):
                # Call the constructor
                try:
                    # If the constructor can be used recursively there is a deep argument
                    return handler(node, deep=True)
                except TypeError:
                    # If not there is no deep argument
                    return handler(node)

        # Error if no handler has been used
        logger.error("Unhandled syntax for given node in yaml config")
        return {}

    def _construct_kwargs(
        self, node: yaml.Node, keys: Tuple[str, ...] = ()) -> Dict[str, Any]:
        """
        Construct data from node, allow to handle multiple types of data
        in a custom statement
        """
        if not keys:
            return {}

        node_data = self._get_node_data(node)

        # Handle the different type of returned data from the node
        construct_kwargs = {}
        if isinstance(node_data, Dict):
            # Handle dictionary data
            construct_kwargs = {
                key: value
                for key, value in node_data.items() if key in keys
            }
        elif isinstance(node_data, List):
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
            logger.error(
                "Could not resolve config, the file %s does not exist", file)
            return None

        # Get the file type to load it correctly
        extension = os.path.splitext(filename)[1].lstrip('.')
        # Load and return the included file
        with open(filename, 'r') as import_data:
            if extension in ('yaml', 'yml'):
                return yaml.load(import_data, Loader)
            elif extension == 'json':
                return json.load(import_data)
            else:
                return ''.join(import_data.readlines())

    @classmethod
    def _merge_dict(cls, data_a: Dict, data_b: Dict) -> Dict:
        """
        Merge the dict A into the dict B by merging their values recursively
        """
        # Check if the types are correct
        if not isinstance(data_a, Dict) or not isinstance(data_b, Dict):
            return data_a

        # Loop over data A and override data B
        for key, value in data_a.items():
            # Append the non existing keys
            if key not in data_b.keys():
                data_b[key] = value
            # Replace the non mergeable corresponding keys
            elif type(value) is not type(data_b[key]):
                data_b[key] = value
            # Merge the mergeable corresponding keys
            else:
                data_b[key] = cls._merge_data(value, data_b[key])
        # Return the overriden data B
        return data_b

    @classmethod
    def _merge_list(cls, data_a: List, data_b: List) -> List:
        """
        Merge the list A into the list B by appending there values and replacing if
        the values matches in a certain way
        """
        # Check if the types are correct
        if not isinstance(data_a, List) or not isinstance(data_b, List):
            return data_a

        for item_a in data_a:
            # Find if some items in data B needs to be replaced
            try:
                match_index = next(index for index, item_b in enumerate(data_b)
                                   if item_b["name"] == item_a["name"])
                data_b[match_index] = item_a
                continue
            except (KeyError, TypeError, StopIteration):
                pass

            # Otherwise just append the item into data B
            data_b.append(item_a)

        return data_b

    @classmethod
    def _merge_data(cls, data_a: Any, data_b: Any) -> Any:
        """
        Merge the data A into the data B by chosing the apropriate merge method
        """
        # Mapp the data types to their merge function
        mapping = {Dict: cls._merge_dict, List: cls._merge_list}
        for data_type, handler in mapping.items():
            if isinstance(data_a, data_type) and isinstance(data_b, data_type):
                # Execute the apropriate merge function
                return handler(data_a, data_b)

        # Just return the data A if no handler has been found
        return data_a

    def include(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !include statement
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
        if include_data is not Dict or "key" not in include_kwargs:
            return include_data

        include_keys = include_kwargs["key"].split(".")
        try:
            for include_key in include_keys:
                include_data = include_data[include_key]
            return include_data
        except (KeyError, TypeError):
            logger.warning(
                "The given key could not be found in the included file %s",
                include_kwargs["file"])
            return include_data

    def inherit(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !inherit statement
        """
        # Handle any type of node
        inherit_kwargs = self._construct_kwargs(node, ("parent", "key"))

        # Get node data
        node_data = self._get_node_data(node)

        # Get the inherited file data
        if "parent" not in inherit_kwargs:
            logger.error("No file given for !inherit statement in yaml config")
            return None
        inherit_data = self._import_file(inherit_kwargs["parent"])

        # If the file is a yaml or json and a key has been specified,
        # return the content of that key in the file
        if isinstance(inherit_data, Dict) and "key" in inherit_kwargs:
            inherit_keys = inherit_kwargs["key"].split(".")
            try:
                for inherit_key in inherit_keys:
                    inherit_data = inherit_data[inherit_key]
            except (KeyError, TypeError):
                logger.warning(
                    "The given key could not be found in the inherited file %s",
                    inherit_kwargs["file"])
                return node_data

        # Merge the two data
        if type(inherit_data) is not type(node_data):
            logger.warning(
                "The node and the inherited node are not the same time, \
                skipping inheritance for yaml config %s",
                inherit_kwargs["parent"])
            return node_data

        return self._merge_data(node_data, inherit_data)


# Set the include method as a handler for the !include statement
Loader.add_constructor('!include', Loader.include)
Loader.add_constructor('!inherit', Loader.inherit)
