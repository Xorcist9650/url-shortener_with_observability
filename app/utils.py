import re
import string

BASE62_ALPHABET =  string.ascii_letters + string.digits
ID_OFFSET = 1000000 

def encode_base62(num: int) -> str:
    val = num + ID_OFFSET
    chars = []
    while val > 0:
        chars.append(BASE62_ALPHABET[val % 62])
        val //= 62
    return "".join(reversed(chars))

def is_valid_custom_alias(alias: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,16}$", alias))