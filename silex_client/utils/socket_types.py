"""
Defintions of all the available socket types.
Socket's types can also be a regular class definition but these
constructors gives more control
"""
# pylint: disable=C0103
from __future__ import annotations

import contextlib
import pathlib
from typing import Any, Dict, List, Type


class SocketTypeMeta(type):
    """
    Every sockets have an input type.
    The input type can either be a regular class definition or an instance of
    this metaclass. The advantage of this metaclass is that it returns additional
    information about the type
    """

    def __new__(cls, name: str, bases: tuple, dct: dict):
        return super().__new__(cls, name, bases, dct)

    def serialize(cls) -> Dict[str, Any]:
        """
        When serializing the socket, this mehod can be overriden to send additional
        information about the type
        """
        return {"name": cls.__name__}

    @staticmethod
    def get_default() -> Any:
        """
        When no value is given on a socket, the default value will be None.
        You can override this method to define the default value that will be set for the
        socket
        """
        return None

    def rebuild(cls) -> SocketTypeMeta:
        """
        Socket types definitions are immutable
        To change their attributes, you can use this method to rebuild it
        """
        return cls("NoneType", (type(None),), {})


class AnyType:
    """
    Sometimes you just want to have the raw value without any casting
    """

    def __new__(cls, value):
        return value

def TaskType():
    """
    Builds a socket type that returns a task id as a string
    In the UI, this socket is a task selector on the current project
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
    return SocketTypeMeta("TaskParameter", (str,), attributes)


def IntArrayType(size: int):
    """
    Builds a socket type that returns a list of integers with the given lenght
    In the UI, this socket is multiple integer fields
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
    return SocketTypeMeta("IntArrayParameter", (list,), attributes)


def RangeType(start: int, end: int, increment: int = 1):
    """
    Builds a socket type that returns an integer clipped in the given range
    In the UI, this socket is a slider with the given limits
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
    return SocketTypeMeta("RangeParameter", (int,), attributes)


def RadioSelectType(*list_options, **options):
    """
    Builds a socket type that returns a string in the given options
    In the UI, this socket is a radio select to pick an option
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
    return SocketTypeMeta("RadioSelectParameter", (str,), attributes)


def SelectType(*list_options, **options):
    """
    Builds a socket type that returns a string in the given options
    In the UI, this socket is a dropdown menu.
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
    return SocketTypeMeta("SelectParameter", (str,), attributes)


def MultipleSelectType(*list_options, **options):
    """
    Build same socket as SelectParameterMeta but return a list of strings
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
    return SocketTypeMeta("SelectParameter", (list,), attributes)


def PathType(extensions: List[str] = None, multiple: bool = False):
    """
    Builds a socket type that returns a pathlib path
    In the UI, this socket is a file selector
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
        return SocketTypeMeta("PathParameter", (list,), attributes)

    return SocketTypeMeta("PathParameter", (type(pathlib.Path()),), attributes)


def TextType(color=None):
    """
    Builds a socket type that return a string
    In the UI, this socket display the string with the given color
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

    return SocketTypeMeta("ListParameter", (str,), attributes)


def StringType(
    multiline: bool = False, max_lenght: int = 1000, readonly: bool = False
):
    """
    Builds a socket type that return a string that will be trimed if too long
    In the UI, this socket display a string field
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

    return SocketTypeMeta("StringParameter", (str,), attributes)


def ListType(socket_type: Type):
    """
    This socket takes an other socket as option
    Builds a socket type that return a list of the given type
    In the UI, this socket show the widget of the given type in a list
    """

    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = socket_type(item)

        self.extend(value)

    def serialize():
        item_type = None

        item_type = {"name": socket_type.__name__}
        if isinstance(socket_type, SocketTypeMeta):
            item_type = socket_type.serialize()

        return {"name": "list", "itemType": item_type}

    def get_default():
        return []

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": ListType,
    }

    return SocketTypeMeta("ListParameter", (list,), attributes)


def DictType(key_type: Type, value_type: Type):
    """
    This socket takes other sockets as options
    Builds a socket type that return a dict of the given types
    In the UI, this socket show the widget of the given types in a key/value manner
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
        if isinstance(key_type, SocketTypeMeta):
            key_serialized = key_type.serialize()

        value_serialized = {"name": value_type.__name__}
        if isinstance(value_type, SocketTypeMeta):
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

    return SocketTypeMeta("ListParameter", (dict,), attributes)


def UnionType(socket_types: List[Type]):
    """
    This socket takes other sockets as options
    Builds a socket type that return a dict of the given types
    In the UI, this socket show the widget of the given types in a key/value manner
    """
    # Remove the double sockets types
    socket_types = list(set(socket_types))

    @staticmethod
    def __new__(value):
        # Test if the value match one of the types
        for socket_type in socket_types:
            if isinstance(value, socket_type):
                return value

        # Try to cast the value into one of the types
        for socket_type in socket_types:
            with contextlib.suppress(Exception):
                return socket_type(value)

        raise TypeError(f"None of the types matches the value {value}")

    def serialize():
        serialized_socket_types = []
        for socket_type in socket_types:
            serialized_socket_type = {"name": socket_type.__name__}
            if isinstance(socket_type, SocketTypeMeta):
                serialized_socket_type = socket_type.serialize()

            serialized_socket_types.append(serialized_socket_type)
            serialized_socket_types = list(set(serialized_socket_types))

        return {"name": "union", "types": serialized_socket_types}

    def get_default():
        if socket_types and isinstance(socket_types[0], SocketTypeMeta):
            return socket_types[0].get_default()
        return None

    attributes = {
        "__new__": __new__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": UnionType,
    }

    return SocketTypeMeta("ListParameter", (object,), attributes)
