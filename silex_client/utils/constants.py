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

# Match environment variable in path for different format
ENV_VARIABLE_FORMAT = [
    re.compile(r'\$(\w+)'),
    re.compile(r'\${(\w+)}'),
    re.compile(r'\%(\w+)\%'),
]

