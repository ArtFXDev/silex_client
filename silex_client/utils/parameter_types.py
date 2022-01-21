# pylint: disable=C0103

import pathlib
from typing import List, Type

from silex_client.utils.log import logger


class CommandParameterMeta(type):
    def __new__(cls, name: str, bases: tuple, dct: dict):
        return super().__new__(cls, name, bases, dct)

    def serialize(cls):
        pass

    def get_default(cls):
        pass

    def rebuild(cls, *args, **kwargs):
        pass


class AnyParameter(object):
    def __new__(cls, value):
        return value


# TODO: Replace this parameter with ListParameterMeta
class ListParameter(list):
    def __init__(self, value):
        logger.warning(
            "Deprecation warning: The parameter type ListParameter is deprecated in favor if ListParameterMeta()"
        )
        data = value

        if not isinstance(value, list):
            data = [value]
        self.extend(data)


def TaskParameterMeta():
    def serialize():
        return {
            "name": "task",
        }

    def get_default():
        return ""

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": TaskParameterMeta,
    }
    return CommandParameterMeta("TaskParameter", (str,), attributes)


def IntArrayParameterMeta(size: int):
    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = int(item)

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
        "rebuild": IntArrayParameterMeta,
    }
    return CommandParameterMeta("IntArrayParameter", (list,), attributes)


def RangeParameterMeta(start: int, end: int, increment: int = 1):
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
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": RangeParameterMeta,
    }
    return CommandParameterMeta("RangeParameter", (int,), attributes)


def SelectParameterMeta(*list_options, **options):
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def serialize():
        return {"name": "select", "options": options}

    def get_default():
        return list(options.values())[0] if options else None

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": SelectParameterMeta,
    }
    return CommandParameterMeta("SelectParameter", (str,), attributes)


def RadioSelectParameterMeta(*list_options, **options):
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def serialize():
        return {"name": "radio_select", "options": options}

    def get_default():
        return list(options.values())[0] if options else None

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": RadioSelectParameterMeta,
    }
    return CommandParameterMeta("RadioSelectParameter", (str,), attributes)


def MultipleSelectParameterMeta(*list_options, **options):
    for unnamed_option in list_options:
        options[unnamed_option] = unnamed_option

    def serialize():
        return {"name": "multiple_select", "options": options}

    def get_default():
        return [list(options.values())[0]] if options else None

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": MultipleSelectParameterMeta,
    }
    return CommandParameterMeta("SelectParameter", (list,), attributes)


def PathParameterMeta(extensions: List[str] = None, multiple: bool = False):
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
        "rebuild": PathParameterMeta,
    }

    if multiple:
        attributes["__init__"] = __init__
        return CommandParameterMeta("PathParameter", (list,), attributes)

    return CommandParameterMeta("PathParameter", (type(pathlib.Path()),), attributes)


def ListParameterMeta(parameter_type: Type):
    def __init__(self, value):
        if not isinstance(value, list):
            value = [value]

        for index, item in enumerate(value):
            value[index] = parameter_type(item)

        self.extend(value)

    def serialize():
        item_type = None

        item_type = {"name": parameter_type.__name__}
        if isinstance(parameter_type, CommandParameterMeta):
            item_type = parameter_type.serialize()

        return {"name": "list", "itemType": item_type}

    def get_default():
        return []

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": ListParameterMeta,
    }

    return CommandParameterMeta("ListParameter", (list,), attributes)


def TextParameterMeta(color=None):
    def serialize():
        return {"name": "text", "color": color}

    def get_default():
        return ""

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": TextParameterMeta,
    }

    return CommandParameterMeta("ListParameter", (str,), attributes)


def StringParameterMeta(multiline: bool = False, max_lenght: int = 1000):
    def serialize():
        return {"name": "str", "multiline": multiline, "maxLenght": max_lenght}

    def get_default():
        return ""

    attributes = {
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": StringParameterMeta,
    }

    return CommandParameterMeta("StringParameter", (str,), attributes)


def DictParameterMeta(key_type: Type, value_type: Type):
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
                input_value[key] = input_value.pop(key)

        super(type(self), self).__init__(input_value)

    def serialize():
        key_serialized = {"name": key_type.__name__}
        if isinstance(key_type, CommandParameterMeta):
            key_serialized = key_type.serialize()

        value_serialized = {"name": value_type.__name__}
        if isinstance(value_type, CommandParameterMeta):
            value_serialized = value_type.serialize()

        return {"name": "dict", "key": key_serialized, "value": value_serialized}

    def get_default():
        return {}

    attributes = {
        "__init__": __init__,
        "serialize": serialize,
        "get_default": get_default,
        "rebuild": DictParameterMeta,
    }

    return CommandParameterMeta("ListParameter", (dict,), attributes)
