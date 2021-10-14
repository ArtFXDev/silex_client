from typing import Dict, Any, Union

# fmt: off

# Definition of an action represented as a YAML
ActionYAML = Dict[
    # <action name>: <action data>
    str, Dict[
        # "steps": <step names>
        str, Union[bool, str, Dict[
            # <step name>: <step data>
            str, Dict[
                # "commands" : <command names> or
                # <step specifier> : <step specifier value>
                str, Union[str, int, bool, Dict[
                    # <command name> : <command data>
                    str, Dict[
                        # "parameters" : <parameter names> or
                        # <command specifier> : <command specifier value>
                        str, Union[str, int, bool, Dict[
                            # <parameter name> : <parameter data>
                            str, Any]
                        ]
                    ]
                ]]
            ]
        ]]
    ]
]

# Definition of an action represented as a dataclass
ActionDataclass = Dict[
    # <action name>: <action data>
    str, Dict[
        # "steps": <step names>
        str, Union[str, bool, Dict[
            # <step name>: <step data>
            str, Union[str, Dict[
                # "commands" : <command names> or
                # <step specifier> : <step specifier value>
                str, Union[str, int, bool, Dict[
                    # <command name> : <command data>
                    str, Union[str, Dict[
                        # "parameters" : <parameter names> or
                        # <command specifier> : <command specifier value>
                        str, Union[str, int, bool, Dict[
                            # <parameter name> : <parameter data>
                            str, Any]
                        ]
                    ]]
                ]]
            ]]
        ]]
    ]
]

ActionType = Union[ActionDataclass, ActionYAML]
