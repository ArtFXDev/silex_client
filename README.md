# silex_client
Python library to execute actions on DCCs and create a connection with a websocket server.

![python](https://img.shields.io/badge/python-3.7-informational)
![code style](https://img.shields.io/badge/code%20formatter-yapf-blue)
![gitHub release (latest by date)](https://img.shields.io/github/v/release/ArtFXDev/silex_client)
![unit test](https://github.com/ArtFXDev/silex_client/actions/workflows/unittest.yml/badge.svg)
![conform code](https://github.com/ArtFXDev/silex_client/actions/workflows/conform.yml/badge.svg)

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

## Usage

You need to be in a rez environment with the silex_client package. You can set the context with ephemerals like shot, sequence...

```bash
$ rez env silex_client .project-==MY_PROJECT .sequence-==130 .shot-==50
```


### Python

```python
from silex_client.core.context import Context

# Initialize the event loop and the websocket connection
context = Context.get()
context.event_loop.start()
context.ws_connection.start()

# Resolve and execute the action "publish"
action = context.get_action("publish")
# Set some parameters if you want
action.set_parameter("file_path", "/foo/bar")
action.execute()
```

### CLI

```bash
$ silex action publish -p file_path=/foo/bar
```
