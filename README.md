# Silex client

Python library to execute actions on DCCs and interface with the silex socket service end using websocket.

![python](https://img.shields.io/badge/PYTHON-blue?style=for-the-badge&logo=Python&logoColor=white)
![code formatter](https://img.shields.io/badge/Formatter-BLACK-black?style=for-the-badge)
![code linter](https://img.shields.io/badge/Linter-PYLINT-yellow?style=for-the-badge&labelColor=navajowhite)
![type checker](https://img.shields.io/badge/Type%20checker-MYPY-dodgerblue?style=for-the-badge&labelColor=abcdef)
![gitHub release](https://img.shields.io/github/v/release/ArtFXDev/silex_client?style=for-the-badge&color=orange&labelColor=sandybrown)
<br>
<br>
![unit test](https://github.com/ArtFXDev/silex_client/actions/workflows/unittest.yml/badge.svg)
![format code](https://github.com/ArtFXDev/silex_client/actions/workflows/format.yml/badge.svg)

## Get started

### Prerequisites

- python 3.7
- REZ (optional)

### Installation

```bash
# Simple global install
$ pip install git+https://github.com/ArtFXDev/silex_client.git

# Rez package install (require rez installed)
$ rez pip -i git+https://github.com/ArtFXDev/silex_client.git
```

## Usage

If you use rez all these command must be executed in the rez context (rez env silex_client)

### CLI

```bash
# To list all the available action
$ silex action --list

# To execute a given action (the task-id is optional)
$ silex action <action_name> --task-id <cgwire_task_id>

# You can also set some default values to the parameters (add the --parameter flag for every parameters you wan to set)
$ silex action <action_name> --task-id <cgwire_task_id> --parameter <parameter_name>=<parameter_value>

# To launch a dcc in a silex context (the silex plugin of the selected dcc must be installed)
$ silex launch --dcc <dcc_name> --task_id <cgwire_task_id>
```

### Python

```python
from silex_client.core.context import Context
from silex_client.action.action_query import ActionQuery

# You can set the context by setting the cgwire entity id in an environment variable
import os
os.environ["SILEX_TASK_ID"] = "<cgwire_task_id>"

# Initialize the different modules
Context.get().start_services()

# Resolve an action
action = ActionQuery("<action_name>")
# Set some default parameter values if you want
action.set_parameter("<parameter_name>", <parameter_value>)
# You can also override some attribute of the parameters
action.set_parameter("<parameter_name>", <parameter_value>, hide=True, label=<new_label>)
# Execute the action
action.execute()
```
