"""
@author: TD gang

Helper that reload a given module and all its submodules recursively
Can be used for development purposes
"""

import importlib
import os
import pathlib
import re
import sys
import errno

from types import ModuleType

# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123


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

def is_valid_pipeline_path(file_path: pathlib.Path, path_type: str = "publish") -> bool:
    """
    Test if the given path is a valid path in the pipeline or not
    """
    if re.search(r"^P:\\.+\\" + path_type + r"\\", str(file_path)) is not None:
        return True
    return False

def is_valid_path(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    """
    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        _, pathname = os.path.splitdrive(pathname)

        root_dirname = os.environ.get('HOMEDRIVE', 'C:') \
            if sys.platform == 'win32' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError as exc:
        return False
    else:
        return True
