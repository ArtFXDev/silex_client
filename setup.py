#!/usr/bin/env python
from setuptools import setup
from distutils.util import convert_path

# Get version without sourcing silex module
# (to avoid importing dependencies yet to be installed)
main_ns = {}
with open(convert_path("silex_client/__version__.py")) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    version=main_ns["__version__"],
    python_requires="==3.7.*",
    entry_points={
        "silex_action_config": [
            "base=silex_client.config.entry_point:action_entry_points",
        ],
        "console_scripts": [
            "silex=silex_client.cli.parser:main",
        ],
    },
)
