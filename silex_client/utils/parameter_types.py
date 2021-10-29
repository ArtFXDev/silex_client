class entity(str):
    pass


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


class IntArrayParameterMeta(CommandParameterMeta):
    def __init__(cls, size: int):
        pass

    def __new__(cls, size: int):
        def serialize():
            return {
                "name": "int_array",
                "size": size,
            }

        def get_default():
            return []

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "IntArrayParameter", (list,), attributes)


class RangeParameterMeta(CommandParameterMeta):
    def __init__(cls, start: int, end: int, increment: int = 1):
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
    def __init__(cls, *options):
        pass

    def __new__(cls, *options):
        def serialize():
            return {"name": "select", "options": options}

        def get_default():
            return options[0] if options else None

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "SelectParameter", (str,), attributes)


class MultipleSelectParameterMeta(CommandParameterMeta):
    def __init__(cls, *options):
        pass

    def __new__(cls, *options):
        def serialize():
            return {"name": "multiple_select", "options": options}

        def get_default():
            return [options[0]] if options else None

        attributes = {
            "serialize": serialize,
            "get_default": get_default,
        }
        return super().__new__(cls, "SelectParameter", (list,), attributes)
