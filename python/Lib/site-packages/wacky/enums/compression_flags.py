from enum import IntFlag

from wacky.basic_types.integers import u32
from wacky.enums.adapter import enum_adapter


class CompressionFlag(IntFlag):
    NONE = 0x00

    # Compress with ZLIB - DEPRECATED, USE FNAME
    ZLIB = 0x01
    # Compress with GZIP - DEPRECATED, USE FNAME
    GZIP = 0x02
    # Compress with user defined callbacks - DEPRECATED, USE FNAME
    CUSTOM = 0x04

    # Joint of the previous ones to determine if old flags are being used
    DEPRECATED_FORMAT_FLAGS_MASK = 0x0F

    # Prefer compression that compresses smaller (ONLY VALID FOR COMPRESSION)
    BIAS_MEMORY = 0x10
    # Prefer compression that compresses faster (ONLY VALID FOR COMPRESSION)
    BIAS_SPEED = 0x20
    # Is the source buffer padded out	(ONLY VALID FOR UNCOMPRESS)
    SOURCE_IS_PADDED = 0x80

    # Set of flags that are still allowed
    OPTIONS_FLAGS_MASK = 0xF0


CompressionFlagStruct = enum_adapter(u32, CompressionFlag)
