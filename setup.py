#!/usr/bin/env python
from distutils.util import convert_path

from setuptools import setup

# Get version without sourcing silex module
main_ns = {}
with open(convert_path("silex_client/__version__.py")) as version_file:
    exec(version_file.read(), main_ns)

setup(
    version=main_ns["__version__"],
    python_requires=">=3.7.*",
    entry_points={
        "silex_action_config": [
            "base=silex_client.config.entry_point:action_entry_points",
        ],
        "console_scripts": [
            "silex=silex_client.cli.parser:main",
        ],
    },
    package_data={"": ["*.yaml", "*.yml", ".env"]},
    include_package_data=True,
)
