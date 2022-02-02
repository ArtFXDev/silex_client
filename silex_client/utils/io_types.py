"""
Defintions of all the available parameter input types.
Parameter's input types can also be a regular class definition but these
constructors gives more control
"""
# pylint: disable=C0103
from __future__ import annotations

import contextlib
import pathlib
from typing import Any, Dict, List, Type


class IOTypeMeta(type):
    """
    Every parameter have an input type.
    The input type can either be a regular class definition or an instance of
    this metaclass. The advantage of this metaclass is that it returns additional
    information about the type
    """

    def __new__(cls, name: str, bases: tuple, dct: dict):
        return super().__new__(cls, name, bases, dct)

    def serialize(cls) -> Dict[str, Any]:
        """
        When serializing the parameter, this mehod can be overriden to send additional
        information about the parameter type
        """
        return {"name": cls.__name__}

    @staticmethod
    def get_default() -> Any:
        """
        When no value is given on a parameter, the default value will be None.
        You can override this method to define the default value that will be set for the
        parameter
        """
        return None

    def rebuild(cls) -> IOTypeMeta:
        """
        Parameter types definitions are immutable
        To change their attributes, you can use this method to rebuild it
        """
        return cls("InvalidParameter", (type(None),), {})


class AnyType(object):
    """
    Data type that allows any value to be passed through
    """

    def __new__(cls, value):
        return value

def TaskType():
    """
    Builds a parameter type that returns a task id as a string
    In the UI, this parameter is a task selector on the current project
    """

    def serialize():
        return {
            "name": "task",
        }

    def get_default():
        return ""

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": TaskType,
    }
    return IOTypeMeta("TaskParameter", (str,), attributes)


def IntArrayType(size: int):
    """
    Builds a parameter type that returns a list of integers with the given lenght
    In the UI, this parameter is multiple integer fields
    """

    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = int(item)

        if not len(value) == size:
            raise TypeError(
                f"The value {value} does not have the right lenght ({size})"
            )

        self.extend(value)

    def serialize():
        return {
            "name": "int_array",
            "size": size,
        }

    def get_default():
        return [0 for _ in range(size)]

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": IntArrayType,
    }
    return IOTypeMeta("IntArrayParameter", (list,), attributes)


def RangeType(start: int, end: int, increment: int = 1):
    """
    Builds a parameter type that returns an integer clipped in the given range
    In the UI, this parameter is a slider with the given limits
    """

    def __new__(cls, value):
        value = int(value)

        if value < start or value > end:
            raise TypeError(
                f"The value {value} does not fit the expexted range ({start}:{end})"
            )
        return int.__new__(cls, value)

    def serialize():
        return {
            "name": "range",
            "start": start,
            "end": end,
            "increment": increment,
        }

    def get_default():
        return start

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": RangeType,
    }
    return IOTypeMeta("RangeParameter", (int,), attributes)


def RadioSelectType(*list_options, **options):
    """
    Builds a parameter type that returns a string in the given options
    In the UI, this parameter is a radio select to pick an option
    The options can either be a list or a dict. In the case of a dict,
    the keys will be the displayed string and the values the returned ones
    """
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def __new__(cls, value):
        value = str(value)
        if value not in options.values():
            raise TypeError(
                f"The value {value} is not among the possible options ({options})"
            )
        return str.__new__(cls, value)

    def serialize():
        return {"name": "radio_select", "options": options}

    def get_default():
        return list(options.values())[0] if options else None

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": RadioSelectType,
    }
    return IOTypeMeta("RadioSelectParameter", (str,), attributes)


def SelectType(*list_options, **options):
    """
    Builds a parameter type that returns a string in the given options
    In the UI, this parameter is a dropdown menu.
    The options can either be a list or a dict. In the case of a dict,
    the keys will be the displayed string and the values the returned ones
    """
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def __new__(cls, value):
        value = str(value)
        if value not in options.values():
            raise TypeError(
                f"The value {value} is not among the possible options ({options})"
            )
        return str.__new__(cls, value)

    def serialize():
        return {"name": "select", "options": options}

    def get_default():
        return list(options.values())[0] if options else None

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": SelectType,
    }
    return IOTypeMeta("SelectParameter", (str,), attributes)


def MultipleSelectType(*list_options, **options):
    """
    Build same parameter as SelectParameterMeta but return a list of strings
    In the UI, the user can select multiple options
    """
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def __init__(self, values):
        if not isinstance(values, list):
            values = [values]

        for value in values:
            value = str(value)
            if value not in options.values():
                raise TypeError(
                    f"The value {value} is not among the possible options ({options})"
                )

        self.extend([str(value) for value in values])

    def serialize():
        return {"name": "multiple_select", "options": options}

    def get_default():
        return [list(options.values())[0]] if options else None

    attributes = {
        "__ini__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": MultipleSelectType,
    }
    return IOTypeMeta("SelectParameter", (list,), attributes)


