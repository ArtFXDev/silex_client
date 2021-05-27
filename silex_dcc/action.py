"""
Actions definitions
"""

from silex_dcc.utils.context import context


def open():
    """
    Open the given file
    """

    print("open")
    context.execute_action("open")


def save():
    """
    Save the current file
    """

    print("save")
