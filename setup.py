#!/usr/bin/env python
from setuptools import setup
from distutils.util import convert_path

# Get version without sourcing silex module
main_ns = {}
with open(convert_path("silex_client/__version__.py")) as version_file:
    exec(version_file.read(), main_ns)

setup(
    version=main_ns["__version__"],
    python_requires="==3.7.*",
)
