# silex_client
Python library to execute action on DCCs and create a connection with a websocket server.

![unit test](https://github.com/ArtFXDev/silex_client/actions/workflows/unittest.yml/badge.svg)
![conform code](https://github.com/ArtFXDev/silex_client/actions/workflows/conform.yml/badge.svg)
![gitHub pipenv locked python version](https://img.shields.io/github/pipenv/locked/python-version/ArtFXDev/silex_client)
![code style](https://img.shields.io/badge/code%20formatter-yapf-blue)
![gitHub release (latest by date)](https://img.shields.io/github/v/release/ArtFXDev/silex_client)

## Get started

### Prerequisites

- python 3.7
- REZ
- REZ packages (see package.py for the list of required packages)

You can use the provided rez_install.ps1 for Windows and rez_install.sh for Linux to make the setup easier. It will install REZ if not found and install all the required REZ packages

### Installation
```
cd path/to/silex_client/root
rez build —-install
```
