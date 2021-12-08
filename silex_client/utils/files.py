"""
@author: TD gang

Helper that reload a given module and all its submodules recursively
Can be used for development purposes
"""

import importlib
import os
import pathlib
import re
from types import ModuleType


def reload_recursive(parent_module: ModuleType) -> None:
    """
    Reload a given module and all its submodules recursively
    Can be used for development purposes

    Stolen from:
    https://stackoverflow.com/questions/28101895/reloading-packages-and-their-submodules-recursively-in-python
    """
    fn_dir = os.path.dirname(parent_module.__file__) + os.sep
    module_visit = {parent_module.__file__}

    def _reload_childs(module: ModuleType):
        importlib.reload(module)

        for module_child in vars(module).values():
            if isinstance(module_child, ModuleType):
                fn_child = getattr(module_child, "__file__", None)
                if (fn_child is not None) and fn_child.startswith(fn_dir):
                    if fn_child not in module_visit:
                        module_visit.add(fn_child)
                        _reload_childs(module_child)

    _reload_childs(parent_module)

def is_valid_pipeline_path(file_path: pathlib.Path) -> bool:
    """
    Test if the given path is a valid path in the pipeline or not
    """
    if re.search(r"^P:\\.+\\publish\\", str(file_path)) is not None:
        return True
    return False
