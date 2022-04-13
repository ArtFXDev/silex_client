from __future__ import annotations

from typing import TYPE_CHECKING, IO, Any, List, Union

from pathlib import Path

import copy
import jsondiff
import yaml

if TYPE_CHECKING:
    from silex_client.resolve.yaml_resolver import YAMLResolver


class YAMLLoader(yaml.SafeLoader):
    """
    Override of the default loader to be able to create custom tags in YAML files,
    like !include or !inherit
    """

    INHERIT_KEY_SEPARATOR = ":"

    def __init__(
        self,
        stream: IO,
        path: Path,
        resolver: YAMLResolver,
        traceback: List[Path] = None,
    ) -> None:
        self.resolver = resolver
        self.config_name = resolver.get_namespace(path)
        self.traceback = traceback or []
        super().__init__(stream)

    def _construct_kwargs(self, node: yaml.Node, keys: Union[tuple, list] = ()) -> dict:
        """
        Construct data from node, allow to handle multiple types of data
        in a custom statement
        """
        if not keys:
            return {}

        node_data = self.construct_mapping(node, deep=True)

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

    def _import_config(self, name: str) -> Any:
        """
        Find a file using the search_path of the resolver and load it
        """
        config_resolver = copy.deepcopy(self.resolver)

        if name == self.config_name:
            config_resolver.search_paths = self.resolver.search_paths[1:]

        return config_resolver.resolve_config(name, traceback=self.traceback)

    def inherit(self, node: yaml.Node) -> Any:
        """
        Contructor function to handle the !inherit statement
        The result will be the merged data between the inherited data and the node's data
        """

        node_data = self.construct_mapping(node, deep=True)

        parents = node_data.get("parents")
        if not isinstance(parents, list):
            raise Exception(
                "No or invalid parents given to !inherit statement in yaml config"
            )

        inherit_datas = []
        for parent in node_data["parents"][::-1]:
            key = self.resolver.split_namespace(parent)[1]
            import_config = self._import_config(parent)
            if key not in import_config:
                raise Exception(f"{key} is missing in the config of {parent}")
            inherit_datas.append(import_config[key])

        data = {}
        for inherit_data in inherit_datas:
            # We can only merge datasets that have the same types
            if not isinstance(inherit_data, type(data)):
                raise Exception("The node and the inherited node are not the same type")

            data = jsondiff.patch(inherit_data, data)

        # The overrides key can be used to apply overrides to the inherited yamls
        if "overrides" in node_data:
            data = jsondiff.patch(node_data["overrides"], data)
        return data


# Set the inherit method as a handler for the !inherit statement
YAMLLoader.add_constructor("!inherit", YAMLLoader.inherit)
