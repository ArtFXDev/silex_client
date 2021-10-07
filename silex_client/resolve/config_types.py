from typing import Dict, Any, Union

ActionType = Dict[
    # <action name>: <action data>
    str,
    Dict[
        # "steps": <step names>
        str,
        Dict[
            # <step name>: <step data>
            str,
            Dict[
                # "commands" : <command names> or
                # <step specifier> : <step specifier value>
                str,
                Union[
                    str,
                    int,
                    bool,
                    Dict[
                        # <command name> : <command data>
                        str,
                        Dict[
                            # "parameters" : <parameter names> or
                            # <command specifier> : <command specifier value>
                            str,
                            Union[
                                str,
                                int,
                                bool,
                                Dict[
                                    # <parameter name> : <parameter data>
                                    str,
                                    Any,
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ],
    ],
]
