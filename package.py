# pylint: skip-file
name = "silex_client"
timestamp = 0
version = "0.3.0"

authors = ["ArtFx TD gang"]

description = """
    Set of modules used to execute actions on client's side
    Part of the Silex ecosystem
    """

requires = [
    "python-3.7",
    "aiogazu",
    "PyYAML",
    "logzero",
    "python_socketio",
    "aiohttp",
    "jsondiff",
    "dacite",
    "Qt.py",
    "python_dotenv",
    "setuptools",
    "tractor",
    "Fileseq",
]

vcs = "git"

tests = {
    "unit": {
        "command": "python -m pytest {root}/test",
        "requires": ["pytest", "aiohttp"],
        "run_on": ["default", "pre_release"],
    },
    "linting": {
        "command": "pylint --rcfile={root}/.pylintrc --fail-under=8 {root}/silex_client",
        "requires": ["pylint"],
        "run_on": ["default", "pre_release"],
    },
    "typing": {
        "command": "mypy --install-types --non-interactive --disallow-untyped-defs {root}/silex_client --ignore-missing-imports",
        "requires": ["mypy"],
        "run_on": ["default", "pre_release"],
    },
}

build_command = "python {root}/script/build.py {install}"


def commands():
    """
    Set the environment variables for silex_client
    """
    import os

    env.PATH.append("{root}/silex_client")
    env.PATH.append("{root}/tools")
    env.PYTHONPATH.append("{root}")
    env.SILEX_ZOU_HOST = os.getenv(
        "SILEX_ZOU_HOST", "http://kitsu.prod.silex.artfx.fr/api"
    )
    env.SILEX_SERVICE_HOST = os.getenv("SILEX_SERVICE_HOST", "http://localhost:5118")
    env.SILEX_LOG_LEVEL = os.getenv("SILEX_LOG_LEVEL", "INFO")
    env.SILEX_ACTION_CONFIG.prepend("{root}/silex_client/config")

    parser_module = ".".join(["silex_client", "cli", "parser"])
    alias("silex", "python -m {parser_module}")
