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

