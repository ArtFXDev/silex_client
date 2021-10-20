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

        attributes = {
            "serialize": serialize,
        }
        return super().__new__(cls, "RangeParameter", (int,), attributes)


class SelectParameter(CommandParameterMeta):
    def __init__(cls, *options):
        pass

    def __new__(cls, *options):
        def serialize():
            return {"name": "select", "options": options}

        attributes = {
            "serialize": serialize,
        }
        return super().__new__(cls, "RangeParameter", (str,), attributes)
