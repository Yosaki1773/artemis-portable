from enum import Enum, IntEnum

class ChuniConstants:
    GAME_CODE = "SDBT"
    GAME_CODE_NEW = "SDHD"
    GAME_CODE_INT = "SDGS"

    CONFIG_NAME = "chuni.yaml"

    VER_CHUNITHM = 0
    VER_CHUNITHM_PLUS = 1
    VER_CHUNITHM_AIR = 2
    VER_CHUNITHM_AIR_PLUS = 3
    VER_CHUNITHM_STAR = 4
    VER_CHUNITHM_STAR_PLUS = 5
    VER_CHUNITHM_AMAZON = 6
    VER_CHUNITHM_AMAZON_PLUS = 7
    VER_CHUNITHM_CRYSTAL = 8
    VER_CHUNITHM_CRYSTAL_PLUS = 9
    VER_CHUNITHM_PARADISE = 10
    VER_CHUNITHM_NEW = 11
    VER_CHUNITHM_NEW_PLUS = 12
    VER_CHUNITHM_SUN = 13
    VER_CHUNITHM_SUN_PLUS = 14
    VER_CHUNITHM_LUMINOUS = 15
    VER_CHUNITHM_LUMINOUS_PLUS = 16
    VERSION_NAMES = [
        "CHUNITHM",
        "CHUNITHM PLUS",
        "CHUNITHM AIR",
        "CHUNITHM AIR PLUS",
        "CHUNITHM STAR",
        "CHUNITHM STAR  PLUS",
        "CHUNITHM AMAZON",
        "CHUNITHM AMAZON PLUS",
        "CHUNITHM CRYSTAL",
        "CHUNITHM CRYSTAL PLUS",
        "CHUNITHM PARADISE",
        "CHUNITHM NEW!!",
        "CHUNITHM NEW PLUS!!",
        "CHUNITHM SUN",
        "CHUNITHM SUN PLUS",
        "CHUNITHM LUMINOUS",
        "CHUNITHM LUMINOUS PLUS",
    ]

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_NAMES[ver]


class FavoriteItemKind(IntEnum):
    MUSIC = 1
    RIVAL = 2
    CHARACTER = 3
