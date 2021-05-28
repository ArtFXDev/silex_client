"""
Maya file commands
"""

import os

import maya.cmds as cmds


def get_path():
    """
    Get the current filepath of the scene
    :return str: the current filepath
    """
    return cmds.file(query=True, sceneName=True)


def open(path):
    """
    Open file
    :param str path: The path to the file to open
    """
    path = path.replace(os.sep, "/")
    cmds.file(path, open=True, force=True)


def save():
    """
    Save the current scene.
    """
    try:
        cmds.file(save=True)
    except Exception as ex:
        print("ERROR: Failed to save the current scene")


def save_as(path):
    """
    Save the given scene.
    :param str path: Path to the scene file
    """
    path = path.replace(os.sep, "/")
    cmds.file(rename=path)
    ext_file = os.path.splitext(path)[1]
    try:
        if ext_file == ".ma":
            cmds.file(save=True, type="mayaAscii")
        elif ext_file == ".mb":
            cmds.file(save=True, type="mayaBinary")
    except Exception as ex:
        print("ERROR: Failed to save as to the given path")
