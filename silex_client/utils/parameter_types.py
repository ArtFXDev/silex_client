import pathlib


class AnyParameter(object):
    def __new__(cls, value):
        return value


class CommandParameterMeta(type):
    def __new__(cls, name: str, bases: tuple, dct: dict):
        def serialize():
            return {
                "name": "parameter",
            }

        attributes = {
            "serialize": serialize,
        }
        attributes.update(dct)
        return super().__new__(cls, name, bases, attributes)

    def get_default(self):
        return None

    def serialize(self):
        return None


class TaskParameterMeta(CommandParameterMeta):
    def __init__(self):
        pass

    def __new__(cls):
        def serialize():
            return {
                "name": "task",
            }

        def get_default():
            return ""

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "TaskParameter", (str,), attributes)


class IntArrayParameterMeta(CommandParameterMeta):
    def __init__(self, size: int):
        pass

    def __new__(cls, size: int):
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
            return [0 for i in range(size)]

        attributes = {
            "__init__": __init__,
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "IntArrayParameter", (list,), attributes)


class RangeParameterMeta(CommandParameterMeta):
    def __init__(self, start: int, end: int, increment: int = 1):
        pass

    def __new__(cls, start: int, end: int, increment: int = 1):
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
        }
        return super().__new__(cls, "RangeParameter", (int,), attributes)


class SelectParameterMeta(CommandParameterMeta):
    def __init__(self, *list_options, **options):
        pass

    def __new__(cls, *list_options, **options):
        for unnamed_option in list_options:
            options[unnamed_option] = unnamed_option

        def serialize():
            return {"name": "select", "options": options}

        def get_default():
            return list(options.values())[0] if options else None

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "SelectParameter", (str,), attributes)


class MultipleSelectParameterMeta(CommandParameterMeta):
    def __init__(self, *list_options, **options):
        pass

    def __new__(cls, *list_options, **options):
        for unnamed_option in list_options:
            options[unnamed_option] = unnamed_option

        def serialize():
            return {"name": "multiple_select", "options": options}

        def get_default():
            return [list(options.values())[0]] if options else None

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "SelectParameter", (list,), attributes)

# TODO: Replace this parameter with ListParameterMeta
class ListParameter(list):
    def __init__(self, value):
        data = value

        if not isinstance(value, list):
            data = [value]
        self.extend(data)

class PathParameterMeta(CommandParameterMeta):
    def __init__(self, extensions=None, multiple=False):
        pass

    def __new__(cls, extensions=None, multiple=False):
        if extensions is None:
            extensions = ["*"]

        def __init_list__(self, value):
            if not isinstance(value, list):
                value = [value]

            for index, item in enumerate(value):
                value[index] = pathlib.Path(item)

            self.extend(value)

        def serialize():
            return {"name": "Path"}

        def get_default():
            return None

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }

        if multiple:
            attributes["__init__"] = __init_list__
            return super().__new__(cls, "PathParameter", (list,), attributes)

        return super().__new__(cls, "PathParameter", (pathlib.Path,), attributes)


class ListParameterMeta(CommandParameterMeta):
    def __init__(self, parameter_type):
        pass

    def __new__(cls, parameter_type):
        def __init__(self, value):
            if not isinstance(value, list):
                value = [value]

            for index, item in enumerate(value):
                value[index] = parameter_type(item)

            self.extend(value)

        def serialize():
            return {"name": "list"}

        def get_default():
            return None

        attributes = {
            "__init__": __init__,
            "serialize": serialize,
            "get_default": get_default,
        }

        return super().__new__(cls, "ListParameter", (list,), attributes)
