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

    SCORE_RANK_INTERVALS_OLD = [
        (1007500, "SSS"),
        (1000000, "SS"),
        ( 975000, "S"),
        ( 950000, "AAA"),
        ( 925000, "AA"),
        ( 900000, "A"),
        ( 800000, "BBB"),
        ( 700000, "BB"),
        ( 600000, "B"),
        ( 500000, "C"),
        (      0, "D"),
    ]

    SCORE_RANK_INTERVALS_NEW = [
        (1009000, "SSS+"),  # New only
        (1007500, "SSS"),
        (1005000, "SS+"),  # New only
        (1000000, "SS"),
        ( 990000, "S+"),  # New only
        ( 975000, "S"),
        ( 950000, "AAA"),
        ( 925000, "AA"),
        ( 900000, "A"),
        ( 800000, "BBB"),
        ( 700000, "BB"),
        ( 600000, "B"),
        ( 500000, "C"),
        (      0, "D"),
    ]

    @classmethod
    def game_ver_to_string(cls, ver: int):
        return cls.VERSION_NAMES[ver]


class MapAreaConditionType(IntEnum):
    """Condition types for the GetGameMapAreaConditionApi endpoint. Incomplete.

    For the MAP_CLEARED/MAP_AREA_CLEARED/TROPHY_OBTAINED conditions, the conditionId
    is the map/map area/trophy.

    For the RANK_*/ALL_JUSTICE conditions, the conditionId is songId * 100 + difficultyId.
    For example, Halcyon [ULTIMA] would be 173 * 100 + 4 = 17304.
    """

    ALWAYS_UNLOCKED = 0
    
    MAP_CLEARED = 1
    MAP_AREA_CLEARED = 2
    
    TROPHY_OBTAINED = 3

    RANK_SSSP = 18
    RANK_SSS = 19
    RANK_SSP = 20
    RANK_SS = 21
    RANK_SP = 22
    RANK_S = 23

    ALL_JUSTICE = 28


class MapAreaConditionLogicalOperator(Enum):
    AND = 1
    OR = 2


class AvatarCategory(Enum):
    WEAR = 1
    HEAD = 2
    FACE = 3
    SKIN = 4
    ITEM = 5
    FRONT = 6
    BACK = 7

class ItemKind(IntEnum):
    NAMEPLATE = 1
    
    FRAME = 2
    """
    "Frame" is the background for the gauge/score/max combo display
    shown during gameplay. This item cannot be equipped (as of LUMINOUS PLUS)
    and is hardcoded to the current game's version.
    """

    TROPHY = 3
    SKILL = 4

    TICKET = 5
    """A statue is also a ticket."""

    PRESENT = 6
    MUSIC_UNLOCK = 7
    MAP_ICON = 8
    SYSTEM_VOICE = 9
    SYMBOL_CHAT = 10
    AVATAR_ACCESSORY = 11

    ULTIMA_UNLOCK = 12
    """This only applies to ULTIMA difficulties that are *not* unlocked by
    reaching S rank on EXPERT difficulty or above.
    """


class FavoriteItemKind(IntEnum):
    MUSIC = 1
    RIVAL = 2
    CHARACTER = 3
