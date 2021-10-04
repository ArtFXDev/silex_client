# pylint: skip-file
name = "silex_client"
timestamp = 0
version = "0.2.0"

authors = ["ArtFx TD gang"]

description = """
    Set of modules used to execute actions on client's side
    Part of the Silex ecosystem
    """

requires = [
    "python-3.7",
    "PyYAML",
    "types_PyYAML",
    "logzero",
    "python_socketio",
    "rez",
    "aiohttp",
    "jsondiff",
    "dacite",
]

vcs = "git"

tests = {
    "unit": {
        "command": "python -m pytest {root}/test",
        "requires": ["pytest"],
        "run_on": ["default", "pre_release"],
    },
    "linting": {
        "command": "pylint --rcfile={root}/.pylintrc --fail-under=8 {root}/silex_client",
        "requires": ["pylint"],
        "run_on": ["default", "pre_release"],
    },
    "typing": {
        "command": "mypy {root}/silex_client --ignore-missing-imports",
        "requires": ["mypy"],
        "run_on": ["default", "pre_release"],
    },
}

build_command = "python {root}/script/build.py {install}"


def commands():
    """
    Set the environment variables for silex_client
    """
    env.PATH.append("{root}/silex_client")
    env.PATH.append("{root}/tools")
    env.PYTHONPATH.append("{root}")
    env.SILEX_LOG_LEVEL = "DEBUG"
    env.SILEX_ACTION_CONFIG = "{root}/config/action"

    parser_module = ".".join(["silex_client", "cli", "parser"])
    alias("silex", "python -m {parser_module}")
