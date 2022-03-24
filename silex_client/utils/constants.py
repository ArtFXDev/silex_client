import re

# Arnold constant regex sequence match
ARNOLD_MATCH_SEQUENCE = [
    re.compile(r"^.+\W(\<.+\>)\W.+$"),
]

# Vray constant regex sequence match
VRAY_MATCH_SEQUENCE = [
    re.compile(r"^.+\W(\<.+\>)\W.+$"),
    re.compile(r"^.+[^\w#](#+)\W.+$"),
]

# Match environement variable in path for differente format
ENV_VARIABLE_FORMAT = [
    re.compile(r'\$(\w+)'),
    re.compile(r'\%(\w+)\%'),
]

