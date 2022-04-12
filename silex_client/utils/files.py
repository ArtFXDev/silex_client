"""
@author: TD gang

Helper that reload a given module and all its submodules recursively
Can be used for development purposes
"""

import errno
import os
import pathlib
import re
import sys
import unicodedata
from types import ModuleType
from typing import List, Dict, Union, Tuple
from silex_client.utils.constants import ENV_VARIABLE_FORMAT

import fileseq

# Sadly, Python fails to provide the following magic number for us.
ERROR_INVALID_NAME = 123

def find_environment_variable(path: pathlib.Path) -> Union[re.Match, None]:
    """
    Find an environment variable in a path, if it exists
    """
    # Format path 
    path_str: str = path.as_posix()
    # Look for the variable 
    for reg in ENV_VARIABLE_FORMAT:
        if re.match(reg, path_str) and re.match(reg, path_str).group(1) in os.environ:
            return re.match(reg, path_str)
    return None
    
def expand_environment_variable(path: pathlib.Path) -> pathlib.Path:
    """
    Replace an environment variable in a path by its value and return it
    """
    if find_environment_variable( path):      
        # Format path 
        path_str: str = path.as_posix()
        
        match:  Union[re.Match, None] = find_environment_variable(path)
        return pathlib.Path(path_str.replace(match.group(0), os.environ[match.group(1)]))

    return path


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

        root_dirname = (
            os.environ.get("HOMEDRIVE", "C:")
            if sys.platform == "win32"
            else os.path.sep
        )
        assert os.path.isdir(root_dirname)  # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, "winerror"):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    except TypeError as exc:
        return False
    else:
        return True


def slugify(value: str, allow_unicode=False) -> str:
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "_", value).strip("-_")


def find_sequence_from_path(file_path: pathlib.Path) -> fileseq.FileSequence:
    """
    Find the sequence corresponding to the given file path
    If no file sequence are found, a file sequene of one item is returned
    """
    default_sequence = fileseq.FileSequence(file_path)

    # Split the input file path using the fileseq's regex
    regex = fileseq.FileSequence.DISK_RE
    match = regex.match(str(file_path))

    if match is None:
        return default_sequence

    # We don't take the index in consideration
    _, basename, _, ext = match.groups()
    for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
        # Find the file sequence that correspond the to file we are looking for
        if basename == file_sequence.basename() and ext == file_sequence.extension():
            return file_sequence

    return default_sequence


def format_sequence_string(
    sequence: fileseq.FileSequence, path_template: str, regexes: List[re.Pattern]
) -> str:
    """
    Format a sequence by replacing the index by the notation in the path_template

    Example:
        path_template: /foo/bar.$F4.exr
        sequence: /publish/publish_name.####.exr

        output -> /publish/publish_name.$F4.exr

    Each regex in the list must contain a single capturing group that will capture the expression
    """
    for regex in regexes:
        match = regex.match(path_template)
        if match is None:
            continue

        # Get the captured index
        (index_expression,) = match.groups()
        dirname = pathlib.Path(str(sequence.dirname()))
        basename = sequence.format("{basename}" + str(index_expression) + "{extension}")
        return (dirname / basename).as_posix()

    # If there is not match just return the first item of the sequence
    return pathlib.Path(str(sequence.index(0))).as_posix()


def expand_template_to_sequence(
    path_template: pathlib.Path, regexes: List[re.Pattern]
) -> fileseq.FileSequence:
    """
    Find the sequence related to the template path given. Used to find sequences of
    path like /foo/bar.<UDIM>.png.

    Each regex in the list must contain a single capturing group that will capture the expression
    """
    if not os.path.exists(path_template.parent):
        return fileseq.FileSequence(path_template)

    file_matches = []
    for regex in regexes:
        match = regex.match(str(path_template))

        if match is None:
            continue

        template_format = re.escape(
            str(path_template).replace(match.group(1), r"__INDEX__")
        )
        regex_format = re.compile(template_format.replace("__INDEX__", r"\d+"))
        for child in path_template.parent.iterdir():
            if regex_format.search(str(child)):
                file_matches.append(child)

        match_sequence = fileseq.findSequencesInList(file_matches)
        if match_sequence:
            return match_sequence[0]

    return fileseq.FileSequence(path_template)


def sequence_exists(sequence: fileseq.FileSequence) -> bool:
    """
    Test if every files in the given sequence exists
    """
    return all(pathlib.Path(str(path)).exists() for path in sequence)
