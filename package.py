name = "silex_client"

version = "0.0.0"

authors = ["ArtFx TD gang"]

description = \
    """
    Set of modules used to execute actions on client's side
    Part of the Silex ecosystem
    """

requires = ["python-3.7+", "PyYAML", "logzero", "pytest"]

vcs = "git"

tests = {"unit": "python -m pytest {root}"}

build_command = "python {root}/script/build.py {install}"


def pre_build_commands():
    """
    Run the test before each build
    """
    pass


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
