import re


# Arnold constant regex sequence match
ARNOLD_MATCH_SEQUENCE = [
    re.compile(r'^.+\W(\<.+\>)\W.+$'),
]