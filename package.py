# pylint: skip-file
name = "silex_client"

version = "0.0.0"

authors = ["ArtFx TD gang"]

description = \
    """
    Set of modules used to execute actions on client's side
    Part of the Silex ecosystem
    """

requires = ["python-3.7", "PyYAML", "logzero", "websockets"]

vcs = "git"

tests = {
    "unit": {
        "command": "python -m pytest {root}/silex_client",
        "requires": ["pytest"],
        "run_on": ["default", "pre_release"]
    },
    "lint": {
        "command":
        "pylint --rcfile={root}/.pylintrc --fail-under=8 {root}/silex_client",
        "requires": ["pylint", "pytest"],
        "run_on": ["default", "pre_release"]
    }
}

build_command = "python {root}/script/build.py {install}"


def commands():
    """
    Set the environment variables for silex_client
    """
    env.PATH.append("{root}/silex_client")
    env.PYTHONPATH.append("{root}/silex_client")
    env.SILEX_LOG_LEVEL = "DEBUG"


def uuid():
    """
    Automatically generate a uuid for the package
    """
    import uuid

    return uuid.uuid4().hex