def PathType(extensions: List[str] = None, multiple: bool = False):
    """
    Builds a parameter type that returns a pathlib path
    In the UI, this parameter is a file selector
    """
    if extensions is None:
        extensions = ["*"]

    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = pathlib.Path(item)

        self.extend(value)

    def serialize():
        return {
            "name": "Path",
            "extensions": extensions,
            "multiple": multiple,
        }

    def get_default():
        return None

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": PathType,
    }

    if multiple:
        attributes["__init__"] = __init__
        return IOTypeMeta("PathParameter", (list,), attributes)

    return IOTypeMeta("PathParameter", (type(pathlib.Path()),), attributes)


def TextType(color=None):
    """
    Builds a parameter type that return a string
    In the UI, this parameter display the string with the given color
    """

    def serialize():
        return {"name": "text", "color": color}

    def get_default():
        return ""

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": TextType,
    }

    return IOTypeMeta("ListParameter", (str,), attributes)


def StringType(
    multiline: bool = False, max_lenght: int = 1000, readonly: bool = False
):
    """
    Builds a parameter type that return a string that will be trimed if too long
    In the UI, this parameter display a string field
    """

    def __new__(cls, value):
        value = str(value)
        # Trim the name with the max lenght
        value = value[:max_lenght]
        return str.__new__(cls, value)

    def serialize():
        return {
            "name": "str",
            "multiline": multiline,
            "maxLenght": max_lenght,
            "readonly": readonly,
        }

    def get_default():
        return ""

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": StringType,
    }

    return IOTypeMeta("StringParameter", (str,), attributes)


def ListType(parameter_type: Type):
    """
    This parameter takes an other parameter as option
    Builds a parameter type that return a list of the given type
    In the UI, this parameter show the widget of the given type in a list
    """

    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = parameter_type(item)

        self.extend(value)

    def serialize():
        item_type = None

        item_type = {"name": parameter_type.__name__}
        if isinstance(parameter_type, IOTypeMeta):
            item_type = parameter_type.serialize()

        return {"name": "list", "itemType": item_type}

    def get_default():
        return []

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": ListType,
    }

    return IOTypeMeta("ListParameter", (list,), attributes)


def DictType(key_type: Type, value_type: Type):
    """
    This parameter takes other parameters as options
    Builds a parameter type that return a dict of the given types
    In the UI, this parameter show the widget of the given types in a key/value manner
    """

    def __init__(self, input_value):
        # Cast the input into a dict
        if not isinstance(input_value, dict):
            value = dict(input_value)

        # Cast the input key into the given type
        for key in input_value.keys():
            if not isinstance(key, key_type):
                input_value[key_type(key)] = input_value.pop(key)
        # Cast the input value into the given type
        for key, value in input_value.items():
            if not isinstance(value, value_type):
                input_value[key] = value_type(input_value.pop(key))

        super(type(self), self).__init__(input_value)

    def serialize():
        key_serialized = {"name": key_type.__name__}
        if isinstance(key_type, IOTypeMeta):
            key_serialized = key_type.serialize()

        value_serialized = {"name": value_type.__name__}
        if isinstance(value_type, IOTypeMeta):
            value_serialized = value_type.serialize()

        return {"name": "dict", "key": key_serialized, "value": value_serialized}

    def get_default():
        return {}

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": DictType,
    }

    return IOTypeMeta("ListParameter", (dict,), attributes)


def UnionType(parameter_types: List[Type]):
    """
    This parameter takes other parameters as options
    Builds a parameter type that return a dict of the given types
    In the UI, this parameter show the widget of the given types in a key/value manner
    """
    # Remove the double parameters types
    parameter_types = list(set(parameter_types))

    @staticmethod
    def __new__(value):
        # Test if the value match one of the types
        for parameter_type in parameter_types:
            if isinstance(value, parameter_type):
                return value

        # Try to cast the value into one of the types
        for parameter_type in parameter_types:
            with contextlib.suppress(Exception):
                return parameter_type(value)

        raise TypeError(f"None of the types matches the value {value}")

    def serialize():
        serialized_parameter_types = []
        for parameter_type in parameter_types:
            serialized_parameter_type = {"name": parameter_type.__name__}
            if isinstance(parameter_type, IOTypeMeta):
                serialized_parameter_type = parameter_type.serialize()

            serialized_parameter_types.append(serialized_parameter_type)
            serialized_parameter_types = list(set(serialized_parameter_types))

        return {"name": "union", "types": serialized_parameter_types}

    def get_default():
        if parameter_types and isinstance(parameter_types[0], IOTypeMeta):
            return parameter_types[0].get_default()
        return None

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": UnionType,
    }

    return IOTypeMeta("ListParameter", (object,), attributes)
