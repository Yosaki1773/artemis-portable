from string import ascii_lowercase, ascii_uppercase

from wacky.hashing import lookup_tables


def deprecated_string_hash(text: str) -> int:
    value = 0
    bytes_ = encode(to_ascii_upper(text))
    for char in bytes_:
        value = ((value >> 8) & 0x00FFFFFF) ^ lookup_tables.DEPRECATED[
            (value ^ char) & 0x000000FF
        ]

    return value


def crc32_string_hash(text: str) -> int:
    value = 0xFFFFFFFF  # 32-bit bitwise inversion of 0
    bytes_ = encode(text)
    char_size = get_char_size(text)
    for i in range(0, len(bytes_), char_size):
        char = int.from_bytes(bytes_[i : i + char_size], "little")
        value = (value >> 8) ^ lookup_tables.SB8[(value ^ char) & 0xFF]
        char >>= 8
        value = (value >> 8) ^ lookup_tables.SB8[(value ^ char) & 0xFF]
        char >>= 8
        value = (value >> 8) ^ lookup_tables.SB8[(value ^ char) & 0xFF]
        char >>= 8
        value = (value >> 8) ^ lookup_tables.SB8[(value ^ char) & 0xFF]

    return value ^ 0xFFFFFFFF  # 32-bit bitwise inversion


def encode(text: str) -> bytes:
    try:
        return text.encode("ascii")
    except UnicodeEncodeError:
        return text.encode("utf-16-le")


UPPER_ASCII_ONLY = str.maketrans(ascii_lowercase, ascii_uppercase)


def to_ascii_upper(text: str) -> str:
    return text.translate(UPPER_ASCII_ONLY)


def get_char_size(text: str) -> int:
    if text.isascii():
        return 1
    else:
        return 2
