from typing import Tuple, List, Optional, Dict
import struct
import logging
from datetime import datetime
from enum import IntEnum

BIGINT_OFF = 16
LONG_OFF = 8
INT_OFF = 4
SHORT_OFF = 2
BYTE_OFF = 1

DT_FMT = "%Y%m%d%H%M%S"

def fmt_dt(d: Optional[datetime] = None) -> str:
    if d is None:
        d = datetime.fromtimestamp(0)
    return d.strftime(DT_FMT)

def prs_dt(s: Optional[str] = None) -> datetime:
    if not s:
        s = "19691231190000"
    return datetime.strptime(s, DT_FMT)

def decode_num(data: bytes, offset: int, size: int) -> int:
    try:
        return int.from_bytes(data[offset:offset + size], 'big')
    except:
        logging.getLogger('sao').error(f"Failed to parse {data[offset:offset + size]} as BE number of width {size}")
        return 0

def decode_byte(data: bytes, offset: int) -> int:
    return decode_num(data, offset, BYTE_OFF)

def decode_short(data: bytes, offset: int) -> int:
    return decode_num(data, offset, SHORT_OFF)

def decode_int(data: bytes, offset: int) -> int:
    return decode_num(data, offset, INT_OFF)

def decode_long(data: bytes, offset: int) -> int:
    return decode_num(data, offset, LONG_OFF)

def decode_bigint(data: bytes, offset: int) -> int:
    return decode_num(data, offset, BIGINT_OFF)

def decode_str(data: bytes, offset: int) -> Tuple[str, int]:
    try:
        str_len = decode_int(data, offset)
        num_bytes_decoded = INT_OFF + str_len
        str_out = data[offset + INT_OFF:offset + num_bytes_decoded].decode("utf-16-le", errors="replace")
        return (str_out, num_bytes_decoded)
    except:
        logging.getLogger('sao').error(f"Failed to parse {data[offset:]} as string!")
        return ("", 0)

def decode_arr_num(data: bytes, offset:int, element_size: int) -> Tuple[List[int], int]:
    size = 0
    num_obj = decode_int(data, offset + size)
    size += INT_OFF
    
    ret: List[int] = []
    for _ in range(num_obj):
        ret.append(decode_num(data, offset + size, element_size))
        size += element_size
    
    return (ret, size)

def decode_arr_str(data: bytes, offset: int) -> Tuple[List[str], int]:
    size = 0
    num_obj = decode_int(data, offset + size)
    size += INT_OFF
    
    ret: List[str] = []
    for _ in range(num_obj):
        tmp = decode_str(data, offset + size)
        ret.append(tmp[0])
        size += tmp[1]
    
    return (ret, size)

def decode_date_str(data: bytes, offset: int) -> Tuple[datetime, int]:
    s, new_o = decode_str(data, offset)
    return (prs_dt(s), new_o)

def decode_bool(data: bytes, offset: int) -> bool:
    return bool(decode_byte(data, offset))

def encode_byte(data: int) -> bytes:
    if data is None:
        return b"\0"
    try:
        return struct.pack("!b", int(data))
    except Exception as e:
        logging.getLogger('sao').error(f"Failed to encode {data} as byte! - {e}")
        return b"\0"

def encode_short(data: int) -> bytes:
    if data is None:
        return b"\0\0"
    try:
        return struct.pack("!h", int(data))
    except Exception as e:
        logging.getLogger('sao').error(f"Failed to encode {data} as short! - {e}")
        return b"\0\0"

def encode_int(data: int) -> bytes:
    if data is None:
        return b"\0\0\0\0"
    try:
        return struct.pack("!i", int(data))
    except Exception as e:
        logging.getLogger('sao').error(f"Failed to encode {data} as int! - {e}")
        return b"\0\0\0\0"

def encode_long(data: int) -> bytes:
    if data is None:
        return b"\0\0\0\0\0\0\0\0"
    return struct.pack("!l", int(data))

def encode_bigint(data: int) -> bytes:
    if data is None:
        return b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"
    return struct.pack("!q", int(data))

def encode_str(s: str) -> bytes:
    if s is None:
        return b"\0\0\0\0"
    try:
        str_bytes = str(s).encode("utf-16-le", errors="replace")
        str_len_bytes = struct.pack("!I", len(str_bytes))
        return str_len_bytes + str_bytes
    except Exception as e:
        logging.getLogger('sao').error(f"Failed to encode {s} as bytes! - {e}")
        return b""

def encode_arr_num(data: List[int], element_size: int) -> bytes:
    if data is None:
        return b"\0\0\0\0"
    ret = encode_int(len(data))
        
    if element_size == BYTE_OFF:
        for x in data:
            ret += encode_byte(x)
    elif element_size == SHORT_OFF:
        for x in data:
            ret += encode_short(x)
    elif element_size == INT_OFF:
        for x in data:
            ret += encode_int(x)
    elif element_size == LONG_OFF:
        for x in data:
            ret += encode_long(x)
    elif element_size == BIGINT_OFF:
        for x in data:
            ret += encode_bigint(x)
    else:
        logging.getLogger('sao').error(f"Unknown element size {element_size}")
        return b"\x00" * INT_OFF

    return ret

def encode_bool(b: bool) -> bytes:
    if b is None:
        return b"\0"
    return encode_byte(int(b))

def encode_date_str(d: datetime) -> bytes:
    return encode_str(fmt_dt(d))

class PrintType(IntEnum):
    NONE = 0
    FromStorage = 1
    FromGasha = 2

class AuthType(IntEnum):
    UNKNOWN = 0
    CARD = 1
    MOBLE = 2

class ActTypeConsumeTicket(IntEnum):
    QuestEpisodeBeginner = 1
    QuestEpisode = 2
    QuestTrialTowerBeginner = 3
    QuestTrialTower = 4
    QuestPvEBeginner = 5
    QuestPvE = 6
    QuestContinue = 7
    QuesRarityUp = 8
    QuestEpisodeBoost = 9
    QuestTrialTowerBoost = 10
    QuestPvEBoost = 11
    CustomModeExtend = 21
    CustomModeRetry = 22
    YuiMedalShop = 31

class ActTypeChangeParty(IntEnum):
    MANUAL = 1
    AUTO = 2

class ActTypeConsumeCredit(IntEnum):
    PurchaseTicketA1 = 1
    PurchaseTicketA2 = 2
    PurchaseTicketA6 = 3
    PurchaseTicketB1 = 4
    PurchaseTicketB2 = 5
    PurchaseTicketB7 = 6
    PurchaseTicketC1 = 7
    PurchaseTicketC3 = 8
    PurchaseTicketC8 = 9
    PurchaseTicketD1 = 10
    PurchaseTicketD2 = 11
    PurchaseTicketD6 = 12
    PurchaseTicketE1 = 13
    PurchaseTicketE3 = 14
    PurchaseTicketE8 = 15
    PurchaseTicketF1 = 16
    PurchaseTicketF2 = 17
    PurchaseTicketF6 = 18
    QuestContinue = 21
    QuestRarityUp = 22
    GashaSatelite = 31
    GashaSateliteAdd1 = 32
    GashaSateliteAdd2 = 33
    GashaTerminal = 41
    GashaTerminalAdd1 = 42
    GashaTerminalAdd2 = 43
    ResourceDischarge = 44
    ResourceHolo = 45
    ProfileCardDischarge = 46
    ProfileCardHolo = 47

class ProtocolErrorNum(IntEnum): # header error_num field
    SUCCESS = 0
    
    ALREADY_LOGIN_DIFF = 1301
    ALREADY_LOGIN_SAME = 1302
    INVALID_AUTH_TYPE = 1303
    INVALID_CABINET_TYPE = 1304
    AMID_SERVER_CONNECT_ERROR = 1305
    AMID_INFO_REQUEST_ERROR = 1306
    NOT_EXIST_PLAY_DATA = 1307
    HAVE_NEVER_PLAYED_SATELLITE = 1308
    
    RESOURCE_CARD_ERR1 = 4831 # ScanQRQuestProfileCard
    RESOURCE_CARD_NOT_EXIST = 4832
    RESOURCE_CARD_ERR3 = 4833 # ScanQRQuestResourceCard / ScanQRShopResourceCard
    RESOURCE_CARD_ERR6 = 4836 # ScanQRQuestResourceCard / ScanQRShopResourceCard
    RESOURCE_CARD_ERR7 = 4837 # ScanQRQuestResourceCard / ScanQRShopResourceCard
    RESOURCE_CARD_ERR8 = 4838 # ScanQRShopResourceCard
    RESOURCE_CARD_ERR9 = 4839 # ScanQRQuestProfileCard
    
    CREDIT_GASHA_ERROR = 7111

    PURCHASE_ERROR = 7711
    
    PAYING_PLAY_END_ERROR = 9120

    CODE_ANALYSIS_API_NOT_RESPONSE = 9201
    CODE_ANALYSIS_API_INIQUITY_SERIAL_CODE = 9202
    CODE_USE_API_USED_SERIAL_CODE = 9203
    CODE_USE_API_NOT_RESPONSE = 9206
    CODE_USE_API_NG = 9207
    CODE_USE_API_LOCK = 9208
    CODE_USE_API_MAINTENANCE = 9209
    CODE_ANALYSIS_API_NOT_MASTER_DATA = 9210
    CODE_ANALYSIS_API_EXPIRED_SERIAL_CODE = 9211

class ProtocolResult(IntEnum): # result field, if used
    NONE = -1
    FAILED = 0
    SUCCESS = 1
    PARAM_ERROR = 2
    MAINTENANCE = 3
    CONNECT_ERROR = 99

class BaseHelper:
    def __init__(self, data: bytes, offset: int) -> None:
        self._sz = 0
        
    @classmethod
    def from_args(cls) -> "BaseHelper":
        return cls(b"", 0)
    
    def get_size(self) -> int:
        return self._sz
    
    def make(self) -> bytes:
        return b""

def decode_arr_cls(data: bytes, offset: int, cls: BaseHelper):
    size = 0
    num_cls = decode_int(data, offset + size)
    size += INT_OFF
    cls_type = type(cls)
    
    ret: List[cls_type] = [] # type: ignore
    for _ in range(num_cls):
        tmp = cls(data, offset + size)
        size += tmp.get_size()
        ret.append(tmp)
    
    return (ret, size)

def encode_arr_cls(data: List[BaseHelper]) -> bytes:
    ret = encode_int(len(data))
    
    for x in data:
        ret += x.make()
    
    return ret

class MaterialCommonRewardUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.common_reward_type = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        user_common_reward_id = decode_str(data, offset + self._sz)
        self.user_common_reward_id = user_common_reward_id[0]
        self._sz += user_common_reward_id[1]

class QuestScenePlayEndUnanalyzedLogRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unanalyzed_log_grade_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_data, new_off = decode_arr_cls(data, off, CommonRewardData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, grade: int, reward: Dict) -> "QuestScenePlayEndUnanalyzedLogRewardData":
        ret = cls(b"\x00" * 8, 0)
        ret.unanalyzed_log_grade_id = grade
        ret.common_reward_data = [CommonRewardData.from_args(reward.get('CommonRewardType'), reward.get('CommonRewardId'), reward.get('CommonRewardNum'))]
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unanalyzed_log_grade_id) \
        + encode_arr_cls(self.common_reward_data)

class PartyTeamData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_party_team_id, new_off = decode_str(data, off)
        off += new_off

        self.arrangement_num = decode_byte(data, off)
        off += BYTE_OFF

        self.user_hero_log_id, new_off = decode_str(data, off)
        off += new_off

        self.main_weapon_user_equipment_id, new_off = decode_str(data, off)
        off += new_off

        self.sub_equipment_user_equipment_id, new_off = decode_str(data, off)
        off += new_off

        self.skill_slot1_skill_id = decode_int(data, off)
        off += INT_OFF

        self.skill_slot2_skill_id = decode_int(data, off)
        off += INT_OFF

        self.skill_slot3_skill_id = decode_int(data, off)
        off += INT_OFF

        self.skill_slot4_skill_id = decode_int(data, off)
        off += INT_OFF

        self.skill_slot5_skill_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, party_team_id: str, arr_num: int, data: Dict) -> "PartyTeamData":
        ret = cls(b"\x00" * 37, 0)
        ret.user_party_team_id = party_team_id
        ret.arrangement_num = arr_num
        ret.user_hero_log_id = data['id']
        ret.main_weapon_user_equipment_id = data['main_weapon']
        ret.sub_equipment_user_equipment_id = data['sub_equipment']
        ret.skill_slot1_skill_id = data['skill_slot1_skill_id']
        ret.skill_slot2_skill_id = data['skill_slot2_skill_id']
        ret.skill_slot3_skill_id = data['skill_slot3_skill_id']
        ret.skill_slot4_skill_id = data['skill_slot4_skill_id']
        ret.skill_slot5_skill_id = data['skill_slot5_skill_id']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_party_team_id) \
        + encode_byte(self.arrangement_num) \
        + encode_str(self.user_hero_log_id) \
        + encode_str(self.main_weapon_user_equipment_id) \
        + encode_str(self.sub_equipment_user_equipment_id) \
        + encode_int(self.skill_slot1_skill_id) \
        + encode_int(self.skill_slot2_skill_id) \
        + encode_int(self.skill_slot3_skill_id) \
        + encode_int(self.skill_slot4_skill_id) \
        + encode_int(self.skill_slot5_skill_id)

class CommonRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.common_reward_type = decode_short(data, off)
        off += SHORT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, reward_type: int, reward_id: int, reward_num: int) -> "CommonRewardData":
        ret = cls(b"\x00" * 10, 0)
        ret.common_reward_type = reward_type
        ret.common_reward_id = reward_id
        ret.common_reward_num = reward_num
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num)

class ReadProfileCardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.profile_card_code, new_off = decode_str(data, off)
        off += new_off

        self.nick_name, new_off = decode_str(data, off)
        off += new_off

        self.rank_num = decode_short(data, off)
        off += SHORT_OFF

        self.setting_title_id = decode_int(data, off)
        off += INT_OFF

        self.skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_log_level = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_equipment_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_enhancement_value = decode_short(data, off)
        off += SHORT_OFF

        self.main_weapon_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.main_weapon_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_equipment_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_enhancement_value = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equipment_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equipment_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.holographic_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, user_profile: Dict, hero_data: Dict) -> "ReadProfileCardData":
        ret = cls(b"\x00" * 185, 0)
        # TODO: real data
        ret.profile_card_code = ""
        ret.nick_name = ""
        ret.rank_num = 0
        ret.setting_title_id = 0
        ret.skill_id = 0
        ret.hero_log_hero_log_id = 0
        ret.hero_log_log_level = 0
        ret.hero_log_awakening_stage = 0
        ret.hero_log_property1_property_id = 0
        ret.hero_log_property1_value1 = 0
        ret.hero_log_property1_value2 = 0
        ret.hero_log_property2_property_id = 0
        ret.hero_log_property2_value1 = 0
        ret.hero_log_property2_value2 = 0
        ret.hero_log_property3_property_id = 0
        ret.hero_log_property3_value1 = 0
        ret.hero_log_property3_value2 = 0
        ret.hero_log_property4_property_id = 0
        ret.hero_log_property4_value1 = 0
        ret.hero_log_property4_value2 = 0
        ret.main_weapon_equipment_id = 0
        ret.main_weapon_enhancement_value = 0
        ret.main_weapon_awakening_stage = 0
        ret.main_weapon_property1_property_id = 0
        ret.main_weapon_property1_value1 = 0
        ret.main_weapon_property1_value2 = 0
        ret.main_weapon_property2_property_id = 0
        ret.main_weapon_property2_value1 = 0
        ret.main_weapon_property2_value2 = 0
        ret.main_weapon_property3_property_id = 0
        ret.main_weapon_property3_value1 = 0
        ret.main_weapon_property3_value2 = 0
        ret.main_weapon_property4_property_id = 0
        ret.main_weapon_property4_value1 = 0
        ret.main_weapon_property4_value2 = 0
        ret.sub_equipment_equipment_id = 0
        ret.sub_equipment_enhancement_value = 0
        ret.sub_equipment_awakening_stage = 0
        ret.sub_equipment_property1_property_id = 0
        ret.sub_equipment_property1_value1 = 0
        ret.sub_equipment_property1_value2 = 0
        ret.sub_equipment_property2_property_id = 0
        ret.sub_equipment_property2_value1 = 0
        ret.sub_equipment_property2_value2 = 0
        ret.sub_equipment_property3_property_id = 0
        ret.sub_equipment_property3_value1 = 0
        ret.sub_equipment_property3_value2 = 0
        ret.sub_equipment_property4_property_id = 0
        ret.sub_equipment_property4_value1 = 0
        ret.sub_equipment_property4_value2 = 0
        ret.holographic_flag = 0
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.profile_card_code) \
        + encode_str(self.nick_name) \
        + encode_short(self.rank_num) \
        + encode_int(self.setting_title_id) \
        + encode_short(self.skill_id) \
        + encode_int(self.hero_log_hero_log_id) \
        + encode_short(self.hero_log_log_level) \
        + encode_short(self.hero_log_awakening_stage) \
        + encode_int(self.hero_log_property1_property_id) \
        + encode_int(self.hero_log_property1_value1) \
        + encode_int(self.hero_log_property1_value2) \
        + encode_int(self.hero_log_property2_property_id) \
        + encode_int(self.hero_log_property2_value1) \
        + encode_int(self.hero_log_property2_value2) \
        + encode_int(self.hero_log_property3_property_id) \
        + encode_int(self.hero_log_property3_value1) \
        + encode_int(self.hero_log_property3_value2) \
        + encode_int(self.hero_log_property4_property_id) \
        + encode_int(self.hero_log_property4_value1) \
        + encode_int(self.hero_log_property4_value2) \
        + encode_int(self.main_weapon_equipment_id) \
        + encode_short(self.main_weapon_enhancement_value) \
        + encode_short(self.main_weapon_awakening_stage) \
        + encode_int(self.main_weapon_property1_property_id) \
        + encode_int(self.main_weapon_property1_value1) \
        + encode_int(self.main_weapon_property1_value2) \
        + encode_int(self.main_weapon_property2_property_id) \
        + encode_int(self.main_weapon_property2_value1) \
        + encode_int(self.main_weapon_property2_value2) \
        + encode_int(self.main_weapon_property3_property_id) \
        + encode_int(self.main_weapon_property3_value1) \
        + encode_int(self.main_weapon_property3_value2) \
        + encode_int(self.main_weapon_property4_property_id) \
        + encode_int(self.main_weapon_property4_value1) \
        + encode_int(self.main_weapon_property4_value2) \
        + encode_int(self.sub_equipment_equipment_id) \
        + encode_short(self.sub_equipment_enhancement_value) \
        + encode_short(self.sub_equipment_awakening_stage) \
        + encode_int(self.sub_equipment_property1_property_id) \
        + encode_int(self.sub_equipment_property1_value1) \
        + encode_int(self.sub_equipment_property1_value2) \
        + encode_int(self.sub_equipment_property2_property_id) \
        + encode_int(self.sub_equipment_property2_value1) \
        + encode_int(self.sub_equipment_property2_value2) \
        + encode_int(self.sub_equipment_property3_property_id) \
        + encode_int(self.sub_equipment_property3_value1) \
        + encode_int(self.sub_equipment_property3_value2) \
        + encode_int(self.sub_equipment_property4_property_id) \
        + encode_int(self.sub_equipment_property4_value1) \
        + encode_int(self.sub_equipment_property4_value2) \
        + encode_byte(self.holographic_flag)

class QuestSceneBestScoreUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.clear_time = decode_int(data, off)
        off += INT_OFF

        self.combo_num = decode_int(data, off)
        off += INT_OFF

        self.total_damage, new_off = decode_str(data, off)
        off += new_off

        self.concurrent_destroying_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSceneBestScoreUserData":
        ret = cls(b"\x00" * 14, 0)
        ret.clear_time = data['clear_time']
        ret.combo_num = data['combo_num']
        ret.total_damage = data['total_damage']
        ret.concurrent_destroying_num = data['concurrent_destroying_num']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.clear_time) \
        + encode_int(self.combo_num) \
        + encode_str(self.total_damage) \
        + encode_short(self.concurrent_destroying_num)

class QuestSceneExBonusUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_bonus_table_id = decode_int(data, off)
        off += INT_OFF

        self.achievement_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, table_id: int = 0, ach_flag: bool = False) -> "QuestSceneExBonusUserData":
        ret = cls(b"\x00" * 5, 0)
        ret.ex_bonus_table_id = table_id
        ret.achievement_flag = ach_flag
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_bonus_table_id) \
        + encode_byte(self.achievement_flag)

class QuestSceneUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_type = decode_byte(data, off)
        off += BYTE_OFF

        self.quest_scene_id = decode_short(data, off)
        off += SHORT_OFF

        self.clear_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.quest_scene_best_score_user_data: List[QuestSceneBestScoreUserData] = []
        self.quest_scene_best_score_user_data, new_off = decode_arr_cls(data, off, QuestSceneBestScoreUserData)
        off += new_off

        self.quest_scene_ex_bonus_user_data_list: List[QuestSceneExBonusUserData] = []
        self.quest_scene_ex_bonus_user_data_list, new_off = decode_arr_cls(data, off, QuestSceneExBonusUserData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSceneUserData":
        ret = cls(b"\x00" * 12, 0)
        ret.quest_type = data['quest_type']
        ret.quest_scene_id = data['quest_scene_id']
        ret.clear_flag = data['quest_clear_flag']
        ret.quest_scene_best_score_user_data = [QuestSceneBestScoreUserData.from_args(data)]
        ret.quest_scene_ex_bonus_user_data_list = [] # TODO
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.quest_type) \
        + encode_short(self.quest_scene_id) \
        + encode_byte(self.clear_flag) \
        + encode_arr_cls(self.quest_scene_best_score_user_data) \
        + encode_arr_cls(self.quest_scene_ex_bonus_user_data_list)

class QuestScenePlayStartAppearancePlayerTraceData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_quest_scene_player_trace_id, new_off = decode_str(data, off)
        off += new_off

        self.nick_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, sesh_id:int, nickname: str) -> "QuestScenePlayStartAppearancePlayerTraceData":
        ret = cls(b"\x00" * 8, 0)
        ret.user_quest_scene_player_trace_id = str(sesh_id)
        ret.nick_name = nickname
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_quest_scene_player_trace_id) \
        + encode_str(self.nick_name)

class QuestScenePlayStartResponseData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.appearance_player_trace_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayStartAppearancePlayerTraceData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, sesh_id: int, nickname: str) -> "QuestScenePlayStartResponseData":
        ret = cls(b"\x00" * 99, 0)
        ret.appearance_player_trace_data_list = [QuestScenePlayStartAppearancePlayerTraceData.from_args(sesh_id, nickname)]
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_arr_cls(self.appearance_player_trace_data_list)

class QuestScenePlayStartRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_party_id, new_off = decode_str(data, off)
        off += new_off

        self.appoint_leader_resource_card_code, new_off = decode_str(data, off)
        off += new_off

        self.use_profile_card_code, new_off = decode_str(data, off)
        off += new_off

        self.quest_drop_boost_apply_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayStartRequestData":
        ret = cls(b"\x00" * 13, 0)
        ret.user_party_id = data['UserPartyId']
        ret.appoint_leader_resource_card_code = data['AppointLeaderResourceCardCode']
        ret.use_profile_card_code = data['UseProfileCardCode']
        ret.quest_drop_boost_apply_flag = data['QuestDropBoostApplyFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_party_id) \
        + encode_str(self.appoint_leader_resource_card_code) \
        + encode_str(self.use_profile_card_code) \
        + encode_byte(self.quest_drop_boost_apply_flag)

class QuestSceneMultiPlayStartEntryUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.host_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSceneMultiPlayStartEntryUserData":
        ret = cls(b"\x00" * 9, 0)
        ret.store_id = data['StoreId']
        ret.user_id = data['UserId']
        ret.host_flag = data['HostFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.store_id) \
        + encode_str(self.user_id) \
        + encode_byte(self.host_flag)

class QuestSceneMultiPlayStartRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.room_id, new_off = decode_str(data, off)
        off += new_off

        self.matching_mode = decode_byte(data, off)
        off += BYTE_OFF

        self.entry_user_data_list: List[QuestSceneMultiPlayStartEntryUserData] = []
        self.entry_user_data_list, new_off = decode_arr_cls(data, off, QuestSceneMultiPlayStartEntryUserData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSceneMultiPlayStartRequestData":
        ret = cls(b"\x00" * 9, 0)
        ret.room_id = data['RoomId']
        ret.matching_mode = data['MatchingMode']
        ret.entry_user_data_list = []
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.room_id) \
        + encode_byte(self.matching_mode) \
        + encode_arr_cls(self.entry_user_data_list)

class QuestSceneMultiPlayStartResponseData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.dummy_1 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_2 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_3 = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls) -> "QuestSceneMultiPlayStartResponseData":
        ret = cls(b"\x00" * 3, 0)
        ret.dummy_1 = 0
        ret.dummy_2 = 0
        ret.dummy_3 = 0
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.dummy_1) \
        + encode_byte(self.dummy_2) \
        + encode_byte(self.dummy_3)

class QuestSceneMultiPlayEndResponseData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.dummy_1 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_2 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_3 = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls) -> "QuestSceneMultiPlayEndResponseData":
        ret = cls(b"\x00" * 3, 0)
        ret.dummy_1 = 0
        ret.dummy_2 = 0
        ret.dummy_3 = 0
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.dummy_1) \
        + encode_byte(self.dummy_2) \
        + encode_byte(self.dummy_3)

class QuestScenePlayEndBaseGetData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.get_hero_log_exp = decode_int(data, off)
        off += INT_OFF

        self.get_col = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndBaseGetData":
        ret = cls(b"\x00" * 99, 0)
        ret.get_hero_log_exp = data['GetHeroLogExp']
        ret.get_col = data['GetCol']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.get_hero_log_exp) \
        + encode_int(self.get_col)

class QuestScenePlayEndDiscoveryEnemyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self.destroy_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndDiscoveryEnemyData":
        ret = cls(b"\x00" * 99, 0)
        ret.enemy_kind_id = data['EnemyKindId']
        ret.destroy_num = data['DestroyNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.enemy_kind_id) \
        + encode_short(self.destroy_num)

class QuestScenePlayEndGetPlayerTraceData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_quest_scene_player_trace_id, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndGetPlayerTraceData":
        ret = cls(b"\x00" * 99, 0)
        ret.user_quest_scene_player_trace_id = data['UserQuestScenePlayerTraceId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_quest_scene_player_trace_id)

class QuestScenePlayEndGetRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_rare_drop_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndGetRareDropData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_rare_drop_id = data['QuestRareDropId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_rare_drop_id)

class QuestScenePlayEndGetSpecialRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_special_rare_drop_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndGetSpecialRareDropData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_special_rare_drop_id = data['QuestSpecialRareDropId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_special_rare_drop_id)

class QuestScenePlayEndGetUnanalyzedLogTmpRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unanalyzed_log_grade_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndGetUnanalyzedLogTmpRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.unanalyzed_log_grade_id = data['UnanalyzedLogGradeId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unanalyzed_log_grade_id)

class QuestScenePlayEndScoreData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.clear_time = decode_int(data, off)
        off += INT_OFF

        self.combo_num = decode_int(data, off)
        off += INT_OFF

        self.total_damage, new_off = decode_str(data, off)
        off += new_off

        self.concurrent_destroying_num = decode_short(data, off)
        off += SHORT_OFF

        self.reaching_skill_level = decode_short(data, off)
        off += SHORT_OFF

        self.ko_chara_num = decode_byte(data, off)
        off += BYTE_OFF

        self.acceleration_invocation_num = decode_short(data, off)
        off += SHORT_OFF

        self.boss_destroying_num = decode_short(data, off)
        off += SHORT_OFF

        self.synchro_skill_used_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.used_friend_skill_id = decode_int(data, off)
        off += INT_OFF

        self.friend_skill_used_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.continue_cnt = decode_short(data, off)
        off += SHORT_OFF

        self.total_loss_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndScoreData":
        ret = cls(b"\x00" * 99, 0)
        ret.clear_time = data['ClearTime']
        ret.combo_num = data['ComboNum']
        ret.total_damage = data['TotalDamage']
        ret.concurrent_destroying_num = data['ConcurrentDestroyingNum']
        ret.reaching_skill_level = data['ReachingSkillLevel']
        ret.ko_chara_num = data['KoCharaNum']
        ret.acceleration_invocation_num = data['AccelerationInvocationNum']
        ret.boss_destroying_num = data['BossDestroyingNum']
        ret.synchro_skill_used_flag = data['SynchroSkillUsedFlag']
        ret.used_friend_skill_id = data['UsedFriendSkillId']
        ret.friend_skill_used_flag = data['FriendSkillUsedFlag']
        ret.continue_cnt = data['ContinueCnt']
        ret.total_loss_num = data['TotalLossNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.clear_time) \
        + encode_int(self.combo_num) \
        + encode_str(self.total_damage) \
        + encode_short(self.concurrent_destroying_num) \
        + encode_short(self.reaching_skill_level) \
        + encode_byte(self.ko_chara_num) \
        + encode_short(self.acceleration_invocation_num) \
        + encode_short(self.boss_destroying_num) \
        + encode_byte(self.synchro_skill_used_flag) \
        + encode_int(self.used_friend_skill_id) \
        + encode_byte(self.friend_skill_used_flag) \
        + encode_short(self.continue_cnt) \
        + encode_short(self.total_loss_num)

class QuestScenePlayEndMissionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.mission_id = decode_int(data, off)
        off += INT_OFF

        self.clear_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.mission_difficulty_id = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndMissionData":
        ret = cls(b"\x00" * 99, 0)
        ret.mission_id = data['MissionId']
        ret.clear_flag = data['ClearFlag']
        ret.mission_difficulty_id = data['MissionDifficultyId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.mission_id) \
        + encode_byte(self.clear_flag) \
        + encode_short(self.mission_difficulty_id)

class QuestScenePlayEndDestroyBossData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.boss_type = decode_byte(data, off)
        off += BYTE_OFF

        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self.destroy_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndDestroyBossData":
        ret = cls(b"\x00" * 99, 0)
        ret.boss_type = data['BossType']
        ret.enemy_kind_id = data['EnemyKindId']
        ret.destroy_num = data['DestroyNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.boss_type) \
        + encode_int(self.enemy_kind_id) \
        + encode_short(self.destroy_num)

class QuestScenePlayEndGetEventItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.event_item_id = decode_int(data, off)
        off += INT_OFF

        self.get_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndGetEventItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.event_item_id = data['EventItemId']
        ret.get_num = data['GetNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.event_item_id) \
        + encode_short(self.get_num)

class QuestTreasureHuntPlayEndResponseData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.get_event_point = decode_int(data, off)
        off += INT_OFF

        self.total_event_point = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, get_pt: int = 0, total_pt: int = 0) -> "QuestTreasureHuntPlayEndResponseData":
        ret = cls(b"\x00" * 8, 0)
        ret.get_event_point = get_pt
        ret.total_event_point = total_pt
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.get_event_point) \
        + encode_int(self.total_event_point)

class QuestTrialTowerPlayEndUpdatedNotificationData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.store_best_score_clear_time_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.store_best_score_combo_num_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.store_best_score_total_damage_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.store_best_score_concurrent_destroying_num_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.store_reaching_trial_tower_rank = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, shop_best_time: bool = False, shop_best_combo: bool = False, shop_best_damage: bool = False, shop_best_concurrent: bool = False, shop_tower_rank: int = 0) -> "QuestTrialTowerPlayEndUpdatedNotificationData":
        ret = cls(b"\x00" * 8, 0)
        ret.store_best_score_clear_time_flag = shop_best_time
        ret.store_best_score_combo_num_flag = shop_best_combo
        ret.store_best_score_total_damage_flag = shop_best_damage
        ret.store_best_score_concurrent_destroying_num_flag = shop_best_concurrent
        ret.store_reaching_trial_tower_rank = shop_tower_rank
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.store_best_score_clear_time_flag) \
        + encode_byte(self.store_best_score_combo_num_flag) \
        + encode_byte(self.store_best_score_total_damage_flag) \
        + encode_byte(self.store_best_score_concurrent_destroying_num_flag) \
        + encode_int(self.store_reaching_trial_tower_rank)

class CommonRewardUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.common_reward_type = decode_short(data, off)
        off += SHORT_OFF

        self.user_common_reward_id, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CommonRewardUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.common_reward_type = data['CommonRewardType']
        ret.user_common_reward_id = data['UserCommonRewardId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.common_reward_type) \
        + encode_str(self.user_common_reward_id)

class QuestScenePlayEndResponseData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.rarity_up_occurrence_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.adventure_ex_area_occurrences_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.ex_bonus_data_list: List[QuestScenePlayEndExBonusData] = []
        self.ex_bonus_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndExBonusData)
        off += new_off

        self.play_end_player_trace_reward_data_list: List[QuestScenePlayEndPlayerTraceRewardData] = []
        self.play_end_player_trace_reward_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndPlayerTraceRewardData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, rarity_up_flag: bool = False, adventure_ex_area_flg: bool = False, ex_tables: List = []) -> "QuestScenePlayEndResponseData":
        ret = cls(b"\x00" * 99, 0)
        ret.rarity_up_occurrence_flag = rarity_up_flag
        ret.adventure_ex_area_occurrences_flag = adventure_ex_area_flg
        for x in ex_tables:
            ret.ex_bonus_data_list.append(QuestScenePlayEndExBonusData.from_args(x['table'], x['ach_status']))
        ret.play_end_player_trace_reward_data_list = []
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.rarity_up_occurrence_flag) \
        + encode_byte(self.adventure_ex_area_occurrences_flag) \
        + encode_arr_cls(self.ex_bonus_data_list) \
        + encode_arr_cls(self.play_end_player_trace_reward_data_list)

class QuestScenePlayEndExBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_bonus_table_id = decode_int(data, off)
        off += INT_OFF

        self.achievement_status = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, table_id: int, ach_status: int) -> "QuestScenePlayEndExBonusData":
        ret = cls(b"\x00" * 5, 0)
        ret.ex_bonus_table_id = table_id
        ret.achievement_status = ach_status
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_bonus_table_id) \
        + encode_byte(self.achievement_status)

class QuestScenePlayEndPlayerTraceRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.common_reward_data: List[CommonRewardData]
        self.common_reward_data, new_off = decode_arr_cls(data, off, CommonRewardData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, reward_data: Dict) -> "QuestScenePlayEndPlayerTraceRewardData":
        ret = cls(b"\x00" * 4, 0)
        ret.common_reward_data.append(CommonRewardData.from_args(reward_data['CommonRewardType'], reward_data['CommonRewardId'], reward_data['CommonRewardNum']))
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_arr_cls(self.common_reward_data)

class QuestScenePlayEndRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.play_result_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.base_get_data: List[QuestScenePlayEndBaseGetData] = []
        self.base_get_data, new_off = decode_arr_cls(data, off, QuestScenePlayEndBaseGetData)
        off += new_off

        self.get_player_trace_data_list: List[QuestScenePlayEndGetPlayerTraceData] = []
        self.get_player_trace_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndGetPlayerTraceData)
        off += new_off

        self.get_rare_drop_data_list: List[QuestScenePlayEndGetRareDropData] = []
        self.get_rare_drop_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndGetRareDropData)
        off += new_off

        self.get_special_rare_drop_data_list: List[QuestScenePlayEndGetSpecialRareDropData] = []
        self.get_special_rare_drop_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndGetSpecialRareDropData)
        off += new_off

        self.get_unanalyzed_log_tmp_reward_data_list: List[QuestScenePlayEndGetUnanalyzedLogTmpRewardData] = []
        self.get_unanalyzed_log_tmp_reward_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndGetUnanalyzedLogTmpRewardData)
        off += new_off

        self.get_event_item_data_list: List[QuestScenePlayEndGetEventItemData] = []
        self.get_event_item_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndGetEventItemData)
        off += new_off

        self.discovery_enemy_data_list: List[QuestScenePlayEndDiscoveryEnemyData] = []
        self.discovery_enemy_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndDiscoveryEnemyData)
        off += new_off

        self.destroy_boss_data_list: List[QuestScenePlayEndDestroyBossData] = []
        self.destroy_boss_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndDestroyBossData)
        off += new_off

        self.mission_data_list: List[QuestScenePlayEndMissionData] = []
        self.mission_data_list, new_off = decode_arr_cls(data, off, QuestScenePlayEndMissionData)
        off += new_off

        self.score_data: List[QuestScenePlayEndScoreData] = []
        self.score_data, new_off = decode_arr_cls(data, off, QuestScenePlayEndScoreData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestScenePlayEndRequestData":
        ret = cls(b"\x00" * 99, 0)
        ret.play_result_flag = data['PlayResultFlag']
        ret.base_get_data = []
        ret.get_player_trace_data_list = []
        ret.get_rare_drop_data_list = []
        ret.get_special_rare_drop_data_list = []
        ret.get_unanalyzed_log_tmp_reward_data_list = []
        ret.get_event_item_data_list = []
        ret.discovery_enemy_data_list = []
        ret.destroy_boss_data_list = []
        ret.mission_data_list = []
        ret.score_data = []
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.play_result_flag) \
        + encode_arr_cls(self.base_get_data) \
        + encode_arr_cls(self.get_player_trace_data_list) \
        + encode_arr_cls(self.get_rare_drop_data_list) \
        + encode_arr_cls(self.get_special_rare_drop_data_list) \
        + encode_arr_cls(self.get_unanalyzed_log_tmp_reward_data_list) \
        + encode_arr_cls(self.get_event_item_data_list) \
        + encode_arr_cls(self.discovery_enemy_data_list) \
        + encode_arr_cls(self.destroy_boss_data_list) \
        + encode_arr_cls(self.mission_data_list) \
        + encode_arr_cls(self.score_data)

class QuestSceneMultiPlayEndRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.dummy_1 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_2 = decode_byte(data, off)
        off += BYTE_OFF

        self.dummy_3 = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls) -> "QuestSceneMultiPlayEndRequestData":
        ret = cls(b"\x00" * 3, 0)
        ret.dummy_1 = 0
        ret.dummy_2 = 0
        ret.dummy_3 = 0
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.dummy_1) \
        + encode_byte(self.dummy_2) \
        + encode_byte(self.dummy_3)

class ChatSideStoryUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chat_side_story_id = decode_int(data, off)
        off += INT_OFF

        self.played_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ChatSideStoryUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.chat_side_story_id = data['ChatSideStoryId']
        ret.played_flag = data['PlayedFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.chat_side_story_id) \
        + encode_byte(self.played_flag)

class PartyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_party_id, new_off = decode_str(data, off)
        off += new_off

        self.team_no = decode_byte(data, off)
        off += BYTE_OFF

        self.party_team_data_list: List[PartyTeamData] = []
        self.party_team_data_list, new_off = decode_arr_cls(data, off, PartyTeamData)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, user_party_id: int, team_num: int, member1: Dict, member2: Dict, member3: Dict) -> "PartyData":
        ret = cls(b"\x00" * 9, 0)
        ret.user_party_id = user_party_id
        ret.team_no = team_num
        ret.party_team_data_list = [
            PartyTeamData.from_args(f"{user_party_id}-{team_num}-1", 1, member1),
            PartyTeamData.from_args(f"{user_party_id}-{team_num}-2", 2, member2),
            PartyTeamData.from_args(f"{user_party_id}-{team_num}-3", 3, member3),
        ]
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_party_id) \
        + encode_byte(self.team_no) \
        + encode_arr_cls(self.party_team_data_list)

class SupportLogPartyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.party_no = decode_byte(data, off)
        off += BYTE_OFF

        self.arrangement_num_1_user_support_log_id, new_off = decode_str(data, off)
        off += new_off

        self.arrangement_num_2_user_support_log_id, new_off = decode_str(data, off)
        off += new_off

        self.arrangement_num_3_user_support_log_id, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SupportLogPartyData":
        ret = cls(b"\x00" * 99, 0)
        ret.party_no = data['PartyNo']
        ret.arrangement_num_1_user_support_log_id = data['ArrangementNum1UserSupportLogId']
        ret.arrangement_num_2_user_support_log_id = data['ArrangementNum2UserSupportLogId']
        ret.arrangement_num_3_user_support_log_id = data['ArrangementNum3UserSupportLogId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.party_no) \
        + encode_str(self.arrangement_num_1_user_support_log_id) \
        + encode_str(self.arrangement_num_2_user_support_log_id) \
        + encode_str(self.arrangement_num_3_user_support_log_id)

class PlayStartRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        sz = 0
        user_party_id = decode_str(data, offset + sz)
        self.user_party_id = user_party_id[0]
        sz += user_party_id[1]

        appoint_leader_resource_card_code = decode_str(data, offset + sz)
        self.appoint_leader_resource_card_code = appoint_leader_resource_card_code[0]
        sz += appoint_leader_resource_card_code[1]

        use_profile_card_code = decode_str(data, offset + sz)
        self.use_profile_card_code = use_profile_card_code[0]
        sz += use_profile_card_code[1]

        self.quest_drop_boost_apply_flag = decode_byte(data, offset + sz)
        sz += BYTE_OFF

        self._sz = sz

class GetPlayerTraceData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        user_quest_scene_player_trace_id = decode_str(data, offset)
        self.user_quest_scene_player_trace_id = user_quest_scene_player_trace_id[0]
        self._sz = user_quest_scene_player_trace_id[1]

class BaseGetData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.get_hero_log_exp = decode_int(data, offset)
        offset += INT_OFF

        self.get_col = decode_int(data, offset)

        self._sz = INT_OFF + INT_OFF

class RareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.quest_rare_drop_id = decode_int(data, offset)

        self._sz = INT_OFF

class UnanalyzedLogTmpRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.unanalyzed_log_grade_id = decode_int(data, offset)

        self._sz = INT_OFF

class SpecialRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.quest_special_rare_drop_id = decode_int(data, offset)

        self._sz = INT_OFF

class EventItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.event_item_id = decode_int(data, offset)
        offset += INT_OFF
        self.get_num = decode_short(data, offset)

        self._sz = INT_OFF + SHORT_OFF

class DiscoveryEnemyData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.enemy_kind_id = decode_int(data, offset)
        offset += INT_OFF
        self.destroy_num = decode_short(data, offset)

        self._sz = INT_OFF + SHORT_OFF

class DestroyBossData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.boss_type = decode_byte(data, offset)
        offset += BYTE_OFF
        self.enemy_kind_id = decode_int(data, offset)
        offset += INT_OFF
        self.mission_difficulty_id = decode_short(data, offset)

        self._sz = INT_OFF + SHORT_OFF + BYTE_OFF

class MissionData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        self.mission_id = decode_int(data, offset)
        offset += INT_OFF
        self.clear_flag = decode_byte(data, offset)
        offset += BYTE_OFF
        self.destroy_num = decode_short(data, offset)

        self._sz = INT_OFF + SHORT_OFF + BYTE_OFF

class ScoreData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.clear_time = decode_int(data, offset + self._sz)
        self._sz += INT_OFF

        self.combo_num = decode_int(data, offset + self._sz)
        self._sz += INT_OFF

        total_damage = decode_str(data, offset + self._sz)
        self.total_damage = total_damage[0]
        self._sz += total_damage[1]

        self.concurrent_destroying_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        self.reaching_skill_level = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        self.ko_chara_num = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

        self.acceleration_invocation_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        self.boss_destroying_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        self.synchro_skill_used_flag = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

        self.used_friend_skill_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF

        self.friend_skill_used_flag = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

        self.continue_cnt = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        self.total_loss_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

class PlayEndRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        sz = 0
        self.play_result_flag = decode_byte(data, offset + sz)
        sz += BYTE_OFF

        self.base_get_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.base_get_data_list: List[BaseGetData] = []
        for _ in range(self.base_get_data_count):
            tmp = BaseGetData(data, offset + sz)
            sz += tmp.get_size()
            self.base_get_data_list.append(tmp)

        self.get_player_trace_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.get_player_trace_data: List[GetPlayerTraceData] = []
        for _ in range(self.get_player_trace_data_count):
            tmp = GetPlayerTraceData(data, offset + sz)
            sz += tmp.get_size()
            self.get_player_trace_data.append(tmp)

        self.get_rare_drop_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.get_rare_drop_data_list: List[RareDropData] = []
        for _ in range(self.get_rare_drop_data_count):
            tmp = RareDropData(data, offset + sz)
            sz += tmp.get_size()
            self.get_rare_drop_data_list.append(tmp)

        self.get_special_rare_drop_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.get_special_rare_drop_data_list: List[SpecialRareDropData] = []
        for _ in range(self.get_special_rare_drop_data_count):
            tmp = SpecialRareDropData(data, offset + sz)
            sz += tmp.get_size()
            self.get_special_rare_drop_data_list.append(tmp)

        self.get_unanalyzed_log_tmp_reward_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.get_unanalyzed_log_tmp_reward_data_list: List[UnanalyzedLogTmpRewardData] = []
        for _ in range(self.get_unanalyzed_log_tmp_reward_data_count):
            tmp = UnanalyzedLogTmpRewardData(data, offset + sz)
            sz += tmp.get_size()
            self.get_unanalyzed_log_tmp_reward_data_list.append(tmp)

        self.get_event_item_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.get_event_item_data_list: List[EventItemData] = []
        for _ in range(self.get_event_item_data_count):
            tmp = EventItemData(data, offset + sz)
            sz += tmp.get_size()
            self.get_event_item_data_list.append(tmp)

        self.discovery_enemy_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.discovery_enemy_data_list: List[DiscoveryEnemyData] = []
        for _ in range(self.discovery_enemy_data_count):
            tmp = DiscoveryEnemyData(data, offset + sz)
            sz += tmp.get_size()
            self.discovery_enemy_data_list.append(tmp)

        self.destroy_boss_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.destroy_boss_data_list: List[DestroyBossData] = []
        for _ in range(self.destroy_boss_data_count):
            tmp = DestroyBossData(data, offset + sz)
            sz += tmp.get_size()
            self.destroy_boss_data_list.append(tmp)

        self.mission_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.mission_data_list: List[MissionData] = []
        for _ in range(self.mission_data_count):
            tmp = MissionData(data, offset + sz)
            sz += tmp.get_size()
            self.mission_data_list.append(tmp)

        self.score_data_count = decode_int(data, offset + sz)
        sz += INT_OFF

        self.score_data_list: List[ScoreData] = []
        for _ in range(self.score_data_count):
            tmp = ScoreData(data, offset + sz)
            sz += tmp.get_size()
            self.score_data_list.append(tmp)

        self._sz = sz

class EntryUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        store_id = decode_str(data, offset + self._sz)
        self.store_id = store_id[0]
        self._sz += store_id[1]

        user_id = decode_str(data, offset + self._sz)
        self.user_id = user_id[0]
        self._sz += user_id[1]

        self.host_flag = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

class MultiPlayStartRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        room_id = decode_str(data, offset + self._sz)
        self.room_id = room_id[0]
        self._sz += room_id[1]

        self.matching_mode = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

        self.entry_user_data_count = decode_int(data, offset + self._sz)
        self._sz += INT_OFF

        self.entry_user_data_list: List[EntryUserData] = []
        for _ in range(self.entry_user_data_count):
            tmp = EntryUserData(data, offset + self._sz)
            self._sz += tmp.get_size()
            self.entry_user_data_list.append(tmp)

class MultiPlayEndRequestData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.dummy_1 = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF
        self.dummy_2 = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF
        self.dummy_3 = decode_byte(data, offset + self._sz)
        self._sz += BYTE_OFF

class SalesResourceData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.common_reward_type = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF
        self.common_reward_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.property1_property_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property1_value1 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property1_value2 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.property2_property_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property2_value1 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property2_value2 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.property3_property_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property3_value1 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property3_value2 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.property4_property_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property4_value1 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.property4_value2 = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
    
    @classmethod
    def from_args(cls, reward_type: int = 0, reward_id: int = 0) -> "SalesResourceData":
        ret = cls(b"\x00" * 54, 0)
        ret.common_reward_type = reward_type # short
        ret.common_reward_id = reward_id # int
        
        return ret

    def make(self) -> bytes:
        ret = b""
        ret += encode_short(self.common_reward_type)
        ret += encode_int(self.common_reward_id)
        
        ret += encode_int(self.property1_property_id)
        ret += encode_int(self.property1_value1)
        ret += encode_int(self.property1_value2)
        
        ret += encode_int(self.property2_property_id)
        ret += encode_int(self.property2_value1)
        ret += encode_int(self.property2_value2)
        
        ret += encode_int(self.property3_property_id)
        ret += encode_int(self.property3_value1)
        ret += encode_int(self.property3_value2)
        
        ret += encode_int(self.property4_property_id)
        ret += encode_int(self.property4_value1)
        ret += encode_int(self.property4_value2)

class ShopResourceSalesData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        user_shop_resource_id = decode_str(data, offset + self._sz)
        self.user_shop_resource_id = user_shop_resource_id[0]
        self._sz = user_shop_resource_id[1]
        
        discharge_user_id = decode_str(data, offset + self._sz)
        self.discharge_user_id = discharge_user_id[0]
        self._sz = discharge_user_id[1]
        
        self.remaining_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF
        self.purchase_num = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF
        
        sales_start_date = decode_str(data, offset + self._sz)
        self.sales_start_date = prs_dt(sales_start_date[0])
        self._sz = sales_start_date[1]
        
        sales_resource_data_list = decode_arr_cls(data, offset + self._sz, SalesResourceData)
        self.sales_resource_data_list: List[SalesResourceData] = sales_resource_data_list[0]
        self._sz += sales_resource_data_list[1]

    @classmethod
    def from_args(cls, resource_id: str = "0", discharge_id: str = "0", remaining: int = 0, purchased: int = 0) -> "ShopResourceSalesData":
        ret = cls(b"\x00" * 20, 0)
        ret.user_shop_resource_id = resource_id
        ret.discharge_user_id = discharge_id
        ret.remaining_num = remaining # short
        ret.purchase_num = purchased # short
        ret.sales_start_date = prs_dt()
    
    def make(self) -> bytes:
        ret = encode_str(self.user_shop_resource_id)
        ret += encode_str(self.discharge_user_id)
        ret += encode_short(self.remaining_num)
        ret += encode_short(self.purchase_num)
        ret += encode_date_str(self.sales_start_date)
        ret += encode_arr_cls(self.sales_resource_data_list)
        return ret

class YuiMedalShopUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.yui_medal_shop_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.purchase_num = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        last_purchase_date = decode_str(data, offset + self._sz)
        self.last_purchase_date = last_purchase_date[0]
        self._sz += last_purchase_date[1]
    
    @classmethod
    def from_args(cls, yui_medal_shop_id: int = 0, purchase_num: int = 0, last_purchase_date: datetime = datetime.fromtimestamp(0)) -> "YuiMedalShopUserData":
        ret = cls(b"\x00" * 20, 0)
        ret.yui_medal_shop_id = yui_medal_shop_id
        ret.purchase_num = purchase_num
        ret.last_purchase_date = last_purchase_date
        return ret
    
    def make(self) -> bytes:
        ret = encode_int(self.yui_medal_shop_id)
        ret += encode_int(self.purchase_num)
        ret += encode_date_str(self.last_purchase_date)
        return ret

class GashaMedalShopUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.gasha_medal_shop_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        
        self.purchase_num = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
    
    @classmethod
    def from_args(cls, gasha_medal_shop_id: int = 0, purchase_num: int = 0) -> "GashaMedalShopUserData":
        ret = cls(b"\x00" * 20, 0)
        ret.gasha_medal_shop_id = gasha_medal_shop_id
        ret.purchase_num = purchase_num
        return ret
    
    def make(self) -> bytes:
        ret = encode_int(self.gasha_medal_shop_id)
        ret += encode_int(self.purchase_num)
        return ret

class QuestHierarchyProgressDegreesRankingData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.rank = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.trial_tower_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF

        user_id = decode_str(data, offset + self._sz)
        self.user_id = user_id[0]
        self._sz += user_id[1]

        nick_name = decode_str(data, offset + self._sz)
        self.nick_name = nick_name[0]
        self._sz += nick_name[1]

        self.setting_title_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.favorite_hero_log_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.favorite_hero_log_awakening_stage = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF
        self.favorite_support_log_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.favorite_support_log_awakening_stage = decode_short(data, offset + self._sz)
        self._sz += SHORT_OFF

        clear_time = decode_str(data, offset + self._sz)
        self.clear_time = clear_time[0]
        self._sz += clear_time[1]
    
    @classmethod
    def from_args(cls) -> "QuestHierarchyProgressDegreesRankingData":
        ret = cls(b"\x00" * 36, 0)
        return ret
    
    def make(self) -> bytes:
        ret = encode_int(self.rank)
        ret += encode_int(self.trial_tower_id)
        ret += encode_str(self.user_id)
        ret += encode_str(self.nick_name)
        ret += encode_int(self.setting_title_id)
        ret += encode_int(self.favorite_hero_log_id)
        ret += encode_short(self.favorite_hero_log_awakening_stage)
        ret += encode_int(self.favorite_support_log_id)
        ret += encode_short(self.favorite_support_log_awakening_stage)
        ret += encode_str(self.clear_time)
        return ret

class PopularHeroLogRankingData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        self.rank = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.hero_log_id = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
        self.used_num = decode_int(data, offset + self._sz)
        self._sz += INT_OFF
    
    @classmethod
    def from_args(cls, ranking: int, hero_id: int, used_num: int) -> "PopularHeroLogRankingData":
        ret = cls(b"\x00" * 992, 0)
        ret.rank = ranking
        ret.hero_log_id = hero_id
        ret.used_num = used_num
        return ret
    
    def make(self) -> bytes:
        ret = encode_int(self.rank)
        ret += encode_int(self.hero_log_id)
        ret += encode_int(self.used_num)
        return ret

class DefragMatchBasicUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.seed_flag = decode_short(data, off)
        off += SHORT_OFF

        self.ad_confirm_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.total_league_point = decode_int(data, off)
        off += INT_OFF

        self.have_league_score = decode_short(data, off)
        off += SHORT_OFF

        self.class_num = decode_short(data, off)
        off += SHORT_OFF

        self.hall_of_fame_confirm_flag = decode_byte(data, off)
        off += BYTE_OFF
        self._sz = off

    @classmethod
    def from_args(cls, seed_flag: int = 0, ad_confirm_flag: int = 0, total_league_point: int = 0, league_score: int = 0, class_num: int = 1, hof_flag: int = 0) -> "DefragMatchBasicUserData":
        ret = cls(b"\x00" * 12, 0)
        ret.seed_flag = seed_flag
        ret.ad_confirm_flag = ad_confirm_flag
        ret.total_league_point = total_league_point
        ret.have_league_score = league_score
        ret.class_num = class_num
        ret.hall_of_fame_confirm_flag = hof_flag
    
    def make(self) -> bytes:
        ret = encode_short(self.seed_flag)
        ret += encode_byte(self.ad_confirm_flag)
        ret += encode_int(self.total_league_point)
        ret += encode_short(self.have_league_score)
        ret += encode_short(self.class_num)
        ret += encode_byte(self.hall_of_fame_confirm_flag)
        return ret

class DefragMatchRankingUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.league_point_rank = decode_int(data, off)
        off += INT_OFF

        self.league_score_rank = decode_int(data, off)
        off += INT_OFF

        self.nick_name, new_off = decode_str(data, off)
        off += new_off

        self.setting_title_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.favorite_support_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_support_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.total_league_point = decode_int(data, off)
        off += INT_OFF

        self.have_league_score = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, profile: Dict) -> "DefragMatchRankingUserData":
        ret = cls(b"\x00" * 34, 0)
        ret.league_point_rank = 0
        ret.league_score_rank = 0
        ret.nick_name = profile['nick_name']
        ret.setting_title_id = profile['setting_title_id']
        ret.favorite_hero_log_id = profile['fav_hero']
        ret.favorite_hero_log_awakening_stage = 0
        ret.favorite_support_log_id = 0
        ret.favorite_support_log_awakening_stage = 0
        ret.total_league_point = 0
        ret.have_league_score = 0
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.league_point_rank) \
        + encode_int(self.league_score_rank) \
        + encode_str(self.nick_name) \
        + encode_int(self.setting_title_id) \
        + encode_int(self.favorite_hero_log_id) \
        + encode_short(self.favorite_hero_log_awakening_stage) \
        + encode_int(self.favorite_support_log_id) \
        + encode_short(self.favorite_support_log_awakening_stage) \
        + encode_int(self.total_league_point) \
        + encode_short(self.have_league_score)

class DefragMatchLeaguePointRankingData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.rank = decode_int(data, off)
        off += INT_OFF

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.nick_name, new_off = decode_str(data, off)
        off += new_off

        self.setting_title_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.favorite_support_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_support_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.class_num = decode_short(data, off)
        off += SHORT_OFF

        self.total_league_point = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchLeaguePointRankingData":
        ret = cls(b"\x00" * 42, 0)
        ret.rank = data['Rank']
        ret.user_id = data['UserId']
        ret.store_id = data['StoreId']
        ret.store_name = data['StoreName']
        ret.nick_name = data['NickName']
        ret.setting_title_id = data['SettingTitleId']
        ret.favorite_hero_log_id = data['FavoriteHeroLogId']
        ret.favorite_hero_log_awakening_stage = data['FavoriteHeroLogAwakeningStage']
        ret.favorite_support_log_id = data['FavoriteSupportLogId']
        ret.favorite_support_log_awakening_stage = data['FavoriteSupportLogAwakeningStage']
        ret.class_num = data['ClassNum']
        ret.total_league_point = data['TotalLeaguePoint']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.rank) \
        + encode_str(self.user_id) \
        + encode_str(self.store_id) \
        + encode_str(self.store_name) \
        + encode_str(self.nick_name) \
        + encode_int(self.setting_title_id) \
        + encode_int(self.favorite_hero_log_id) \
        + encode_short(self.favorite_hero_log_awakening_stage) \
        + encode_int(self.favorite_support_log_id) \
        + encode_short(self.favorite_support_log_awakening_stage) \
        + encode_short(self.class_num) \
        + encode_int(self.total_league_point)

class DefragMatchLeagueScoreRankingList(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.rank = decode_byte(data, off)
        off += BYTE_OFF

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.nick_name, new_off = decode_str(data, off)
        off += new_off

        self.setting_title_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_hero_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.favorite_support_log_id = decode_int(data, off)
        off += INT_OFF

        self.favorite_support_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.class_num = decode_short(data, off)
        off += SHORT_OFF

        self.have_league_score = decode_short(data, off)
        off += SHORT_OFF
    
    @classmethod
    def from_args(cls) -> "DefragMatchLeagueScoreRankingList":
        return cls(b"\x00" * 40, 0)
    
    def make(self) -> bytes:
        ret = encode_int(self.rank)
        ret += encode_str(self.user_id)
        ret += encode_str(self.store_id)
        ret += encode_str(self.store_name)
        ret += encode_str(self.nick_name)

        ret += encode_int(self.setting_title_id)
        ret += encode_int(self.favorite_hero_log_id)
        ret += encode_short(self.favorite_hero_log_awakening_stage)
        ret += encode_int(self.favorite_support_log_id)
        ret += encode_short(self.favorite_support_log_awakening_stage)
        ret += encode_short(self.class_num)
        ret += encode_short(self.have_league_score)
        return ret

class AppVersionData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.version_app_id = decode_int(data, off)
        off += INT_OFF

        self.applying_start_date, new_off = decode_date_str(data, off)
        off += new_off
    
    @classmethod
    def from_args(cls, app_ver: int, start_date: datetime) -> BaseHelper:
        ret = cls(b"\x00" * 8, 0)
        ret.version_app_id = app_ver
        ret.applying_start_date = start_date
        return ret
    
    def make(self) -> bytes:
        ret = encode_int(self.version_app_id)
        ret += encode_date_str(self.applying_start_date)
        return ret

class MatchingErrorData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.param_1, new_off = decode_str(data, off)
        off += new_off

        self.param_2, new_off = decode_str(data, off)
        off += new_off

        self.param_3, new_off = decode_str(data, off)
        off += new_off

        self.param_4, new_off = decode_str(data, off)
        off += new_off

        self.param_5, new_off = decode_str(data, off)
        off += new_off

        self.param_6, new_off = decode_str(data, off)
        off += new_off

        self.param_7, new_off = decode_str(data, off)
        off += new_off

        self.param_8, new_off = decode_str(data, off)
        off += new_off

        self.param_9, new_off = decode_str(data, off)
        off += new_off

        self.param_10, new_off = decode_str(data, off)
        off += new_off

        self.error_occurred_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset
    
    def __str__(self) -> str:
        s = f"User: {self.user_id} || "
        s += f"Params: {self.param_1} {self.param_2} {self.param_3} {self.param_4} {self.param_5} {self.param_6} {self.param_7} {self.param_8} {self.param_9} {self.param_10} || "
        s += f"Date: {self.error_occurred_date}"
        return s

class ReadProfileCard(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.profile_card_code, new_off = decode_str(data, off) # ID of the QR code
        off += new_off
        self.nick_name = decode_str(data, off)
        off += new_off
        
        self.rank_num = decode_short(data, off) #short
        off += SHORT_OFF
        self.setting_title_id = decode_int(data, off) #int
        off += INT_OFF
        self.skill_id = decode_short(data, off) #short
        off += SHORT_OFF
        self.hero_log_hero_log_id = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_log_level = decode_short(data, off) #short
        off += SHORT_OFF
        self.hero_log_awakening_stage = decode_short(data, off) #short
        off += SHORT_OFF

        self.hero_log_property1_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property1_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property1_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property2_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property2_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property2_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property3_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property3_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property3_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property4_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property4_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.hero_log_property4_value2 = decode_int(data, off) #int
        off += INT_OFF

        self.main_weapon_equipment_id = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_enhancement_value = decode_short(data, off) #short
        off += SHORT_OFF
        self.main_weapon_awakening_stage = decode_short(data, off) #short
        off += SHORT_OFF

        self.main_weapon_property1_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property1_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property1_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property2_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property2_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property2_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property3_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property3_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property3_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property4_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property4_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.main_weapon_property4_value2 = decode_int(data, off) #int
        off += INT_OFF

        self.sub_equipment_equipment_id = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_enhancement_value = decode_short(data, off) #short
        off += SHORT_OFF
        self.sub_equipment_awakening_stage = decode_short(data, off) #short
        off += SHORT_OFF

        self.sub_equipment_property1_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property1_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property1_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property2_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property2_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property2_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property3_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property3_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property3_value2 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property4_property_id = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property4_value1 = decode_int(data, off) #int
        off += INT_OFF
        self.sub_equipment_property4_value2 = decode_int(data, off) #int
        off += INT_OFF

        self.holographic_flag = decode_byte(data, off) #byte
        off += BYTE_OFF
        self._sz = off - offset
    
    @classmethod
    def from_args(cls, code: str, player_name: str) -> "ReadProfileCard":
        resp = cls(b"\x00" * 44, 0)
        resp.profile_card_code = code # ID of the QR code
        resp.nick_name = player_name
        resp.rank_num = 1 #short
        resp.setting_title_id = 20005 #int
        resp.skill_id = 0 #short
        resp.hero_log_hero_log_id = 118000230 #int
        resp.hero_log_log_level = 1 #short
        resp.hero_log_awakening_stage = 1 #short

        resp.hero_log_property1_property_id = 0 #int
        resp.hero_log_property1_value1 = 0 #int
        resp.hero_log_property1_value2 = 0 #int
        resp.hero_log_property2_property_id = 0 #int
        resp.hero_log_property2_value1 = 0 #int
        resp.hero_log_property2_value2 = 0 #int
        resp.hero_log_property3_property_id = 0 #int
        resp.hero_log_property3_value1 = 0 #int
        resp.hero_log_property3_value2 = 0 #int
        resp.hero_log_property4_property_id = 0 #int
        resp.hero_log_property4_value1 = 0 #int
        resp.hero_log_property4_value2 = 0 #int

        resp.main_weapon_equipment_id = 0 #int
        resp.main_weapon_enhancement_value = 0 #short
        resp.main_weapon_awakening_stage = 0 #short

        resp.main_weapon_property1_property_id = 0 #int
        resp.main_weapon_property1_value1 = 0 #int
        resp.main_weapon_property1_value2 = 0 #int
        resp.main_weapon_property2_property_id = 0 #int
        resp.main_weapon_property2_value1 = 0 #int
        resp.main_weapon_property2_value2 = 0 #int
        resp.main_weapon_property3_property_id = 0 #int
        resp.main_weapon_property3_value1 = 0 #int
        resp.main_weapon_property3_value2 = 0 #int
        resp.main_weapon_property4_property_id = 0 #int
        resp.main_weapon_property4_value1 = 0 #int
        resp.main_weapon_property4_value2 = 0 #int

        resp.sub_equipment_equipment_id = 0 #int
        resp.sub_equipment_enhancement_value = 0 #short
        resp.sub_equipment_awakening_stage = 0 #short

        resp.sub_equipment_property1_property_id = 0 #int
        resp.sub_equipment_property1_value1 = 0 #int
        resp.sub_equipment_property1_value2 = 0 #int
        resp.sub_equipment_property2_property_id = 0 #int
        resp.sub_equipment_property2_value1 = 0 #int
        resp.sub_equipment_property2_value2 = 0 #int
        resp.sub_equipment_property3_property_id = 0 #int
        resp.sub_equipment_property3_value1 = 0 #int
        resp.sub_equipment_property3_value2 = 0 #int
        resp.sub_equipment_property4_property_id = 0 #int
        resp.sub_equipment_property4_value1 = 0 #int
        resp.sub_equipment_property4_value2 = 0 #int

        resp.holographic_flag = 0 #byte
        return resp

class HeroLogUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.user_hero_log_id, new_off = decode_str(data, off)
        off += new_off
        self.hero_log_id = decode_int(data, off)
        off += INT_OFF
        self.log_level = decode_short(data, off)
        off += SHORT_OFF
        self.max_log_level_extended_num = decode_short(data, off)
        off += SHORT_OFF
        self.log_exp = decode_int(data, off)
        off += INT_OFF
        self.possible_awakening_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.awakening_stage = decode_short(data, off)
        off += SHORT_OFF
        self.awakening_exp = decode_int(data, off)
        off += INT_OFF
        self.skill_slot_correction_value = decode_byte(data, off)
        off += BYTE_OFF
        self.last_set_skill_slot1_skill_id = decode_short(data, off)
        off += SHORT_OFF
        self.last_set_skill_slot2_skill_id = decode_short(data, off)
        off += SHORT_OFF
        self.last_set_skill_slot3_skill_id = decode_short(data, off)
        off += SHORT_OFF
        self.last_set_skill_slot4_skill_id = decode_short(data, off)
        off += SHORT_OFF
        self.last_set_skill_slot5_skill_id = decode_short(data, off)
        off += SHORT_OFF
        self.property1_property_id = decode_int(data, off)
        off += INT_OFF
        self.property1_value1 = decode_int(data, off)
        off += INT_OFF
        self.property1_value2 = decode_int(data, off)
        off += INT_OFF
        self.property2_property_id = decode_int(data, off)
        off += INT_OFF
        self.property2_value1 = decode_int(data, off)
        off += INT_OFF
        self.property2_value2 = decode_int(data, off)
        off += INT_OFF
        self.property3_property_id = decode_int(data, off)
        off += INT_OFF
        self.property3_value1 = decode_int(data, off)
        off += INT_OFF
        self.property3_value2 = decode_int(data, off)
        off += INT_OFF
        self.property4_property_id = decode_int(data, off)
        off += INT_OFF
        self.property4_value1 = decode_int(data, off)
        off += INT_OFF
        self.property4_value2 = decode_int(data, off)
        off += INT_OFF
        self.converted_card_num = decode_short(data, off)
        off += SHORT_OFF
        self.shop_purchase_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.protect_flag = decode_byte(data, off)
        off += BYTE_OFF

        get_date, new_off = decode_str(data, off)
        off += new_off
        self.get_date = prs_dt(get_date)
        self.sz = off - offset
    
    @classmethod
    def from_args(cls, hero_data: Dict) -> "HeroLogUserData":
        ret = cls(b"\x00" * 90, 0)
        # Seems user_hero_log_id is a globally unique identifier, while hero_log_id identifies the hero
        ret.user_hero_log_id = f"{hero_data['id']}"
        ret.hero_log_id = hero_data['hero_log_id']

        ret.log_level = hero_data['log_level']
        ret.max_log_level_extended_num = hero_data['max_level_extend_num']
        ret.log_exp = hero_data['log_exp']
        
        ret.possible_awakening_flag = hero_data['is_awakenable']
        ret.awakening_stage = hero_data['awakening_stage']
        ret.awakening_exp = hero_data['awakening_exp']

        ret.skill_slot_correction_value = 0 # Allows unlocking skill slot 4 and 5 early
        ret.last_set_skill_slot1_skill_id = hero_data['skill_slot1_skill_id']
        ret.last_set_skill_slot2_skill_id = hero_data['skill_slot2_skill_id']
        ret.last_set_skill_slot3_skill_id = hero_data['skill_slot3_skill_id']
        ret.last_set_skill_slot4_skill_id = hero_data['skill_slot4_skill_id']
        ret.last_set_skill_slot5_skill_id = hero_data['skill_slot5_skill_id']

        ret.property1_property_id = hero_data['property1_property_id']
        ret.property1_value1 = hero_data['property1_value1']
        ret.property1_value2 = hero_data['property1_value2']
        ret.property2_property_id = hero_data['property2_property_id']
        ret.property2_value1 = hero_data['property2_value1']
        ret.property2_value2 = hero_data['property2_value2']
        ret.property3_property_id = hero_data['property2_property_id']
        ret.property3_value1 = hero_data['property3_value1']
        ret.property3_value2 = hero_data['property3_value2']
        ret.property4_property_id = hero_data['property2_property_id']
        ret.property4_value1 = hero_data['property4_value1']
        ret.property4_value2 = hero_data['property4_value2']

        ret.converted_card_num = hero_data['converted_card_num']
        ret.shop_purchase_flag = hero_data['is_shop_purchase']
        ret.protect_flag = hero_data['is_protect']
        ret.get_date = hero_data['get_date']
        return ret
    
    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_hero_log_id) \
        + encode_int(self.hero_log_id) \
        + encode_short(self.log_level) \
        + encode_short(self.max_log_level_extended_num) \
        + encode_int(self.log_exp) \
        + encode_byte(self.possible_awakening_flag) \
        + encode_short(self.awakening_stage) \
        + encode_int(self.awakening_exp) \
        + encode_byte(self.skill_slot_correction_value) \
        + encode_short(self.last_set_skill_slot1_skill_id) \
        + encode_short(self.last_set_skill_slot2_skill_id) \
        + encode_short(self.last_set_skill_slot3_skill_id) \
        + encode_short(self.last_set_skill_slot4_skill_id) \
        + encode_short(self.last_set_skill_slot5_skill_id) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2) \
        + encode_short(self.converted_card_num) \
        + encode_byte(self.shop_purchase_flag) \
        + encode_byte(self.protect_flag) \
        + encode_date_str(self.get_date) 

class YuiMedalBonusUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.elapsed_days = decode_int(data, off)
        off += INT_OFF
        self.loop_num = decode_int(data, off)
        off += INT_OFF
        
        last_check_date, new_off = decode_str(data, off)
        off += new_off
        self.last_check_date = prs_dt(last_check_date)
        
        last_get_date, new_off = decode_str(data, off)
        off += new_off
        self.last_get_date = prs_dt(last_get_date)
        
        self._sz = off - offset
    
    @classmethod
    def from_args(cls, elapsed_days: int = 0, loop_num: int = 0) -> BaseHelper:
        ret = cls(b"\x00" * 996, 0)
        ret.elapsed_days = elapsed_days
        ret.loop_num = loop_num
        ret.last_check_date = datetime.fromtimestamp(0)
        ret.last_get_date = datetime.fromtimestamp(0)
        return ret
    
    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.elapsed_days) \
        + encode_int(self.loop_num) \
        + encode_date_str(self.last_check_date) \
        + encode_date_str(self.last_get_date)

class UserBasicData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.user_type = decode_short(data, off)
        off += SHORT_OFF
        
        self.nick_name, new_off = decode_str(data, off)
        off += new_off
        
        self.rank_num = decode_short(data, off)
        off += SHORT_OFF
        
        self.rank_exp = decode_int(data, off)
        off += INT_OFF
        
        self.own_col = decode_int(data, off)
        off += INT_OFF
        
        self.own_vp = decode_int(data, off)
        off += INT_OFF
        
        self.own_yui_medal = decode_int(data, off)
        off += INT_OFF
        
        self.setting_title_id = decode_int(data, off)
        off += INT_OFF
        
        self.favorite_user_hero_log_id, new_off = decode_str(data, off)
        off += new_off
        
        self.favorite_user_support_log_id, new_off = decode_str(data, off)
        off += new_off
        
        self.my_store_id, new_off = decode_str(data, off)
        off += new_off
        
        self.my_store_name, new_off = decode_str(data, off)
        off += new_off
        
        user_reg_date, new_off = decode_str(data, off)
        self.user_reg_date = prs_dt(user_reg_date)
        off += new_off
        
        self._sz = off - offset
    
    @classmethod
    def from_args(cls, profile_data: Dict, shop_name: str = "ARTEMiS") -> "UserBasicData":
        ret = cls(b"\0" * 52, 0)
        ret.user_type = profile_data['user_type']
        ret.nick_name = profile_data['nick_name']
        ret.rank_num = profile_data['rank_num']
        ret.rank_exp = profile_data['rank_exp']
        ret.own_col = profile_data['own_col']
        ret.own_vp = profile_data['own_vp']
        ret.own_yui_medal = profile_data['own_yui_medal']
        ret.setting_title_id = profile_data['setting_title_id']
        ret.favorite_user_hero_log_id = profile_data['fav_hero']
        ret.favorite_user_support_log_id = "" # TODO: Supports
        ret.my_store_id = "JPN0" + f"{profile_data['my_shop']:04X}" if profile_data["my_shop"] else "0"
        ret.my_store_name = shop_name
        ret.user_reg_date = profile_data['when_register'] if profile_data['when_register'] else prs_dt("20230101120000")
        return ret
    
    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.user_type) \
        + encode_str(self.nick_name) \
        + encode_short(self.rank_num) \
        + encode_int(self.rank_exp) \
        + encode_int(self.own_col) \
        + encode_int(self.own_vp) \
        + encode_int(self.own_yui_medal) \
        + encode_int(self.setting_title_id) \
        + encode_str(self.favorite_user_hero_log_id) \
        + encode_str(self.favorite_user_support_log_id) \
        + encode_str(self.my_store_id) \
        + encode_str(self.my_store_name) \
        + encode_date_str(self.user_reg_date) \

class VpGashaTicketData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.remaining_own_vp_gasha_ticket = decode_int(data, off)
        off += INT_OFF

        self.expire_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset
    
    @classmethod
    def from_args(cls, ticket_remain: int, exp_date: datetime) -> "VpGashaTicketData":
        ret = cls(b"\x00" * 8, 0)
        ret.remaining_own_vp_gasha_ticket = ticket_remain
        ret.expire_date = exp_date
    
    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.remaining_own_vp_gasha_ticket) \
        + encode_date_str(self.expire_date)

class BeginnerMissionUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ad_confirm_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.ad_confirm_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, confirm_date: datetime, confirm_flg: bool = False) -> "BeginnerMissionUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.ad_confirm_flag = confirm_flg
        ret.ad_confirm_date = confirm_date
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.ad_confirm_flag) \
        + encode_date_str(self.ad_confirm_date)

class EquipmentUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.user_equipment_id, new_off = decode_str(data, off)
        off += new_off
        
        self.equipment_id = decode_int(data, off)
        off += INT_OFF
        self.enhancement_value = decode_short(data, off)
        off += SHORT_OFF
        self.max_enhancement_value_extended_num = decode_short(data, off)
        off += SHORT_OFF
        self.enhancement_exp = decode_int(data, off)
        off += INT_OFF
        self.possible_awakening_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.awakening_stage = decode_short(data, off)
        off += SHORT_OFF
        self.awakening_exp = decode_int(data, off)
        off += INT_OFF
        
        self.property1_property_id = decode_int(data, off)
        off += INT_OFF
        self.property1_value1 = decode_int(data, off)
        off += INT_OFF
        self.property1_value2 = decode_int(data, off)
        off += INT_OFF
        self.property2_property_id = decode_int(data, off)
        off += INT_OFF
        self.property2_value1 = decode_int(data, off)
        off += INT_OFF
        self.property2_value2 = decode_int(data, off)
        off += INT_OFF
        self.property3_property_id = decode_int(data, off)
        off += INT_OFF
        self.property3_value1 = decode_int(data, off)
        off += INT_OFF
        self.property3_value2 = decode_int(data, off)
        off += INT_OFF
        self.property4_property_id = decode_int(data, off)
        off += INT_OFF
        self.property4_value1 = decode_int(data, off)
        off += INT_OFF
        self.property4_value2 = decode_int(data, off)
        off += INT_OFF
        
        self.converted_card_num = decode_short(data, off)
        off += SHORT_OFF
        self.shop_purchase_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.protect_flag = decode_byte(data, off)
        off += BYTE_OFF
        
        self.get_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset
    
    @classmethod
    def from_args(cls, equip_data: Dict) -> "EquipmentUserData":
        ret = cls(b"\x00" * 79, 0)
        ret.user_equipment_id = str(equip_data['id'])
        ret.equipment_id = equip_data['equipment_id']
        ret.enhancement_value = equip_data['enhancement_value']
        ret.max_enhancement_value_extended_num = 0 #equip_data['max_enhancement_value_extended_num'] TODO: This
        ret.enhancement_exp = equip_data['enhancement_exp']
        ret.possible_awakening_flag = equip_data['possible_awakening_flag']
        ret.awakening_stage = equip_data['awakening_stage']
        ret.awakening_exp = equip_data['awakening_exp']
        ret.property1_property_id = equip_data['property1_property_id']
        ret.property1_value1 = equip_data['property1_value1']
        ret.property1_value2 = equip_data['property1_value2']
        ret.property2_property_id = equip_data['property2_property_id']
        ret.property2_value1 = equip_data['property2_value1']
        ret.property2_value2 = equip_data['property2_value2']
        ret.property3_property_id = equip_data['property2_property_id']
        ret.property3_value1 = equip_data['property3_value1']
        ret.property3_value2 = equip_data['property3_value2']
        ret.property4_property_id = equip_data['property2_property_id']
        ret.property4_value1 = equip_data['property4_value1']
        ret.property4_value2 = equip_data['property4_value2']
        ret.converted_card_num = equip_data['converted_card_num']
        ret.shop_purchase_flag = equip_data['is_shop_purchase']
        ret.protect_flag = equip_data['is_protect']
        ret.get_date = equip_data['get_date']
        return ret
    
    def make(self) -> bytes:
        return encode_str(self.user_equipment_id) \
        + encode_int(self.equipment_id) \
        + encode_short(self.enhancement_value) \
        + encode_short(self.max_enhancement_value_extended_num) \
        + encode_int(self.enhancement_exp) \
        + encode_byte(self.possible_awakening_flag) \
        + encode_short(self.awakening_stage) \
        + encode_int(self.awakening_exp) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2) \
        + encode_short(self.converted_card_num) \
        + encode_byte(self.shop_purchase_flag) \
        + encode_byte(self.protect_flag) \
        + encode_date_str(self.get_date)

class ItemUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int) -> None:
        super().__init__(data, offset)
        off = offset
        self.user_item_id, new_off = decode_str(data, off)
        off += new_off
        self.item_id = decode_int(data, off)
        off += INT_OFF
        self.protect_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.get_date = decode_date_str(data, off)

        self._sz = off - offset
    
    @classmethod
    def from_args(cls, item_data: Dict) -> BaseHelper:
        ret = cls(b"\x00" * 993, 0)
        ret.user_item_id = str(item_data['id'])
        ret.item_id = item_data['item_id']
        ret.protect_flag = 0
        ret.get_date = item_data['get_date']
        return ret
    
    def make(self) -> bytes:
        return encode_str(self.user_item_id) \
        + encode_int(self.item_id) \
        + encode_byte(self.protect_flag) \
        + encode_date_str(self.get_date)

class SupportLogUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_support_log_id, new_off = decode_str(data, off)
        off += new_off

        self.support_log_id = decode_int(data, off)
        off += INT_OFF

        self.possible_awakening_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.awakening_exp = decode_int(data, off)
        off += INT_OFF

        self.converted_card_num = decode_short(data, off)
        off += SHORT_OFF

        self.shop_purchase_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.protect_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.get_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, user_support_log: str, support_log: int) -> "SupportLogUserData":
        ret = cls(b"\x00" * 23, 0)
        ret.user_support_log_id = user_support_log
        ret.support_log_id = support_log
        ret.possible_awakening_flag = 0
        ret.awakening_stage = 0
        ret.awakening_exp = 0
        ret.converted_card_num = 0
        ret.shop_purchase_flag = 0
        ret.protect_flag = 0
        ret.get_date = prs_dt()
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_support_log_id) \
        + encode_int(self.support_log_id) \
        + encode_byte(self.possible_awakening_flag) \
        + encode_short(self.awakening_stage) \
        + encode_int(self.awakening_exp) \
        + encode_short(self.converted_card_num) \
        + encode_byte(self.shop_purchase_flag) \
        + encode_byte(self.protect_flag) \
        + encode_date_str(self.get_date)

class EventItemUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_event_item_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.event_item_id = decode_int(data, off)
        off += INT_OFF

        self.own_num = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EventItemUserData":
        ret = cls(b"\x00" * 996, 0)
        ret.user_event_item_id = data['UserEventItemId']
        ret.user_id = data['UserId']
        ret.event_item_id = data['EventItemId']
        ret.own_num = data['OwnNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_event_item_id) \
        + encode_str(self.user_id) \
        + encode_int(self.event_item_id) \
        + encode_int(self.own_num)

class GashaMedalUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_gasha_medal_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.gasha_medal_id = decode_int(data, off)
        off += INT_OFF

        self.own_num = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalUserData":
        ret = cls(b"\x00" * 996, 0)
        ret.user_gasha_medal_id = data['UserGashaMedalId']
        ret.user_id = data['UserId']
        ret.gasha_medal_id = data['GashaMedalId']
        ret.own_num = data['OwnNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_gasha_medal_id) \
        + encode_str(self.user_id) \
        + encode_int(self.gasha_medal_id) \
        + encode_int(self.own_num)

class TitleUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_title_id, new_off = decode_str(data, off)
        off += new_off

        self.title_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, user_title_id: str, title_id: int) -> "TitleUserData":
        ret = cls(b"\x00" * 8, 0)
        ret.user_title_id = user_title_id
        ret.title_id = title_id
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_title_id) \
        + encode_int(self.title_id)

class PlayerRankData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.player_rank_id = decode_short(data, off)
        off += SHORT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self.storage = decode_short(data, off)
        off += SHORT_OFF

        self.team_preset = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PlayerRankData":
        ret = cls(b"\x00" * 99, 0)
        ret.player_rank_id = data['PlayerRankId']
        ret.total_exp = data['TotalExp']
        ret.storage = data['Storage']
        ret.team_preset = data['TeamPreset']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.player_rank_id) \
        + encode_int(self.total_exp) \
        + encode_short(self.storage) \
        + encode_short(self.team_preset)

class TitleData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.title_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.requirement = decode_int(data, off)
        off += INT_OFF

        self.value1 = decode_int(data, off)
        off += INT_OFF

        self.value2 = decode_int(data, off)
        off += INT_OFF

        self.rank = decode_int(data, off)
        off += INT_OFF

        self.image_file_path, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TitleData":
        ret = cls(b"\x00" * 99, 0)
        ret.title_id = data['TitleId']
        ret.display_name = data['DisplayName']
        ret.requirement = data['Requirement']
        ret.value1 = data['Value1']
        ret.value2 = data['Value2']
        ret.rank = data['Rank']
        ret.image_file_path = data['ImageFilePath']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.title_id) \
        + encode_str(self.display_name) \
        + encode_int(self.requirement) \
        + encode_int(self.value1) \
        + encode_int(self.value2) \
        + encode_int(self.rank) \
        + encode_str(self.image_file_path)

class FragmentData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.fragment_id = decode_short(data, off)
        off += SHORT_OFF

        self.exp = decode_int(data, off)
        off += INT_OFF

        self.comment_id, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "FragmentData":
        ret = cls(b"\x00" * 99, 0)
        ret.fragment_id = data['FragmentId']
        ret.exp = data['Exp']
        ret.comment_id = data['CommentId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.fragment_id) \
        + encode_int(self.exp) \
        + encode_str(self.comment_id)

class RewardTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.reward_table_id = decode_int(data, off)
        off += INT_OFF

        self.reward_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.unanalyzed_log_grade_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.strength_min = decode_int(data, off)
        off += INT_OFF

        self.strength_max = decode_int(data, off)
        off += INT_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.rate = decode_int(data, off)
        off += INT_OFF

        self.quest_info_display_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "RewardTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.reward_table_id = data['RewardTableId']
        ret.reward_table_sub_id = data['RewardTableSubId']
        ret.unanalyzed_log_grade_id = data['UnanalyzedLogGradeId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength_min = data['StrengthMin']
        ret.strength_max = data['StrengthMax']
        ret.property_table_sub_id = data['PropertyTableSubId']
        ret.rate = data['Rate']
        ret.quest_info_display_flag = data['QuestInfoDisplayFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.reward_table_id) \
        + encode_int(self.reward_table_sub_id) \
        + encode_int(self.unanalyzed_log_grade_id) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.strength_min) \
        + encode_int(self.strength_max) \
        + encode_int(self.property_table_sub_id) \
        + encode_int(self.rate) \
        + encode_byte(self.quest_info_display_flag)

class RewardSetData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.reward_set_id = decode_int(data, off)
        off += INT_OFF

        self.reward_set_sub_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "RewardSetData":
        ret = cls(b"\x00" * 99, 0)
        ret.reward_set_id = data['RewardSetId']
        ret.reward_set_sub_id = data['RewardSetSubId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.reward_set_id) \
        + encode_int(self.reward_set_sub_id) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class UnanalyzedLogGradeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unanalyzed_log_grade_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.comment_id, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "UnanalyzedLogGradeData":
        ret = cls(b"\x00" * 99, 0)
        ret.unanalyzed_log_grade_id = data['UnanalyzedLogGradeId']
        ret.name = data['Name']
        ret.comment_id = data['CommentId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unanalyzed_log_grade_id) \
        + encode_str(self.name) \
        + encode_str(self.comment_id)

class AppointLeaderParamData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.appoint_leader_param_id = decode_short(data, off)
        off += SHORT_OFF

        self.initial_synchro_rate = decode_int(data, off)
        off += INT_OFF

        self.appoint_leader_increment_synchro_rate = decode_int(data, off)
        off += INT_OFF

        self.awakening_increment_synchro_rate = decode_int(data, off)
        off += INT_OFF

        self.foil_add_synchro_rate = decode_int(data, off)
        off += INT_OFF

        self.appoint_leader_trust_bonus = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AppointLeaderParamData":
        ret = cls(b"\x00" * 99, 0)
        ret.appoint_leader_param_id = data['AppointLeaderParamId']
        ret.initial_synchro_rate = data['InitialSynchroRate']
        ret.appoint_leader_increment_synchro_rate = data['AppointLeaderIncrementSynchroRate']
        ret.awakening_increment_synchro_rate = data['AwakeningIncrementSynchroRate']
        ret.foil_add_synchro_rate = data['FoilAddSynchroRate']
        ret.appoint_leader_trust_bonus = data['AppointLeaderTrustBonus']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.appoint_leader_param_id) \
        + encode_int(self.initial_synchro_rate) \
        + encode_int(self.appoint_leader_increment_synchro_rate) \
        + encode_int(self.awakening_increment_synchro_rate) \
        + encode_int(self.foil_add_synchro_rate) \
        + encode_int(self.appoint_leader_trust_bonus)

class AppointLeaderEffectData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.appoint_leader_effect_id = decode_short(data, off)
        off += SHORT_OFF

        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.info_text_format, new_off = decode_str(data, off)
        off += new_off

        self.appoint_leader_effect_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.low_effect_value, new_off = decode_str(data, off)
        off += new_off

        self.middle_effect_value, new_off = decode_str(data, off)
        off += new_off

        self.high_effect_value, new_off = decode_str(data, off)
        off += new_off

        self.max_effect_value, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AppointLeaderEffectData":
        ret = cls(b"\x00" * 99, 0)
        ret.appoint_leader_effect_id = data['AppointLeaderEffectId']
        ret.chara_id = data['CharaId']
        ret.info_text_format = data['InfoTextFormat']
        ret.appoint_leader_effect_type_id = data['AppointLeaderEffectTypeId']
        ret.low_effect_value = data['LowEffectValue']
        ret.middle_effect_value = data['MiddleEffectValue']
        ret.high_effect_value = data['HighEffectValue']
        ret.max_effect_value = data['MaxEffectValue']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.appoint_leader_effect_id) \
        + encode_short(self.chara_id) \
        + encode_str(self.info_text_format) \
        + encode_short(self.appoint_leader_effect_type_id) \
        + encode_str(self.low_effect_value) \
        + encode_str(self.middle_effect_value) \
        + encode_str(self.high_effect_value) \
        + encode_str(self.max_effect_value)

class AppointLeaderEffectTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.appoint_leader_effect_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AppointLeaderEffectTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.appoint_leader_effect_type_id = data['AppointLeaderEffectTypeId']
        ret.name = data['Name']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.appoint_leader_effect_type_id) \
        + encode_str(self.name)

class RarityData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.rarity_id = decode_short(data, off)
        off += SHORT_OFF

        self.require_col_my_card = decode_int(data, off)
        off += INT_OFF

        self.require_col_other_card = decode_int(data, off)
        off += INT_OFF

        self.require_medal_other_card = decode_int(data, off)
        off += INT_OFF

        self.synthesis_exp_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "RarityData":
        ret = cls(b"\x00" * 99, 0)
        ret.rarity_id = data['RarityId']
        ret.require_col_my_card = data['RequireColMyCard']
        ret.require_col_other_card = data['RequireColOtherCard']
        ret.require_medal_other_card = data['RequireMedalOtherCard']
        ret.synthesis_exp_rate = data['SynthesisExpRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.rarity_id) \
        + encode_int(self.require_col_my_card) \
        + encode_int(self.require_col_other_card) \
        + encode_int(self.require_medal_other_card) \
        + encode_str(self.synthesis_exp_rate)

class CompositionEventData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.composition_event_id = decode_short(data, off)
        off += SHORT_OFF

        self.composition_exp_rate, new_off = decode_str(data, off)
        off += new_off

        self.awakening_exp_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CompositionEventData":
        ret = cls(b"\x00" * 99, 0)
        ret.composition_event_id = data['CompositionEventId']
        ret.composition_exp_rate = data['CompositionExpRate']
        ret.awakening_exp_rate = data['AwakeningExpRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.composition_event_id) \
        + encode_str(self.composition_exp_rate) \
        + encode_str(self.awakening_exp_rate)

class CompositionParamData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.composition_param_id = decode_short(data, off)
        off += SHORT_OFF

        self.use_value = decode_int(data, off)
        off += INT_OFF

        self.max_extended_use_coef, new_off = decode_str(data, off)
        off += new_off

        self.awakening_coef, new_off = decode_str(data, off)
        off += new_off

        self.use_value_support_log = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CompositionParamData":
        ret = cls(b"\x00" * 99, 0)
        ret.composition_param_id = data['CompositionParamId']
        ret.use_value = data['UseValue']
        ret.max_extended_use_coef = data['MaxExtendedUseCoef']
        ret.awakening_coef = data['AwakeningCoef']
        ret.use_value_support_log = data['UseValueSupportLog']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.composition_param_id) \
        + encode_int(self.use_value) \
        + encode_str(self.max_extended_use_coef) \
        + encode_str(self.awakening_coef) \
        + encode_int(self.use_value_support_log)

class GamePlayPriceData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.game_play_price_id = decode_short(data, off)
        off += SHORT_OFF

        self.player_rank_id = decode_short(data, off)
        off += SHORT_OFF

        self.episode_ticket = decode_int(data, off)
        off += INT_OFF

        self.trial_tower_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.custom_retry_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.subdue_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.continue_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.continue_credit = decode_short(data, off)
        off += SHORT_OFF

        self.extend_time_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.reward_grade_up_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.reward_grade_up_credit = decode_short(data, off)
        off += SHORT_OFF

        self.give_free_ticket = decode_short(data, off)
        off += SHORT_OFF

        self.free_continue_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GamePlayPriceData":
        ret = cls(b"\x00" * 99, 0)
        ret.game_play_price_id = data['GamePlayPriceId']
        ret.player_rank_id = data['PlayerRankId']
        ret.episode_ticket = data['EpisodeTicket']
        ret.trial_tower_ticket = data['TrialTowerTicket']
        ret.custom_retry_ticket = data['CustomRetryTicket']
        ret.subdue_ticket = data['SubdueTicket']
        ret.continue_ticket = data['ContinueTicket']
        ret.continue_credit = data['ContinueCredit']
        ret.extend_time_ticket = data['ExtendTimeTicket']
        ret.reward_grade_up_ticket = data['RewardGradeUpTicket']
        ret.reward_grade_up_credit = data['RewardGradeUpCredit']
        ret.give_free_ticket = data['GiveFreeTicket']
        ret.free_continue_num = data['FreeContinueNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.game_play_price_id) \
        + encode_short(self.player_rank_id) \
        + encode_int(self.episode_ticket) \
        + encode_short(self.trial_tower_ticket) \
        + encode_short(self.custom_retry_ticket) \
        + encode_short(self.subdue_ticket) \
        + encode_short(self.continue_ticket) \
        + encode_short(self.continue_credit) \
        + encode_short(self.extend_time_ticket) \
        + encode_short(self.reward_grade_up_ticket) \
        + encode_short(self.reward_grade_up_credit) \
        + encode_short(self.give_free_ticket) \
        + encode_short(self.free_continue_num)

class BuyTicketData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.buy_ticket_id = decode_int(data, off)
        off += INT_OFF

        self.buy_ticket_pattern = decode_int(data, off)
        off += INT_OFF

        self.credit_cnt = decode_int(data, off)
        off += INT_OFF

        self.get_ticket_cnt = decode_int(data, off)
        off += INT_OFF

        self.get_bonus_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BuyTicketData":
        ret = cls(b"\x00" * 99, 0)
        ret.buy_ticket_id = data['BuyTicketId']
        ret.buy_ticket_pattern = data['BuyTicketPattern']
        ret.credit_cnt = data['CreditCnt']
        ret.get_ticket_cnt = data['GetTicketCnt']
        ret.get_bonus_vp = data['GetBonusVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.buy_ticket_id) \
        + encode_int(self.buy_ticket_pattern) \
        + encode_int(self.credit_cnt) \
        + encode_int(self.get_ticket_cnt) \
        + encode_int(self.get_bonus_vp)

class TipsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.tips_id = decode_int(data, off)
        off += INT_OFF

        self.tips_category = decode_byte(data, off)
        off += BYTE_OFF

        self.tips_text, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TipsData":
        ret = cls(b"\x00" * 99, 0)
        ret.tips_id = data['TipsId']
        ret.tips_category = data['TipsCategory']
        ret.tips_text = data['TipsText']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.tips_id) \
        + encode_byte(self.tips_category) \
        + encode_str(self.tips_text)

class CapData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.cap_id = decode_short(data, off)
        off += SHORT_OFF

        self.trust1_cap = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CapData":
        ret = cls(b"\x00" * 99, 0)
        ret.cap_id = data['CapId']
        ret.trust1_cap = data['Trust1Cap']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.cap_id) \
        + encode_int(self.trust1_cap)

class HeroLogData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.nickname, new_off = decode_str(data, off)
        off += new_off

        self.rarity = decode_byte(data, off)
        off += BYTE_OFF

        self.weapon_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_role_id = decode_short(data, off)
        off += SHORT_OFF

        self.costume_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.default_equipment_id1 = decode_int(data, off)
        off += INT_OFF

        self.default_equipment_id2 = decode_int(data, off)
        off += INT_OFF

        self.skill_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.hp_min = decode_int(data, off)
        off += INT_OFF

        self.hp_max = decode_int(data, off)
        off += INT_OFF

        self.str_min = decode_int(data, off)
        off += INT_OFF

        self.str_max = decode_int(data, off)
        off += INT_OFF

        self.vit_min = decode_int(data, off)
        off += INT_OFF

        self.vit_max = decode_int(data, off)
        off += INT_OFF

        self.int_min = decode_int(data, off)
        off += INT_OFF

        self.int_max = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.sale_price = decode_int(data, off)
        off += INT_OFF

        self.composition_exp = decode_int(data, off)
        off += INT_OFF

        self.awakening_exp = decode_int(data, off)
        off += INT_OFF

        self.slot4_unlock_level = decode_int(data, off)
        off += INT_OFF

        self.slot5_unlock_level = decode_int(data, off)
        off += INT_OFF

        self.cut_in_image, new_off = decode_str(data, off)
        off += new_off

        self.cut_in_image_awake, new_off = decode_str(data, off)
        off += new_off

        self.cut_in_upper_side_text = decode_byte(data, off)
        off += BYTE_OFF

        self.chara_comment_image, new_off = decode_str(data, off)
        off += new_off

        self.chara_comment_image_awake, new_off = decode_str(data, off)
        off += new_off

        self.quest_start_introduce, new_off = decode_str(data, off)
        off += new_off

        self.quest_start_introduce_awake, new_off = decode_str(data, off)
        off += new_off

        self.quest_chara_icon, new_off = decode_str(data, off)
        off += new_off

        self.quest_chara_icon_awake, new_off = decode_str(data, off)
        off += new_off

        self.quest_chara_icon_loss, new_off = decode_str(data, off)
        off += new_off

        self.quest_chara_icon_awake_loss, new_off = decode_str(data, off)
        off += new_off

        self.collection_display_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.collection_empty_frame_display_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "HeroLogData":
        ret = cls(b"\x00" * 99, 0)
        ret.hero_log_id = data['HeroLogId']
        ret.chara_id = data['CharaId']
        ret.name = data['Name']
        ret.nickname = data['Nickname']
        ret.rarity = data['Rarity']
        ret.weapon_type_id = data['WeaponTypeId']
        ret.hero_log_role_id = data['HeroLogRoleId']
        ret.costume_type_id = data['CostumeTypeId']
        ret.unit_id = data['UnitId']
        ret.default_equipment_id1 = data['DefaultEquipmentId1']
        ret.default_equipment_id2 = data['DefaultEquipmentId2']
        ret.skill_table_sub_id = data['SkillTableSubId']
        ret.hp_min = data['HpMin']
        ret.hp_max = data['HpMax']
        ret.str_min = data['StrMin']
        ret.str_max = data['StrMax']
        ret.vit_min = data['VitMin']
        ret.vit_max = data['VitMax']
        ret.int_min = data['IntMin']
        ret.int_max = data['IntMax']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        ret.flavor_text = data['FlavorText']
        ret.sale_price = data['SalePrice']
        ret.composition_exp = data['CompositionExp']
        ret.awakening_exp = data['AwakeningExp']
        ret.slot4_unlock_level = data['Slot4UnlockLevel']
        ret.slot5_unlock_level = data['Slot5UnlockLevel']
        ret.cut_in_image = data['CutinImage']
        ret.cut_in_image_awake = data['CutinImageAwake']
        ret.cut_in_upper_side_text = data['CutinUpperSideText']
        ret.chara_comment_image = data['CharaCommentImage']
        ret.chara_comment_image_awake = data['CharaCommentImageAwake']
        ret.quest_start_introduce = data['QuestStartIntroduce']
        ret.quest_start_introduce_awake = data['QuestStartIntroduceAwake']
        ret.quest_chara_icon = data['QuestCharaIcon']
        ret.quest_chara_icon_awake = data['QuestCharaIconAwake']
        ret.quest_chara_icon_loss = data['QuestCharaIconLoss']
        ret.quest_chara_icon_awake_loss = data['QuestCharaIconAwakeLoss']
        ret.collection_display_start_date = data['CollectionDisplayStartDate']
        ret.collection_empty_frame_display_flag = data['CollectionEmptyFrameDisplayFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.hero_log_id) \
        + encode_short(self.chara_id) \
        + encode_str(self.name) \
        + encode_str(self.nickname) \
        + encode_byte(self.rarity) \
        + encode_short(self.weapon_type_id) \
        + encode_short(self.hero_log_role_id) \
        + encode_short(self.costume_type_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.default_equipment_id1) \
        + encode_int(self.default_equipment_id2) \
        + encode_int(self.skill_table_sub_id) \
        + encode_int(self.hp_min) \
        + encode_int(self.hp_max) \
        + encode_int(self.str_min) \
        + encode_int(self.str_max) \
        + encode_int(self.vit_min) \
        + encode_int(self.vit_max) \
        + encode_int(self.int_min) \
        + encode_int(self.int_max) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2) \
        + encode_str(self.flavor_text) \
        + encode_int(self.sale_price) \
        + encode_int(self.composition_exp) \
        + encode_int(self.awakening_exp) \
        + encode_int(self.slot4_unlock_level) \
        + encode_int(self.slot5_unlock_level) \
        + encode_str(self.cut_in_image) \
        + encode_str(self.cut_in_image_awake) \
        + encode_byte(self.cut_in_upper_side_text) \
        + encode_str(self.chara_comment_image) \
        + encode_str(self.chara_comment_image_awake) \
        + encode_str(self.quest_start_introduce) \
        + encode_str(self.quest_start_introduce_awake) \
        + encode_str(self.quest_chara_icon) \
        + encode_str(self.quest_chara_icon_awake) \
        + encode_str(self.quest_chara_icon_loss) \
        + encode_str(self.quest_chara_icon_awake_loss) \
        + encode_date_str(self.collection_display_start_date) \
        + encode_byte(self.collection_empty_frame_display_flag)

class HeroLogLevelData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.level = decode_short(data, off)
        off += SHORT_OFF

        self.require_exp = decode_int(data, off)
        off += INT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "HeroLogLevelData":
        ret = cls(b"\x00" * 99, 0)
        ret.level = data['HeroLogLevelId']
        ret.require_exp = data['RequireExp']
        ret.total_exp = data['TotalExp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.level) \
        + encode_int(self.require_exp) \
        + encode_int(self.total_exp)

class HeroLogRoleData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.hero_log_role_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "HeroLogRoleData":
        ret = cls(b"\x00" * 99, 0)
        ret.hero_log_role_id = data['HeroLogRoleId']
        ret.name = data['Name']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.hero_log_role_id) \
        + encode_str(self.name)

class HeroLogTrustRankData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.rank = decode_short(data, off)
        off += SHORT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "HeroLogTrustRankData":
        ret = cls(b"\x00" * 99, 0)
        ret.rank = data['HeroLogTrustRankId']
        ret.total_exp = data['TotalExp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.rank) \
        + encode_int(self.total_exp)

class CharaData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.roma, new_off = decode_str(data, off)
        off += new_off

        self.gender = decode_short(data, off)
        off += SHORT_OFF

        self.real_name, new_off = decode_str(data, off)
        off += new_off

        self.comment, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CharaData":
        ret = cls(b"\x00" * 99, 0)
        ret.chara_id = data['CharaId']
        ret.name = data['Name']
        ret.roma = data['Roma']
        ret.gender = data['Gender']
        ret.real_name = data['RealName']
        ret.comment = data['Comment']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.chara_id) \
        + encode_str(self.name) \
        + encode_str(self.roma) \
        + encode_short(self.gender) \
        + encode_str(self.real_name) \
        + encode_str(self.comment)

class CharaFriendlyRankData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.rank = decode_short(data, off)
        off += SHORT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CharaFriendlyRankData":
        ret = cls(b"\x00" * 99, 0)
        ret.rank = data['CharaFriendlyRankId']
        ret.total_exp = data['TotalExp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.rank) \
        + encode_int(self.total_exp)

class EquipmentData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.equipment_id = decode_int(data, off)
        off += INT_OFF

        self.equipment_type = decode_byte(data, off)
        off += BYTE_OFF

        self.weapon_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.rarity = decode_byte(data, off)
        off += BYTE_OFF

        self.prefab, new_off = decode_str(data, off)
        off += new_off

        self.power = decode_int(data, off)
        off += INT_OFF

        self.strength_increment = decode_int(data, off)
        off += INT_OFF

        self.skill_condition = decode_short(data, off)
        off += SHORT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.sale_price = decode_int(data, off)
        off += INT_OFF

        self.composition_exp = decode_int(data, off)
        off += INT_OFF

        self.awakening_exp = decode_int(data, off)
        off += INT_OFF

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.collection_display_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.collection_empty_frame_display_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EquipmentData":
        ret = cls(b"\x00" * 99, 0)
        ret.equipment_id = data['EquipmentId']
        ret.equipment_type = data['EquipmentType']
        ret.weapon_type_id = data['WeaponTypeId']
        ret.name = data['Name']
        ret.rarity = data['Rarity']
        ret.prefab = data['Prefab']
        ret.power = data['Power']
        ret.strength_increment = data['StrengthIncrement']
        ret.skill_condition = data['SkillCondition']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        ret.sale_price = data['SalePrice']
        ret.composition_exp = data['CompositionExp']
        ret.awakening_exp = data['AwakeningExp']
        ret.flavor_text = data['FlavorText']
        ret.collection_display_start_date = data['CollectionDisplayStartDate']
        ret.collection_empty_frame_display_flag = data['CollectionEmptyFrameDisplayFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.equipment_id) \
        + encode_byte(self.equipment_type) \
        + encode_short(self.weapon_type_id) \
        + encode_str(self.name) \
        + encode_byte(self.rarity) \
        + encode_str(self.prefab) \
        + encode_int(self.power) \
        + encode_int(self.strength_increment) \
        + encode_short(self.skill_condition) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2) \
        + encode_int(self.sale_price) \
        + encode_int(self.composition_exp) \
        + encode_int(self.awakening_exp) \
        + encode_str(self.flavor_text) \
        + encode_date_str(self.collection_display_start_date) \
        + encode_byte(self.collection_empty_frame_display_flag)

class EquipmentLevelData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.level = decode_short(data, off)
        off += SHORT_OFF

        self.require_exp = decode_int(data, off)
        off += INT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EquipmentLevelData":
        ret = cls(b"\x00" * 99, 0)
        ret.level = data['EquipmentLevelId']
        ret.require_exp = data['RequireExp']
        ret.total_exp = data['TotalExp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.level) \
        + encode_int(self.require_exp) \
        + encode_int(self.total_exp)

class WeaponTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.weapon_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.action_behaviour, new_off = decode_str(data, off)
        off += new_off

        self.sound_behaviour, new_off = decode_str(data, off)
        off += new_off

        self.physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.main_equip = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equip1 = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equip2 = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "WeaponTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.weapon_type_id = data['WeaponTypeId']
        ret.name = data['Name']
        ret.action_behaviour = data['ActionBehaviour']
        ret.sound_behaviour = data['SoundBehaviour']
        ret.physics_attr = data['PhysicsAttr']
        ret.main_equip = data['MainEquip']
        ret.sub_equip1 = data['SubEquip1']
        ret.sub_equip2 = data['SubEquip2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.weapon_type_id) \
        + encode_str(self.name) \
        + encode_str(self.action_behaviour) \
        + encode_str(self.sound_behaviour) \
        + encode_short(self.physics_attr) \
        + encode_short(self.main_equip) \
        + encode_short(self.sub_equip1) \
        + encode_short(self.sub_equip2)

class ItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.item_id = decode_int(data, off)
        off += INT_OFF

        self.item_type = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.rarity = decode_byte(data, off)
        off += BYTE_OFF

        self.value = decode_int(data, off)
        off += INT_OFF

        self.property_id = decode_int(data, off)
        off += INT_OFF

        self.property_value1_min, new_off = decode_str(data, off)
        off += new_off

        self.property_value1_max, new_off = decode_str(data, off)
        off += new_off

        self.property_value2_min, new_off = decode_str(data, off)
        off += new_off

        self.property_value2_max, new_off = decode_str(data, off)
        off += new_off

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.sale_price = decode_int(data, off)
        off += INT_OFF

        self.item_icon, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.item_id = data['ItemId']
        ret.item_type = data['ItemTypeId']
        ret.name = data['Name']
        ret.rarity = data['Rarity']
        ret.value = data['Value']
        ret.property_id = data['PropertyId']
        ret.property_value1_min = data['PropertyValue1Min']
        ret.property_value1_max = data['PropertyValue1Max']
        ret.property_value2_min = data['PropertyValue2Min']
        ret.property_value2_max = data['PropertyValue2Max']
        ret.flavor_text = data['FlavorText']
        ret.sale_price = data['SalePrice']
        ret.item_icon = data['ItemIcon']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.item_id) \
        + encode_int(self.item_type) \
        + encode_str(self.name) \
        + encode_byte(self.rarity) \
        + encode_int(self.value) \
        + encode_int(self.property_id) \
        + encode_str(self.property_value1_min) \
        + encode_str(self.property_value1_max) \
        + encode_str(self.property_value2_min) \
        + encode_str(self.property_value2_max) \
        + encode_str(self.flavor_text) \
        + encode_int(self.sale_price) \
        + encode_str(self.item_icon)

class ItemTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.item_type_id = decode_int(data, off)
        off += INT_OFF

        self.item_type_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ItemTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.item_type_id = data['ItemTypeId']
        ret.item_type_name = data['ItemTypeName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.item_type_id) \
        + encode_str(self.item_type_name)

class BuffItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.buff_item_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BuffItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.buff_item_id = data['BuffItemId']
        ret.name = data['Name']
        ret.flavor_text = data['FlavorText']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.buff_item_id) \
        + encode_str(self.name) \
        + encode_str(self.flavor_text)

class EnemyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.enemy_id = decode_short(data, off)
        off += SHORT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EnemyData":
        ret = cls(b"\x00" * 99, 0)
        ret.enemy_id = data['EnemyId']
        ret.unit_id = data['UnitId']
        ret.name = data['Name']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.enemy_id) \
        + encode_int(self.unit_id) \
        + encode_str(self.name)

class EnemySetData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.enemy_set_id = decode_int(data, off)
        off += INT_OFF

        self.enemy_set_sub_id = decode_int(data, off)
        off += INT_OFF

        self.enemy_id = decode_int(data, off)
        off += INT_OFF

        self.enemy_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EnemySetData":
        ret = cls(b"\x00" * 99, 0)
        ret.enemy_set_id = data['EnemySetId']
        ret.enemy_set_sub_id = data['EnemySetSubId']
        ret.enemy_id = data['EnemyId']
        ret.enemy_num = data['EnemyNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.enemy_set_id) \
        + encode_int(self.enemy_set_sub_id) \
        + encode_int(self.enemy_id) \
        + encode_short(self.enemy_num)

class EnemyKindData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self.enemy_category_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.icon_filepath, new_off = decode_str(data, off)
        off += new_off

        self.weak_physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.weak_magic_attr = decode_short(data, off)
        off += SHORT_OFF

        self.weak_text, new_off = decode_str(data, off)
        off += new_off

        self.resist_text, new_off = decode_str(data, off)
        off += new_off

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.collection_display_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.collection_empty_frame_display_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EnemyKindData":
        ret = cls(b"\x00" * 99, 0)
        ret.enemy_kind_id = data['EnemyKindId']
        ret.enemy_category_id = data['EnemyCategoryId']
        ret.name = data['Name']
        ret.icon_filepath = data['IconFilepath']
        ret.weak_physics_attr = data['WeakPhysicsAttr']
        ret.weak_magic_attr = data['WeakMagicAttr']
        ret.weak_text = data['WeakText']
        ret.resist_text = data['ResistText']
        ret.flavor_text = data['FlavorText']
        ret.collection_display_start_date = data['CollectionDisplayStartDate']
        ret.collection_empty_frame_display_flag = data['CollectionEmptyFrameDisplayFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.enemy_kind_id) \
        + encode_short(self.enemy_category_id) \
        + encode_str(self.name) \
        + encode_str(self.icon_filepath) \
        + encode_short(self.weak_physics_attr) \
        + encode_short(self.weak_magic_attr) \
        + encode_str(self.weak_text) \
        + encode_str(self.resist_text) \
        + encode_str(self.flavor_text) \
        + encode_date_str(self.collection_display_start_date) \
        + encode_byte(self.collection_empty_frame_display_flag)

class EnemyCategoryData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.enemy_category_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.detail_text, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EnemyCategoryData":
        ret = cls(b"\x00" * 99, 0)
        ret.enemy_category_id = data['EnemyCategoryId']
        ret.name = data['Name']
        ret.detail_text = data['DetailText']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.enemy_category_id) \
        + encode_str(self.name) \
        + encode_str(self.detail_text)

class UnitData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.prefab, new_off = decode_str(data, off)
        off += new_off

        self.animator, new_off = decode_str(data, off)
        off += new_off

        self.collision, new_off = decode_str(data, off)
        off += new_off

        self.radius, new_off = decode_str(data, off)
        off += new_off

        self.child_unit_id = decode_int(data, off)
        off += INT_OFF

        self.stage_start_prefab, new_off = decode_str(data, off)
        off += new_off

        self.stage_start_y, new_off = decode_str(data, off)
        off += new_off

        self.stage_start_z, new_off = decode_str(data, off)
        off += new_off

        self.stage_touch_y, new_off = decode_str(data, off)
        off += new_off

        self.stage_touch_z, new_off = decode_str(data, off)
        off += new_off

        self.playable = decode_byte(data, off)
        off += BYTE_OFF

        self.monster = decode_byte(data, off)
        off += BYTE_OFF

        self.gimmick = decode_byte(data, off)
        off += BYTE_OFF

        self.anger = decode_byte(data, off)
        off += BYTE_OFF

        self.commander = decode_byte(data, off)
        off += BYTE_OFF

        self.isolated = decode_byte(data, off)
        off += BYTE_OFF

        self.base_behaviour, new_off = decode_str(data, off)
        off += new_off

        self.sound_behaviour, new_off = decode_str(data, off)
        off += new_off

        self.weapon_type = decode_int(data, off)
        off += INT_OFF

        self.poison_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.paralysis_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.sealed_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.question_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.blue_rose_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.charm_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.burning_time_coef, new_off = decode_str(data, off)
        off += new_off

        self.invalid_quake = decode_byte(data, off)
        off += BYTE_OFF

        self.guard_coef, new_off = decode_str(data, off)
        off += new_off

        self.just_guard_time, new_off = decode_str(data, off)
        off += new_off

        self.flip_hp = decode_short(data, off)
        off += SHORT_OFF

        self.down_hp = decode_short(data, off)
        off += SHORT_OFF

        self.flip_recover_time, new_off = decode_str(data, off)
        off += new_off

        self.down_recover_time, new_off = decode_str(data, off)
        off += new_off

        self.down_time, new_off = decode_str(data, off)
        off += new_off

        self.loss_damage = decode_short(data, off)
        off += SHORT_OFF

        self.loss_time, new_off = decode_str(data, off)
        off += new_off

        self.move_speed, new_off = decode_str(data, off)
        off += new_off

        self.move_speed_angry, new_off = decode_str(data, off)
        off += new_off

        self.rot_speed, new_off = decode_str(data, off)
        off += new_off

        self.rot_speed_angry, new_off = decode_str(data, off)
        off += new_off

        self.range_min, new_off = decode_str(data, off)
        off += new_off

        self.range_max, new_off = decode_str(data, off)
        off += new_off

        self.range_min_angry, new_off = decode_str(data, off)
        off += new_off

        self.range_max_angry, new_off = decode_str(data, off)
        off += new_off

        self.back_step_speed, new_off = decode_str(data, off)
        off += new_off

        self.back_step_speed_angry, new_off = decode_str(data, off)
        off += new_off

        self.back_step_cool_time, new_off = decode_str(data, off)
        off += new_off

        self.monster_type = decode_short(data, off)
        off += SHORT_OFF

        self.monster_type_angry = decode_short(data, off)
        off += SHORT_OFF

        self.vs_boss_type = decode_short(data, off)
        off += SHORT_OFF

        self.boss_camera_height, new_off = decode_str(data, off)
        off += new_off

        self.boss_camera_near_distance, new_off = decode_str(data, off)
        off += new_off

        self.boss_camera_far_distance, new_off = decode_str(data, off)
        off += new_off

        self.boss_camera_near_range, new_off = decode_str(data, off)
        off += new_off

        self.boss_camera_far_range, new_off = decode_str(data, off)
        off += new_off

        self.search_range, new_off = decode_str(data, off)
        off += new_off

        self.search_angle, new_off = decode_str(data, off)
        off += new_off

        self.lost_range, new_off = decode_str(data, off)
        off += new_off

        self.home_range, new_off = decode_str(data, off)
        off += new_off

        self.roar_id, new_off = decode_str(data, off)
        off += new_off

        self.auto_attack_range, new_off = decode_str(data, off)
        off += new_off

        self.auto_attack_interval, new_off = decode_str(data, off)
        off += new_off

        self.find_priority = decode_short(data, off)
        off += SHORT_OFF

        self.find_range_min = decode_short(data, off)
        off += SHORT_OFF

        self.find_range_max = decode_short(data, off)
        off += SHORT_OFF

        self.leave_range = decode_short(data, off)
        off += SHORT_OFF

        self.show_arrow = decode_byte(data, off)
        off += BYTE_OFF

        self.find_id, new_off = decode_str(data, off)
        off += new_off

        self.leave_id, new_off = decode_str(data, off)
        off += new_off

        self.defeat_id, new_off = decode_str(data, off)
        off += new_off

        self.warfare_id, new_off = decode_str(data, off)
        off += new_off

        self.angry_id, new_off = decode_str(data, off)
        off += new_off

        self.bad_state_bone, new_off = decode_str(data, off)
        off += new_off

        self.bad_state_offset_x, new_off = decode_str(data, off)
        off += new_off

        self.bad_state_offset_y, new_off = decode_str(data, off)
        off += new_off

        self.bad_state_offset_z, new_off = decode_str(data, off)
        off += new_off

        self.drop_offset_y, new_off = decode_str(data, off)
        off += new_off

        self.col_drop_percentage, new_off = decode_str(data, off)
        off += new_off

        self.col_drop_amount = decode_short(data, off)
        off += SHORT_OFF

        self.vp_drop_percentage, new_off = decode_str(data, off)
        off += new_off

        self.vp_drop_amount = decode_short(data, off)
        off += SHORT_OFF

        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_league_point = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "UnitData":
        ret = cls(b"\x00" * 99, 0)
        ret.unit_id = data['UnitId']
        ret.name = data['Name']
        ret.prefab = data['Prefab']
        ret.animator = data['Animator']
        ret.collision = data['Collision']
        ret.radius = data['Radius']
        ret.child_unit_id = data['ChildUnitId']
        ret.stage_start_prefab = data['StageStartPrefab']
        ret.stage_start_y = data['StageStartY']
        ret.stage_start_z = data['StageStartZ']
        ret.stage_touch_y = data['StageTouchY']
        ret.stage_touch_z = data['StageTouchZ']
        ret.playable = data['Playable']
        ret.monster = data['Monster']
        ret.gimmick = data['Gimmick']
        ret.anger = data['Anger']
        ret.commander = data['Commander']
        ret.isolated = data['Isolated']
        ret.base_behaviour = data['BaseBehaviour']
        ret.sound_behaviour = data['SoundBehaviour']
        ret.weapon_type = data['WeaponType']
        ret.poison_time_coef = data['PoisonTimeCoef']
        ret.paralysis_time_coef = data['ParalysisTimeCoef']
        ret.sealed_time_coef = data['SealedTimeCoef']
        ret.question_time_coef = data['QuestionTimeCoef']
        ret.blue_rose_time_coef = data['BlueRoseTimeCoef']
        ret.charm_time_coef = data['CharmTimeCoef']
        ret.burning_time_coef = data['BurningTimeCoef']
        ret.invalid_quake = data['InvalidQuake']
        ret.guard_coef = data['GuardCoef']
        ret.just_guard_time = data['JustGuardTime']
        ret.flip_hp = data['FlipHp']
        ret.down_hp = data['DownHp']
        ret.flip_recover_time = data['FlipRecoverTime']
        ret.down_recover_time = data['DownRecoverTime']
        ret.down_time = data['DownTime']
        ret.loss_damage = data['LossDamage']
        ret.loss_time = data['LossTime']
        ret.move_speed = data['MoveSpeed']
        ret.move_speed_angry = data['MoveSpeedAngry']
        ret.rot_speed = data['RotSpeed']
        ret.rot_speed_angry = data['RotSpeedAngry']
        ret.range_min = data['RangeMin']
        ret.range_max = data['RangeMax']
        ret.range_min_angry = data['RangeMinAngry']
        ret.range_max_angry = data['RangeMaxAngry']
        ret.back_step_speed = data['BackStepSpeed']
        ret.back_step_speed_angry = data['BackStepSpeedAngry']
        ret.back_step_cool_time = data['BackStepCoolTime']
        ret.monster_type = data['MonsterType']
        ret.monster_type_angry = data['MonsterTypeAngry']
        ret.vs_boss_type = data['VsBossType']
        ret.boss_camera_height = data['BossCameraHeight']
        ret.boss_camera_near_distance = data['BossCameraNearDistance']
        ret.boss_camera_far_distance = data['BossCameraFarDistance']
        ret.boss_camera_near_range = data['BossCameraNearRange']
        ret.boss_camera_far_range = data['BossCameraFarRange']
        ret.search_range = data['SearchRange']
        ret.search_angle = data['SearchAngle']
        ret.lost_range = data['LostRange']
        ret.home_range = data['HomeRange']
        ret.roar_id = data['RoarId']
        ret.auto_attack_range = data['AutoAttackRange']
        ret.auto_attack_interval = data['AutoAttackInterval']
        ret.find_priority = data['FindPriority']
        ret.find_range_min = data['FindRangeMin']
        ret.find_range_max = data['FindRangeMax']
        ret.leave_range = data['LeaveRange']
        ret.show_arrow = data['ShowArrow']
        ret.find_id = data['FindId']
        ret.leave_id = data['LeaveId']
        ret.defeat_id = data['DefeatId']
        ret.warfare_id = data['WarfareId']
        ret.angry_id = data['AngryId']
        ret.bad_state_bone = data['BadStateBone']
        ret.bad_state_offset_x = data['BadStateOffsetX']
        ret.bad_state_offset_y = data['BadStateOffsetY']
        ret.bad_state_offset_z = data['BadStateOffsetZ']
        ret.drop_offset_y = data['DropOffsetY']
        ret.col_drop_percentage = data['ColDropPercentage']
        ret.col_drop_amount = data['ColDropAmount']
        ret.vp_drop_percentage = data['VpDropPercentage']
        ret.vp_drop_amount = data['VpDropAmount']
        ret.enemy_kind_id = data['EnemyKindId']
        ret.defrag_match_league_point = data['DefragMatchLeaguePoint']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unit_id) \
        + encode_str(self.name) \
        + encode_str(self.prefab) \
        + encode_str(self.animator) \
        + encode_str(self.collision) \
        + encode_str(self.radius) \
        + encode_int(self.child_unit_id) \
        + encode_str(self.stage_start_prefab) \
        + encode_str(self.stage_start_y) \
        + encode_str(self.stage_start_z) \
        + encode_str(self.stage_touch_y) \
        + encode_str(self.stage_touch_z) \
        + encode_byte(self.playable) \
        + encode_byte(self.monster) \
        + encode_byte(self.gimmick) \
        + encode_byte(self.anger) \
        + encode_byte(self.commander) \
        + encode_byte(self.isolated) \
        + encode_str(self.base_behaviour) \
        + encode_str(self.sound_behaviour) \
        + encode_int(self.weapon_type) \
        + encode_str(self.poison_time_coef) \
        + encode_str(self.paralysis_time_coef) \
        + encode_str(self.sealed_time_coef) \
        + encode_str(self.question_time_coef) \
        + encode_str(self.blue_rose_time_coef) \
        + encode_str(self.charm_time_coef) \
        + encode_str(self.burning_time_coef) \
        + encode_byte(self.invalid_quake) \
        + encode_str(self.guard_coef) \
        + encode_str(self.just_guard_time) \
        + encode_short(self.flip_hp) \
        + encode_short(self.down_hp) \
        + encode_str(self.flip_recover_time) \
        + encode_str(self.down_recover_time) \
        + encode_str(self.down_time) \
        + encode_short(self.loss_damage) \
        + encode_str(self.loss_time) \
        + encode_str(self.move_speed) \
        + encode_str(self.move_speed_angry) \
        + encode_str(self.rot_speed) \
        + encode_str(self.rot_speed_angry) \
        + encode_str(self.range_min) \
        + encode_str(self.range_max) \
        + encode_str(self.range_min_angry) \
        + encode_str(self.range_max_angry) \
        + encode_str(self.back_step_speed) \
        + encode_str(self.back_step_speed_angry) \
        + encode_str(self.back_step_cool_time) \
        + encode_short(self.monster_type) \
        + encode_short(self.monster_type_angry) \
        + encode_short(self.vs_boss_type) \
        + encode_str(self.boss_camera_height) \
        + encode_str(self.boss_camera_near_distance) \
        + encode_str(self.boss_camera_far_distance) \
        + encode_str(self.boss_camera_near_range) \
        + encode_str(self.boss_camera_far_range) \
        + encode_str(self.search_range) \
        + encode_str(self.search_angle) \
        + encode_str(self.lost_range) \
        + encode_str(self.home_range) \
        + encode_str(self.roar_id) \
        + encode_str(self.auto_attack_range) \
        + encode_str(self.auto_attack_interval) \
        + encode_short(self.find_priority) \
        + encode_short(self.find_range_min) \
        + encode_short(self.find_range_max) \
        + encode_short(self.leave_range) \
        + encode_byte(self.show_arrow) \
        + encode_str(self.find_id) \
        + encode_str(self.leave_id) \
        + encode_str(self.defeat_id) \
        + encode_str(self.warfare_id) \
        + encode_str(self.angry_id) \
        + encode_str(self.bad_state_bone) \
        + encode_str(self.bad_state_offset_x) \
        + encode_str(self.bad_state_offset_y) \
        + encode_str(self.bad_state_offset_z) \
        + encode_str(self.drop_offset_y) \
        + encode_str(self.col_drop_percentage) \
        + encode_short(self.col_drop_amount) \
        + encode_str(self.vp_drop_percentage) \
        + encode_short(self.vp_drop_amount) \
        + encode_int(self.enemy_kind_id) \
        + encode_int(self.defrag_match_league_point)

class UnitGimmickData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unit_gimmick_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.gimmick_type = decode_int(data, off)
        off += INT_OFF

        self.range, new_off = decode_str(data, off)
        off += new_off

        self.crystal_grade = decode_int(data, off)
        off += INT_OFF

        self.col = decode_int(data, off)
        off += INT_OFF

        self.skill_exp = decode_int(data, off)
        off += INT_OFF

        self.heal_rate, new_off = decode_str(data, off)
        off += new_off

        self.gimmick_attack_id = decode_short(data, off)
        off += SHORT_OFF

        self.interval, new_off = decode_str(data, off)
        off += new_off

        self.summon_count = decode_int(data, off)
        off += INT_OFF

        self.effect, new_off = decode_str(data, off)
        off += new_off

        self.effect_bone, new_off = decode_str(data, off)
        off += new_off

        self.effect_x, new_off = decode_str(data, off)
        off += new_off

        self.effect_y, new_off = decode_str(data, off)
        off += new_off

        self.effect_z, new_off = decode_str(data, off)
        off += new_off

        self.se, new_off = decode_str(data, off)
        off += new_off

        self.ground_se, new_off = decode_str(data, off)
        off += new_off

        self.sub_state_idle, new_off = decode_str(data, off)
        off += new_off

        self.sub_state_reaction, new_off = decode_str(data, off)
        off += new_off

        self.sub_state_active, new_off = decode_str(data, off)
        off += new_off

        self.sub_state_break, new_off = decode_str(data, off)
        off += new_off

        self.time_sub_state_break, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "UnitGimmickData":
        ret = cls(b"\x00" * 99, 0)
        ret.unit_gimmick_id = data['UnitGimmickId']
        ret.name = data['Name']
        ret.gimmick_type = data['GimmickType']
        ret.range = data['Range']
        ret.crystal_grade = data['CrystalGrade']
        ret.col = data['Col']
        ret.skill_exp = data['SkillExp']
        ret.heal_rate = data['HealRate']
        ret.gimmick_attack_id = data['GimmickAttackId']
        ret.interval = data['Interval']
        ret.summon_count = data['SummonCount']
        ret.effect = data['Effect']
        ret.effect_bone = data['EffectBone']
        ret.effect_x = data['EffectX']
        ret.effect_y = data['EffectY']
        ret.effect_z = data['EffectZ']
        ret.se = data['Se']
        ret.ground_se = data['GroundSe']
        ret.sub_state_idle = data['SubStateIdle']
        ret.sub_state_reaction = data['SubStateReaction']
        ret.sub_state_active = data['SubStateActive']
        ret.sub_state_break = data['SubStateBreak']
        ret.time_sub_state_break = data['TimeSubStateBreak']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unit_gimmick_id) \
        + encode_str(self.name) \
        + encode_int(self.gimmick_type) \
        + encode_str(self.range) \
        + encode_int(self.crystal_grade) \
        + encode_int(self.col) \
        + encode_int(self.skill_exp) \
        + encode_str(self.heal_rate) \
        + encode_short(self.gimmick_attack_id) \
        + encode_str(self.interval) \
        + encode_int(self.summon_count) \
        + encode_str(self.effect) \
        + encode_str(self.effect_bone) \
        + encode_str(self.effect_x) \
        + encode_str(self.effect_y) \
        + encode_str(self.effect_z) \
        + encode_str(self.se) \
        + encode_str(self.ground_se) \
        + encode_str(self.sub_state_idle) \
        + encode_str(self.sub_state_reaction) \
        + encode_str(self.sub_state_active) \
        + encode_str(self.sub_state_break) \
        + encode_str(self.time_sub_state_break)

class UnitCollisionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unit_collision_id = decode_int(data, off)
        off += INT_OFF

        self.keyword, new_off = decode_str(data, off)
        off += new_off

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.bone, new_off = decode_str(data, off)
        off += new_off

        self.usually = decode_byte(data, off)
        off += BYTE_OFF

        self.angry = decode_byte(data, off)
        off += BYTE_OFF

        self.type_index = decode_short(data, off)
        off += SHORT_OFF

        self.begin_x, new_off = decode_str(data, off)
        off += new_off

        self.begin_y, new_off = decode_str(data, off)
        off += new_off

        self.begin_z, new_off = decode_str(data, off)
        off += new_off

        self.end_x, new_off = decode_str(data, off)
        off += new_off

        self.end_y, new_off = decode_str(data, off)
        off += new_off

        self.end_z, new_off = decode_str(data, off)
        off += new_off

        self.radius, new_off = decode_str(data, off)
        off += new_off

        self.slash_coef, new_off = decode_str(data, off)
        off += new_off

        self.strike_coef, new_off = decode_str(data, off)
        off += new_off

        self.thrust_coef, new_off = decode_str(data, off)
        off += new_off

        self.fire_coef, new_off = decode_str(data, off)
        off += new_off

        self.water_coef, new_off = decode_str(data, off)
        off += new_off

        self.air_coef, new_off = decode_str(data, off)
        off += new_off

        self.earth_coef, new_off = decode_str(data, off)
        off += new_off

        self.holy_coef, new_off = decode_str(data, off)
        off += new_off

        self.dark_coef, new_off = decode_str(data, off)
        off += new_off

        self.poison_coef, new_off = decode_str(data, off)
        off += new_off

        self.paralysis_coef, new_off = decode_str(data, off)
        off += new_off

        self.sealed_coef, new_off = decode_str(data, off)
        off += new_off

        self.question_coef, new_off = decode_str(data, off)
        off += new_off

        self.blue_rose_coef, new_off = decode_str(data, off)
        off += new_off

        self.charm_coef, new_off = decode_str(data, off)
        off += new_off

        self.burning_coef, new_off = decode_str(data, off)
        off += new_off

        self.flip_coef, new_off = decode_str(data, off)
        off += new_off

        self.down_coef, new_off = decode_str(data, off)
        off += new_off

        self.knock_back_coef, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "UnitCollisionData":
        ret = cls(b"\x00" * 99, 0)
        ret.unit_collision_id = data['UnitCollisionId']
        ret.keyword = data['Keyword']
        ret.name = data['Name']
        ret.bone = data['Bone']
        ret.usually = data['Usually']
        ret.angry = data['Angry']
        ret.type_index = data['TypeIndex']
        ret.begin_x = data['BeginX']
        ret.begin_y = data['BeginY']
        ret.begin_z = data['BeginZ']
        ret.end_x = data['EndX']
        ret.end_y = data['EndY']
        ret.end_z = data['EndZ']
        ret.radius = data['Radius']
        ret.slash_coef = data['SlashCoef']
        ret.strike_coef = data['StrikeCoef']
        ret.thrust_coef = data['ThrustCoef']
        ret.fire_coef = data['FireCoef']
        ret.water_coef = data['WaterCoef']
        ret.air_coef = data['AirCoef']
        ret.earth_coef = data['EarthCoef']
        ret.holy_coef = data['HolyCoef']
        ret.dark_coef = data['DarkCoef']
        ret.poison_coef = data['PoisonCoef']
        ret.paralysis_coef = data['ParalysisCoef']
        ret.sealed_coef = data['SealedCoef']
        ret.question_coef = data['QuestionCoef']
        ret.blue_rose_coef = data['BlueRoseCoef']
        ret.charm_coef = data['CharmCoef']
        ret.burning_coef = data['BurningCoef']
        ret.flip_coef = data['FlipCoef']
        ret.down_coef = data['DownCoef']
        ret.knock_back_coef = data['KnockBackCoef']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unit_collision_id) \
        + encode_str(self.keyword) \
        + encode_str(self.name) \
        + encode_str(self.bone) \
        + encode_byte(self.usually) \
        + encode_byte(self.angry) \
        + encode_short(self.type_index) \
        + encode_str(self.begin_x) \
        + encode_str(self.begin_y) \
        + encode_str(self.begin_z) \
        + encode_str(self.end_x) \
        + encode_str(self.end_y) \
        + encode_str(self.end_z) \
        + encode_str(self.radius) \
        + encode_str(self.slash_coef) \
        + encode_str(self.strike_coef) \
        + encode_str(self.thrust_coef) \
        + encode_str(self.fire_coef) \
        + encode_str(self.water_coef) \
        + encode_str(self.air_coef) \
        + encode_str(self.earth_coef) \
        + encode_str(self.holy_coef) \
        + encode_str(self.dark_coef) \
        + encode_str(self.poison_coef) \
        + encode_str(self.paralysis_coef) \
        + encode_str(self.sealed_coef) \
        + encode_str(self.question_coef) \
        + encode_str(self.blue_rose_coef) \
        + encode_str(self.charm_coef) \
        + encode_str(self.burning_coef) \
        + encode_str(self.flip_coef) \
        + encode_str(self.down_coef) \
        + encode_str(self.knock_back_coef)

class UnitPowerData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.unit_power_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.lv = decode_int(data, off)
        off += INT_OFF

        self.param_hp = decode_int(data, off)
        off += INT_OFF

        self.param_str = decode_int(data, off)
        off += INT_OFF

        self.param_vit = decode_int(data, off)
        off += INT_OFF

        self.param_int = decode_int(data, off)
        off += INT_OFF

        self.exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "UnitPowerData":
        ret = cls(b"\x00" * 99, 0)
        ret.unit_power_id = data['UnitPowerId']
        ret.unit_id = data['UnitId']
        ret.lv = data['Lv']
        ret.param_hp = data['ParamHp']
        ret.param_str = data['ParamStr']
        ret.param_vit = data['ParamVit']
        ret.param_int = data['ParamInt']
        ret.exp = data['Exp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.unit_power_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.lv) \
        + encode_int(self.param_hp) \
        + encode_int(self.param_str) \
        + encode_int(self.param_vit) \
        + encode_int(self.param_int) \
        + encode_int(self.exp)

class GimmickAttackData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gimmick_attack_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.hit_enemy = decode_byte(data, off)
        off += BYTE_OFF

        self.hit_friend = decode_byte(data, off)
        off += BYTE_OFF

        self.attack_coef, new_off = decode_str(data, off)
        off += new_off

        self.heal_coef, new_off = decode_str(data, off)
        off += new_off

        self.flip_damage = decode_short(data, off)
        off += SHORT_OFF

        self.down_damage = decode_short(data, off)
        off += SHORT_OFF

        self.poison_incidence, new_off = decode_str(data, off)
        off += new_off

        self.paralysis_incidence, new_off = decode_str(data, off)
        off += new_off

        self.sealed_incidence, new_off = decode_str(data, off)
        off += new_off

        self.question_incidence, new_off = decode_str(data, off)
        off += new_off

        self.blue_rose_incidence, new_off = decode_str(data, off)
        off += new_off

        self.charm_incidence, new_off = decode_str(data, off)
        off += new_off

        self.burning_incidence, new_off = decode_str(data, off)
        off += new_off

        self.knock_back, new_off = decode_str(data, off)
        off += new_off

        self.knock_back_g, new_off = decode_str(data, off)
        off += new_off

        self.forward_knock_back = decode_byte(data, off)
        off += BYTE_OFF

        self.break_interval, new_off = decode_str(data, off)
        off += new_off

        self.attack_type = decode_short(data, off)
        off += SHORT_OFF

        self.physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.magic_attr = decode_short(data, off)
        off += SHORT_OFF

        self.hit_se, new_off = decode_str(data, off)
        off += new_off

        self.weak_se, new_off = decode_str(data, off)
        off += new_off

        self.resist_se, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GimmickAttackData":
        ret = cls(b"\x00" * 99, 0)
        ret.gimmick_attack_id = data['GimmickAttackId']
        ret.name = data['Name']
        ret.hit_enemy = data['HitEnemy']
        ret.hit_friend = data['HitFriend']
        ret.attack_coef = data['AttackCoef']
        ret.heal_coef = data['HealCoef']
        ret.flip_damage = data['FlipDamage']
        ret.down_damage = data['DownDamage']
        ret.poison_incidence = data['PoisonIncidence']
        ret.paralysis_incidence = data['ParalysisIncidence']
        ret.sealed_incidence = data['SealedIncidence']
        ret.question_incidence = data['QuestionIncidence']
        ret.blue_rose_incidence = data['BlueRoseIncidence']
        ret.charm_incidence = data['CharmIncidence']
        ret.burning_incidence = data['BurningIncidence']
        ret.knock_back = data['KnockBack']
        ret.knock_back_g = data['KnockBackG']
        ret.forward_knock_back = data['ForwardKnockBack']
        ret.break_interval = data['BreakInterval']
        ret.attack_type = data['AttackType']
        ret.physics_attr = data['PhysicsAttr']
        ret.magic_attr = data['MagicAttr']
        ret.hit_se = data['HitSe']
        ret.weak_se = data['WeakSe']
        ret.resist_se = data['ResistSe']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.gimmick_attack_id) \
        + encode_str(self.name) \
        + encode_byte(self.hit_enemy) \
        + encode_byte(self.hit_friend) \
        + encode_str(self.attack_coef) \
        + encode_str(self.heal_coef) \
        + encode_short(self.flip_damage) \
        + encode_short(self.down_damage) \
        + encode_str(self.poison_incidence) \
        + encode_str(self.paralysis_incidence) \
        + encode_str(self.sealed_incidence) \
        + encode_str(self.question_incidence) \
        + encode_str(self.blue_rose_incidence) \
        + encode_str(self.charm_incidence) \
        + encode_str(self.burning_incidence) \
        + encode_str(self.knock_back) \
        + encode_str(self.knock_back_g) \
        + encode_byte(self.forward_knock_back) \
        + encode_str(self.break_interval) \
        + encode_short(self.attack_type) \
        + encode_short(self.physics_attr) \
        + encode_short(self.magic_attr) \
        + encode_str(self.hit_se) \
        + encode_str(self.weak_se) \
        + encode_str(self.resist_se)

class CharaAttackData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chara_attack_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.attack_coef, new_off = decode_str(data, off)
        off += new_off

        self.flip_damage = decode_short(data, off)
        off += SHORT_OFF

        self.down_damage = decode_short(data, off)
        off += SHORT_OFF

        self.poison_incidence, new_off = decode_str(data, off)
        off += new_off

        self.paralysis_incidence, new_off = decode_str(data, off)
        off += new_off

        self.sealed_incidence, new_off = decode_str(data, off)
        off += new_off

        self.question_incidence, new_off = decode_str(data, off)
        off += new_off

        self.blue_rose_incidence, new_off = decode_str(data, off)
        off += new_off

        self.charm_incidence, new_off = decode_str(data, off)
        off += new_off

        self.knock_back, new_off = decode_str(data, off)
        off += new_off

        self.forward_knock_back = decode_byte(data, off)
        off += BYTE_OFF

        self.break_interval, new_off = decode_str(data, off)
        off += new_off

        self.weapon_slot = decode_short(data, off)
        off += SHORT_OFF

        self.attack_type = decode_short(data, off)
        off += SHORT_OFF

        self.physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.magic_attr = decode_short(data, off)
        off += SHORT_OFF

        self.spell_blast = decode_byte(data, off)
        off += BYTE_OFF

        self.hit_se, new_off = decode_str(data, off)
        off += new_off

        self.weak_se, new_off = decode_str(data, off)
        off += new_off

        self.resist_se, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CharaAttackData":
        ret = cls(b"\x00" * 99, 0)
        ret.chara_attack_id = data['CharaAttackId']
        ret.name = data['Name']
        ret.attack_coef = data['AttackCoef']
        ret.flip_damage = data['FlipDamage']
        ret.down_damage = data['DownDamage']
        ret.poison_incidence = data['PoisonIncidence']
        ret.paralysis_incidence = data['ParalysisIncidence']
        ret.sealed_incidence = data['SealedIncidence']
        ret.question_incidence = data['QuestionIncidence']
        ret.blue_rose_incidence = data['BlueRoseIncidence']
        ret.charm_incidence = data['CharmIncidence']
        ret.knock_back = data['KnockBack']
        ret.forward_knock_back = data['ForwardKnockBack']
        ret.break_interval = data['BreakInterval']
        ret.weapon_slot = data['WeaponSlot']
        ret.attack_type = data['AttackType']
        ret.physics_attr = data['PhysicsAttr']
        ret.magic_attr = data['MagicAttr']
        ret.spell_blast = data['SpellBlast']
        ret.hit_se = data['HitSe']
        ret.weak_se = data['WeakSe']
        ret.resist_se = data['ResistSe']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.chara_attack_id) \
        + encode_str(self.name) \
        + encode_str(self.attack_coef) \
        + encode_short(self.flip_damage) \
        + encode_short(self.down_damage) \
        + encode_str(self.poison_incidence) \
        + encode_str(self.paralysis_incidence) \
        + encode_str(self.sealed_incidence) \
        + encode_str(self.question_incidence) \
        + encode_str(self.blue_rose_incidence) \
        + encode_str(self.charm_incidence) \
        + encode_str(self.knock_back) \
        + encode_byte(self.forward_knock_back) \
        + encode_str(self.break_interval) \
        + encode_short(self.weapon_slot) \
        + encode_short(self.attack_type) \
        + encode_short(self.physics_attr) \
        + encode_short(self.magic_attr) \
        + encode_byte(self.spell_blast) \
        + encode_str(self.hit_se) \
        + encode_str(self.weak_se) \
        + encode_str(self.resist_se)

class BossAttackData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.boss_attack_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.attack_coef, new_off = decode_str(data, off)
        off += new_off

        self.flip_damage = decode_short(data, off)
        off += SHORT_OFF

        self.down_damage = decode_short(data, off)
        off += SHORT_OFF

        self.poison_incidence, new_off = decode_str(data, off)
        off += new_off

        self.sealed_incidence, new_off = decode_str(data, off)
        off += new_off

        self.question_incidence, new_off = decode_str(data, off)
        off += new_off

        self.reduce_max_hp_incidence, new_off = decode_str(data, off)
        off += new_off

        self.burning_incidence, new_off = decode_str(data, off)
        off += new_off

        self.quake = decode_byte(data, off)
        off += BYTE_OFF

        self.can_parry = decode_byte(data, off)
        off += BYTE_OFF

        self.knock_back, new_off = decode_str(data, off)
        off += new_off

        self.knock_back_g, new_off = decode_str(data, off)
        off += new_off

        self.forward_knock_back = decode_byte(data, off)
        off += BYTE_OFF

        self.attack_type = decode_short(data, off)
        off += SHORT_OFF

        self.physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.magic_attr = decode_short(data, off)
        off += SHORT_OFF

        self.spell_blast = decode_byte(data, off)
        off += BYTE_OFF

        self.hit_se, new_off = decode_str(data, off)
        off += new_off

        self.weak_se, new_off = decode_str(data, off)
        off += new_off

        self.resist_se, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BossAttackData":
        ret = cls(b"\x00" * 99, 0)
        ret.boss_attack_id = data['BossAttackId']
        ret.name = data['Name']
        ret.attack_coef = data['AttackCoef']
        ret.flip_damage = data['FlipDamage']
        ret.down_damage = data['DownDamage']
        ret.poison_incidence = data['PoisonIncidence']
        ret.sealed_incidence = data['SealedIncidence']
        ret.question_incidence = data['QuestionIncidence']
        ret.reduce_max_hp_incidence = data['ReduceMaxHpIncidence']
        ret.burning_incidence = data['BurningIncidence']
        ret.quake = data['Quake']
        ret.can_parry = data['CanParry']
        ret.knock_back = data['KnockBack']
        ret.knock_back_g = data['KnockBackG']
        ret.forward_knock_back = data['ForwardKnockBack']
        ret.attack_type = data['AttackType']
        ret.physics_attr = data['PhysicsAttr']
        ret.magic_attr = data['MagicAttr']
        ret.spell_blast = data['SpellBlast']
        ret.hit_se = data['HitSe']
        ret.weak_se = data['WeakSe']
        ret.resist_se = data['ResistSe']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.boss_attack_id) \
        + encode_str(self.name) \
        + encode_str(self.attack_coef) \
        + encode_short(self.flip_damage) \
        + encode_short(self.down_damage) \
        + encode_str(self.poison_incidence) \
        + encode_str(self.sealed_incidence) \
        + encode_str(self.question_incidence) \
        + encode_str(self.reduce_max_hp_incidence) \
        + encode_str(self.burning_incidence) \
        + encode_byte(self.quake) \
        + encode_byte(self.can_parry) \
        + encode_str(self.knock_back) \
        + encode_str(self.knock_back_g) \
        + encode_byte(self.forward_knock_back) \
        + encode_short(self.attack_type) \
        + encode_short(self.physics_attr) \
        + encode_short(self.magic_attr) \
        + encode_byte(self.spell_blast) \
        + encode_str(self.hit_se) \
        + encode_str(self.weak_se) \
        + encode_str(self.resist_se)

class MonsterAttackData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.monster_attack_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.attack_coef, new_off = decode_str(data, off)
        off += new_off

        self.flip_damage = decode_short(data, off)
        off += SHORT_OFF

        self.down_damage = decode_short(data, off)
        off += SHORT_OFF

        self.poison_incidence, new_off = decode_str(data, off)
        off += new_off

        self.sealed_incidence, new_off = decode_str(data, off)
        off += new_off

        self.question_incidence, new_off = decode_str(data, off)
        off += new_off

        self.reduce_max_hp_incidence, new_off = decode_str(data, off)
        off += new_off

        self.burning_incidence, new_off = decode_str(data, off)
        off += new_off

        self.quake = decode_byte(data, off)
        off += BYTE_OFF

        self.can_parry = decode_byte(data, off)
        off += BYTE_OFF

        self.knock_back, new_off = decode_str(data, off)
        off += new_off

        self.knock_back_g, new_off = decode_str(data, off)
        off += new_off

        self.forward_knock_back = decode_byte(data, off)
        off += BYTE_OFF

        self.attack_type = decode_short(data, off)
        off += SHORT_OFF

        self.physics_attr = decode_short(data, off)
        off += SHORT_OFF

        self.magic_attr = decode_short(data, off)
        off += SHORT_OFF

        self.spell_blast = decode_byte(data, off)
        off += BYTE_OFF

        self.hit_se, new_off = decode_str(data, off)
        off += new_off

        self.weak_se, new_off = decode_str(data, off)
        off += new_off

        self.resist_se, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MonsterAttackData":
        ret = cls(b"\x00" * 99, 0)
        ret.monster_attack_id = data['MonsterAttackId']
        ret.name = data['Name']
        ret.attack_coef = data['AttackCoef']
        ret.flip_damage = data['FlipDamage']
        ret.down_damage = data['DownDamage']
        ret.poison_incidence = data['PoisonIncidence']
        ret.sealed_incidence = data['SealedIncidence']
        ret.question_incidence = data['QuestionIncidence']
        ret.reduce_max_hp_incidence = data['ReduceMaxHpIncidence']
        ret.burning_incidence = data['BurningIncidence']
        ret.quake = data['Quake']
        ret.can_parry = data['CanParry']
        ret.knock_back = data['KnockBack']
        ret.knock_back_g = data['KnockBackG']
        ret.forward_knock_back = data['ForwardKnockBack']
        ret.attack_type = data['AttackType']
        ret.physics_attr = data['PhysicsAttr']
        ret.magic_attr = data['MagicAttr']
        ret.spell_blast = data['SpellBlast']
        ret.hit_se = data['HitSe']
        ret.weak_se = data['WeakSe']
        ret.resist_se = data['ResistSe']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.monster_attack_id) \
        + encode_str(self.name) \
        + encode_str(self.attack_coef) \
        + encode_short(self.flip_damage) \
        + encode_short(self.down_damage) \
        + encode_str(self.poison_incidence) \
        + encode_str(self.sealed_incidence) \
        + encode_str(self.question_incidence) \
        + encode_str(self.reduce_max_hp_incidence) \
        + encode_str(self.burning_incidence) \
        + encode_byte(self.quake) \
        + encode_byte(self.can_parry) \
        + encode_str(self.knock_back) \
        + encode_str(self.knock_back_g) \
        + encode_byte(self.forward_knock_back) \
        + encode_short(self.attack_type) \
        + encode_short(self.physics_attr) \
        + encode_short(self.magic_attr) \
        + encode_byte(self.spell_blast) \
        + encode_str(self.hit_se) \
        + encode_str(self.weak_se) \
        + encode_str(self.resist_se)

class MonsterActionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.monster_action_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.slot = decode_int(data, off)
        off += INT_OFF

        self.usable_lv = decode_int(data, off)
        off += INT_OFF

        self.use_count = decode_int(data, off)
        off += INT_OFF

        self.not_angry = decode_byte(data, off)
        off += BYTE_OFF

        self.is_angry = decode_byte(data, off)
        off += BYTE_OFF

        self.can_sealed = decode_byte(data, off)
        off += BYTE_OFF

        self.multi_play_only = decode_byte(data, off)
        off += BYTE_OFF

        self.angle_min, new_off = decode_str(data, off)
        off += new_off

        self.angle_max, new_off = decode_str(data, off)
        off += new_off

        self.range_min, new_off = decode_str(data, off)
        off += new_off

        self.range_max, new_off = decode_str(data, off)
        off += new_off

        self.attack_time, new_off = decode_str(data, off)
        off += new_off

        self.delay_time, new_off = decode_str(data, off)
        off += new_off

        self.cool_time, new_off = decode_str(data, off)
        off += new_off

        self.state, new_off = decode_str(data, off)
        off += new_off

        self.sub_state, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MonsterActionData":
        ret = cls(b"\x00" * 99, 0)
        ret.monster_action_id = data['MonsterActionId']
        ret.name = data['Name']
        ret.unit_id = data['UnitId']
        ret.slot = data['Slot']
        ret.usable_lv = data['UsableLv']
        ret.use_count = data['UseCount']
        ret.not_angry = data['NotAngry']
        ret.is_angry = data['IsAngry']
        ret.can_sealed = data['CanSealed']
        ret.multi_play_only = data['MultiPlayOnly']
        ret.angle_min = data['AngleMin']
        ret.angle_max = data['AngleMax']
        ret.range_min = data['RangeMin']
        ret.range_max = data['RangeMax']
        ret.attack_time = data['AttackTime']
        ret.delay_time = data['DelayTime']
        ret.cool_time = data['CoolTime']
        ret.state = data['State']
        ret.sub_state = data['SubState']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.monster_action_id) \
        + encode_str(self.name) \
        + encode_int(self.unit_id) \
        + encode_int(self.slot) \
        + encode_int(self.usable_lv) \
        + encode_int(self.use_count) \
        + encode_byte(self.not_angry) \
        + encode_byte(self.is_angry) \
        + encode_byte(self.can_sealed) \
        + encode_byte(self.multi_play_only) \
        + encode_str(self.angle_min) \
        + encode_str(self.angle_max) \
        + encode_str(self.range_min) \
        + encode_str(self.range_max) \
        + encode_str(self.attack_time) \
        + encode_str(self.delay_time) \
        + encode_str(self.cool_time) \
        + encode_str(self.state) \
        + encode_str(self.sub_state)

class PropertyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.property_id = decode_int(data, off)
        off += INT_OFF

        self.property_target_type = decode_short(data, off)
        off += SHORT_OFF

        self.property_name, new_off = decode_str(data, off)
        off += new_off

        self.property_name_format, new_off = decode_str(data, off)
        off += new_off

        self.property_type_id = decode_int(data, off)
        off += INT_OFF

        self.value1_min = decode_int(data, off)
        off += INT_OFF

        self.value1_max = decode_int(data, off)
        off += INT_OFF

        self.value2_min = decode_int(data, off)
        off += INT_OFF

        self.value2_max = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PropertyData":
        ret = cls(b"\x00" * 99, 0)
        ret.property_id = data['PropertyId']
        ret.property_target_type = data['PropertyTargetType']
        ret.property_name = data['PropertyName']
        ret.property_name_format = data['PropertyNameFormat']
        ret.property_type_id = data['PropertyTypeId']
        ret.value1_min = data['Value1Min']
        ret.value1_max = data['Value1Max']
        ret.value2_min = data['Value2Min']
        ret.value2_max = data['Value2Max']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.property_id) \
        + encode_short(self.property_target_type) \
        + encode_str(self.property_name) \
        + encode_str(self.property_name_format) \
        + encode_int(self.property_type_id) \
        + encode_int(self.value1_min) \
        + encode_int(self.value1_max) \
        + encode_int(self.value2_min) \
        + encode_int(self.value2_max)

class PropertyTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.property_table_id = decode_int(data, off)
        off += INT_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.property_id = decode_int(data, off)
        off += INT_OFF

        self.value1_min = decode_int(data, off)
        off += INT_OFF

        self.value1_max = decode_int(data, off)
        off += INT_OFF

        self.value2_min = decode_int(data, off)
        off += INT_OFF

        self.value2_max = decode_int(data, off)
        off += INT_OFF

        self.rate = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PropertyTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.property_table_id = data['PropertyTableId']
        ret.property_table_sub_id = data['PropertyTableSubId']
        ret.property_id = data['PropertyId']
        ret.value1_min = data['Value1Min']
        ret.value1_max = data['Value1Max']
        ret.value2_min = data['Value2Min']
        ret.value2_max = data['Value2Max']
        ret.rate = data['Rate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.property_table_id) \
        + encode_int(self.property_table_sub_id) \
        + encode_int(self.property_id) \
        + encode_int(self.value1_min) \
        + encode_int(self.value1_max) \
        + encode_int(self.value2_min) \
        + encode_int(self.value2_max) \
        + encode_int(self.rate)

class PropertyTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.property_type_id = decode_int(data, off)
        off += INT_OFF

        self.property_type_name, new_off = decode_str(data, off)
        off += new_off

        self.physics_attr = decode_int(data, off)
        off += INT_OFF

        self.magic_attr = decode_int(data, off)
        off += INT_OFF

        self.permission_same_id_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.auto_equip_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PropertyTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.property_type_id = data['PropertyTypeId']
        ret.property_type_name = data['PropertyTypeName']
        ret.physics_attr = data['PhysicsAttr']
        ret.magic_attr = data['MagicAttr']
        ret.permission_same_id_flag = data['PermissionSameIdFlag']
        ret.auto_equip_flag = data['AutoEquipFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.property_type_id) \
        + encode_str(self.property_type_name) \
        + encode_int(self.physics_attr) \
        + encode_int(self.magic_attr) \
        + encode_byte(self.permission_same_id_flag) \
        + encode_byte(self.auto_equip_flag)

class SkillData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.weapon_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.attack = decode_byte(data, off)
        off += BYTE_OFF

        self.passive = decode_byte(data, off)
        off += BYTE_OFF

        self.pet = decode_byte(data, off)
        off += BYTE_OFF

        self.level = decode_short(data, off)
        off += SHORT_OFF

        self.skill_condition = decode_short(data, off)
        off += SHORT_OFF

        self.cool_time, new_off = decode_str(data, off)
        off += new_off

        self.sword_color_r, new_off = decode_str(data, off)
        off += new_off

        self.sword_color_g, new_off = decode_str(data, off)
        off += new_off

        self.sword_color_b, new_off = decode_str(data, off)
        off += new_off

        self.motion_index = decode_short(data, off)
        off += SHORT_OFF

        self.state, new_off = decode_str(data, off)
        off += new_off

        self.sub_state, new_off = decode_str(data, off)
        off += new_off

        self.skill_icon, new_off = decode_str(data, off)
        off += new_off

        self.friend_skill_icon, new_off = decode_str(data, off)
        off += new_off

        self.info_text, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SkillData":
        ret = cls(b"\x00" * 99, 0)
        ret.skill_id = data['SkillId']
        ret.weapon_type_id = data['WeaponTypeId']
        ret.name = data['Name']
        ret.attack = data['Attack']
        ret.passive = data['Passive']
        ret.pet = data['Pet']
        ret.level = data['Level']
        ret.skill_condition = data['SkillCondition']
        ret.cool_time = data['CoolTime']
        ret.sword_color_r = data['SwordColorR']
        ret.sword_color_g = data['SwordColorG']
        ret.sword_color_b = data['SwordColorB']
        ret.motion_index = data['MotionIndex']
        ret.state = data['State']
        ret.sub_state = data['SubState']
        ret.skill_icon = data['SkillIcon']
        ret.friend_skill_icon = data['FriendSkillIcon']
        ret.info_text = data['InfoText']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.skill_id) \
        + encode_short(self.weapon_type_id) \
        + encode_str(self.name) \
        + encode_byte(self.attack) \
        + encode_byte(self.passive) \
        + encode_byte(self.pet) \
        + encode_short(self.level) \
        + encode_short(self.skill_condition) \
        + encode_str(self.cool_time) \
        + encode_str(self.sword_color_r) \
        + encode_str(self.sword_color_g) \
        + encode_str(self.sword_color_b) \
        + encode_short(self.motion_index) \
        + encode_str(self.state) \
        + encode_str(self.sub_state) \
        + encode_str(self.skill_icon) \
        + encode_str(self.friend_skill_icon) \
        + encode_str(self.info_text)

class SkillTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.skill_table_id = decode_int(data, off)
        off += INT_OFF

        self.skill_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.level = decode_int(data, off)
        off += INT_OFF

        self.awakening_id = decode_int(data, off)
        off += INT_OFF

        self.skill_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SkillTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.skill_table_id = data['SkillTableId']
        ret.skill_table_sub_id = data['SkillTableSubId']
        ret.level = data['Level']
        ret.awakening_id = data['AwakeningId']
        ret.skill_id = data['SkillId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.skill_table_id) \
        + encode_int(self.skill_table_sub_id) \
        + encode_int(self.level) \
        + encode_int(self.awakening_id) \
        + encode_int(self.skill_id)

class SkillLevelData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.skill_level_id = decode_short(data, off)
        off += SHORT_OFF

        self.exp = decode_int(data, off)
        off += INT_OFF

        self.exp_total = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SkillLevelData":
        ret = cls(b"\x00" * 99, 0)
        ret.skill_level_id = data['SkillLevelId']
        ret.exp = data['Exp']
        ret.exp_total = data['ExpTotal']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.skill_level_id) \
        + encode_int(self.exp) \
        + encode_int(self.exp_total)

class AwakeningData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.awakening_id = decode_short(data, off)
        off += SHORT_OFF

        self.total_exp = decode_int(data, off)
        off += INT_OFF

        self.bonus_hero_log, new_off = decode_str(data, off)
        off += new_off

        self.bonus_weapon, new_off = decode_str(data, off)
        off += new_off

        self.bonus_armor, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AwakeningData":
        ret = cls(b"\x00" * 99, 0)
        ret.awakening_id = data['AwakeningId']
        ret.total_exp = data['TotalExp']
        ret.bonus_hero_log = data['BonusHeroLog']
        ret.bonus_weapon = data['BonusWeapon']
        ret.bonus_armor = data['BonusArmor']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.awakening_id) \
        + encode_int(self.total_exp) \
        + encode_str(self.bonus_hero_log) \
        + encode_str(self.bonus_weapon) \
        + encode_str(self.bonus_armor)

class SynchroSkillData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.synchro_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.name_in_skill_cutin, new_off = decode_str(data, off)
        off += new_off

        self.sub_state, new_off = decode_str(data, off)
        off += new_off

        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.icon_file_path, new_off = decode_str(data, off)
        off += new_off

        self.info_text, new_off = decode_str(data, off)
        off += new_off

        self.se_name, new_off = decode_str(data, off)
        off += new_off

        self.voice_id, new_off = decode_str(data, off)
        off += new_off

        self.delay_time = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SynchroSkillData":
        ret = cls(b"\x00" * 99, 0)
        ret.synchro_skill_id = data['SynchroSkillId']
        ret.name = data['Name']
        ret.name_in_skill_cutin = data['NameInSkillCutin']
        ret.sub_state = data['SubState']
        ret.chara_id = data['CharaId']
        ret.icon_file_path = data['IconFilePath']
        ret.info_text = data['InfoText']
        ret.se_name = data['SeName']
        ret.voice_id = data['VoiceId']
        ret.delay_time = data['DelayTime']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.synchro_skill_id) \
        + encode_str(self.name) \
        + encode_str(self.name_in_skill_cutin) \
        + encode_str(self.sub_state) \
        + encode_short(self.chara_id) \
        + encode_str(self.icon_file_path) \
        + encode_str(self.info_text) \
        + encode_str(self.se_name) \
        + encode_str(self.voice_id) \
        + encode_int(self.delay_time)

class SoundSkillCutInVoiceData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.sound_skill_cut_in_voice_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_id = decode_int(data, off)
        off += INT_OFF

        self.chara_id = decode_int(data, off)
        off += INT_OFF

        self.record_id, new_off = decode_str(data, off)
        off += new_off

        self.que_name, new_off = decode_str(data, off)
        off += new_off

        self.delay_time = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SoundSkillCutInVoiceData":
        ret = cls(b"\x00" * 99, 0)
        ret.sound_skill_cut_in_voice_id = data['SoundSkillCutInVoiceId']
        ret.skill_id = data['SkillId']
        ret.chara_id = data['CharaId']
        ret.record_id = data['RecordId']
        ret.que_name = data['QueName']
        ret.delay_time = data['DelayTime']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.sound_skill_cut_in_voice_id) \
        + encode_int(self.skill_id) \
        + encode_int(self.chara_id) \
        + encode_str(self.record_id) \
        + encode_str(self.que_name) \
        + encode_int(self.delay_time)

class QuestSceneData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_scene_id = decode_short(data, off)
        off += SHORT_OFF

        self.sort_no = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.map_data, new_off = decode_str(data, off)
        off += new_off

        self.unit_data, new_off = decode_str(data, off)
        off += new_off

        self.demo_map, new_off = decode_str(data, off)
        off += new_off

        self.bgm_basic, new_off = decode_str(data, off)
        off += new_off

        self.bgm_boss, new_off = decode_str(data, off)
        off += new_off

        self.tutorial = decode_byte(data, off)
        off += BYTE_OFF

        self.chara_comment_id_0 = decode_int(data, off)
        off += INT_OFF

        self.chara_comment_id_1 = decode_int(data, off)
        off += INT_OFF

        self.chara_comment_id_2 = decode_int(data, off)
        off += INT_OFF

        self.chara_comment_id_3 = decode_int(data, off)
        off += INT_OFF

        self.chara_comment_id_4 = decode_int(data, off)
        off += INT_OFF

        self.col_rate, new_off = decode_str(data, off)
        off += new_off

        self.limit_default = decode_int(data, off)
        off += INT_OFF

        self.limit_time_dec, new_off = decode_str(data, off)
        off += new_off

        self.limit_chara_dec, new_off = decode_str(data, off)
        off += new_off

        self.limit_resurrection = decode_int(data, off)
        off += INT_OFF

        self.mission_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.mission_enemy_lv_limit = decode_short(data, off)
        off += SHORT_OFF

        self.reward_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.player_trace_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.success_player_exp = decode_int(data, off)
        off += INT_OFF

        self.failed_player_exp = decode_int(data, off)
        off += INT_OFF

        self.greed_spawn_wait_count = decode_int(data, off)
        off += INT_OFF

        self.honey_spawn_wait_count = decode_int(data, off)
        off += INT_OFF

        self.menu_display_enemy_set_id = decode_int(data, off)
        off += INT_OFF

        self.stage_filepath, new_off = decode_str(data, off)
        off += new_off

        self.rarity_up_chance_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_mob_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_mob_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_leader_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_leader_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_boss_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_boss_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.pair_exp_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_mob_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_mob_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_leader_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_leader_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_boss_hp_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_boss_atk_rate, new_off = decode_str(data, off)
        off += new_off

        self.trio_exp_rate, new_off = decode_str(data, off)
        off += new_off

        self.single_reward_vp = decode_int(data, off)
        off += INT_OFF

        self.pair_reward_vp = decode_int(data, off)
        off += INT_OFF

        self.trio_reward_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSceneData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_scene_id = data['QuestSceneId']
        ret.sort_no = data['SortNo']
        ret.name = data['Name']
        ret.map_data = data['MapData']
        ret.unit_data = data['UnitData']
        ret.demo_map = data['DemoMap']
        ret.bgm_basic = data['BgmBasic']
        ret.bgm_boss = data['BgmBoss']
        ret.tutorial = data['Tutorial']
        ret.chara_comment_id_0 = data['CharaCommentId0']
        ret.chara_comment_id_1 = data['CharaCommentId1']
        ret.chara_comment_id_2 = data['CharaCommentId2']
        ret.chara_comment_id_3 = data['CharaCommentId3']
        ret.chara_comment_id_4 = data['CharaCommentId4']
        ret.col_rate = data['ColRate']
        ret.limit_default = data['LimitDefault']
        ret.limit_time_dec = data['LimitTimeDec']
        ret.limit_chara_dec = data['LimitCharaDec']
        ret.limit_resurrection = data['LimitResurrection']
        ret.mission_table_sub_id = data['MissionTableSubId']
        ret.mission_enemy_lv_limit = data['MissionEnemyLvLimit']
        ret.reward_table_sub_id = data['RewardTableSubId']
        ret.player_trace_table_sub_id = data['PlayerTraceTableSubId']
        ret.success_player_exp = data['SuccessPlayerExp']
        ret.failed_player_exp = data['FailedPlayerExp']
        ret.greed_spawn_wait_count = data['GreedSpawnWaitCount']
        ret.honey_spawn_wait_count = data['HoneySpawnWaitCount']
        ret.menu_display_enemy_set_id = data['MenuDisplayEnemySetId']
        ret.stage_filepath = data['StageFilepath']
        ret.rarity_up_chance_rate = data['RarityUpChanceRate']
        ret.pair_mob_hp_rate = data['PairMobHpRate']
        ret.pair_mob_atk_rate = data['PairMobAtkRate']
        ret.pair_leader_hp_rate = data['PairLeaderHpRate']
        ret.pair_leader_atk_rate = data['PairLeaderAtkRate']
        ret.pair_boss_hp_rate = data['PairBossHpRate']
        ret.pair_boss_atk_rate = data['PairBossAtkRate']
        ret.pair_exp_rate = data['PairExpRate']
        ret.trio_mob_hp_rate = data['TrioMobHpRate']
        ret.trio_mob_atk_rate = data['TrioMobAtkRate']
        ret.trio_leader_hp_rate = data['TrioLeaderHpRate']
        ret.trio_leader_atk_rate = data['TrioLeaderAtkRate']
        ret.trio_boss_hp_rate = data['TrioBossHpRate']
        ret.trio_boss_atk_rate = data['TrioBossAtkRate']
        ret.trio_exp_rate = data['TrioExpRate']
        ret.single_reward_vp = data['SingleRewardVp']
        ret.pair_reward_vp = data['PairRewardVp']
        ret.trio_reward_vp = data['TrioRewardVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.quest_scene_id) \
        + encode_short(self.sort_no) \
        + encode_str(self.name) \
        + encode_str(self.map_data) \
        + encode_str(self.unit_data) \
        + encode_str(self.demo_map) \
        + encode_str(self.bgm_basic) \
        + encode_str(self.bgm_boss) \
        + encode_byte(self.tutorial) \
        + encode_int(self.chara_comment_id_0) \
        + encode_int(self.chara_comment_id_1) \
        + encode_int(self.chara_comment_id_2) \
        + encode_int(self.chara_comment_id_3) \
        + encode_int(self.chara_comment_id_4) \
        + encode_str(self.col_rate) \
        + encode_int(self.limit_default) \
        + encode_str(self.limit_time_dec) \
        + encode_str(self.limit_chara_dec) \
        + encode_int(self.limit_resurrection) \
        + encode_int(self.mission_table_sub_id) \
        + encode_short(self.mission_enemy_lv_limit) \
        + encode_int(self.reward_table_sub_id) \
        + encode_int(self.player_trace_table_sub_id) \
        + encode_int(self.success_player_exp) \
        + encode_int(self.failed_player_exp) \
        + encode_int(self.greed_spawn_wait_count) \
        + encode_int(self.honey_spawn_wait_count) \
        + encode_int(self.menu_display_enemy_set_id) \
        + encode_str(self.stage_filepath) \
        + encode_str(self.rarity_up_chance_rate) \
        + encode_str(self.pair_mob_hp_rate) \
        + encode_str(self.pair_mob_atk_rate) \
        + encode_str(self.pair_leader_hp_rate) \
        + encode_str(self.pair_leader_atk_rate) \
        + encode_str(self.pair_boss_hp_rate) \
        + encode_str(self.pair_boss_atk_rate) \
        + encode_str(self.pair_exp_rate) \
        + encode_str(self.trio_mob_hp_rate) \
        + encode_str(self.trio_mob_atk_rate) \
        + encode_str(self.trio_leader_hp_rate) \
        + encode_str(self.trio_leader_atk_rate) \
        + encode_str(self.trio_boss_hp_rate) \
        + encode_str(self.trio_boss_atk_rate) \
        + encode_str(self.trio_exp_rate) \
        + encode_int(self.single_reward_vp) \
        + encode_int(self.pair_reward_vp) \
        + encode_int(self.trio_reward_vp)

class QuestExistUnitData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_exist_unit_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestExistUnitData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_exist_unit_id = data['QuestExistUnitId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.enemy_kind_id = data['EnemyKindId']
        ret.unit_id = data['UnitId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_exist_unit_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.enemy_kind_id) \
        + encode_int(self.unit_id)

class QuestEpisodeAppendRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_episode_append_reward_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.episode_append_id = decode_int(data, off)
        off += INT_OFF

        self.episode_append_num = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestEpisodeAppendRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_episode_append_reward_id = data['QuestEpisodeAppendRewardId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.episode_append_id = data['EpisodeAppendId']
        ret.episode_append_num = data['EpisodeAppendNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_episode_append_reward_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.episode_append_id) \
        + encode_int(self.episode_append_num)

class SideQuestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.side_quest_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.episode_num = decode_int(data, off)
        off += INT_OFF

        self.ex_bonus_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.recommend_lv = decode_int(data, off)
        off += INT_OFF

        self.comment_summary, new_off = decode_str(data, off)
        off += new_off

        self.comment_introduction, new_off = decode_str(data, off)
        off += new_off

        self.start_adv_name, new_off = decode_str(data, off)
        off += new_off

        self.end_adv_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SideQuestData":
        ret = cls(b"\x00" * 99, 0)
        ret.side_quest_id = data['SideQuestId']
        ret.display_name = data['DisplayName']
        ret.episode_num = data['EpisodeNum']
        ret.ex_bonus_table_sub_id = data['ExBonusTableSubId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.recommend_lv = data['RecommendLv']
        ret.comment_summary = data['CommentSummary']
        ret.comment_introduction = data['CommentIntroduction']
        ret.start_adv_name = data['StartAdvName']
        ret.end_adv_name = data['EndAdvName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.side_quest_id) \
        + encode_str(self.display_name) \
        + encode_int(self.episode_num) \
        + encode_int(self.ex_bonus_table_sub_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.recommend_lv) \
        + encode_str(self.comment_summary) \
        + encode_str(self.comment_introduction) \
        + encode_str(self.start_adv_name) \
        + encode_str(self.end_adv_name)

class EpisodeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.episode_id = decode_int(data, off)
        off += INT_OFF

        self.episode_chapter_id = decode_int(data, off)
        off += INT_OFF

        self.release_episode_id = decode_int(data, off)
        off += INT_OFF

        self.episode_num = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.comment_summary, new_off = decode_str(data, off)
        off += new_off

        self.comment_introduction, new_off = decode_str(data, off)
        off += new_off

        self.recommend_lv = decode_int(data, off)
        off += INT_OFF

        self.ex_bonus_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.start_adv_name, new_off = decode_str(data, off)
        off += new_off

        self.end_adv_name, new_off = decode_str(data, off)
        off += new_off

        self.unlock_still_id = decode_int(data, off)
        off += INT_OFF

        self.required_release_episode_append_id = decode_int(data, off)
        off += INT_OFF

        self.required_release_episode_append_num = decode_short(data, off)
        off += SHORT_OFF

        self.release_reward_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EpisodeData":
        ret = cls(b"\x00" * 99, 0)
        ret.episode_id = data['EpisodeId']
        ret.episode_chapter_id = data['EpisodeChapterId']
        ret.release_episode_id = data['ReleaseEpisodeId']
        ret.episode_num = data['EpisodeNum']
        ret.title = data['Title']
        ret.comment_summary = data['CommentSummary']
        ret.comment_introduction = data['CommentIntroduction']
        ret.recommend_lv = data['RecommendLv']
        ret.ex_bonus_table_sub_id = data['ExBonusTableSubId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.start_adv_name = data['StartAdvName']
        ret.end_adv_name = data['EndAdvName']
        ret.unlock_still_id = data['UnlockStillId']
        ret.required_release_episode_append_id = data['RequiredReleaseEpisodeAppendId']
        ret.required_release_episode_append_num = data['RequiredReleaseEpisodeAppendNum']
        ret.release_reward_vp = data['ReleaseRewardVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.episode_id) \
        + encode_int(self.episode_chapter_id) \
        + encode_int(self.release_episode_id) \
        + encode_int(self.episode_num) \
        + encode_str(self.title) \
        + encode_str(self.comment_summary) \
        + encode_str(self.comment_introduction) \
        + encode_int(self.recommend_lv) \
        + encode_int(self.ex_bonus_table_sub_id) \
        + encode_int(self.quest_scene_id) \
        + encode_str(self.start_adv_name) \
        + encode_str(self.end_adv_name) \
        + encode_int(self.unlock_still_id) \
        + encode_int(self.required_release_episode_append_id) \
        + encode_short(self.required_release_episode_append_num) \
        + encode_int(self.release_reward_vp)

class EpisodeChapterData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.episode_chapter_id = decode_int(data, off)
        off += INT_OFF

        self.episode_part_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EpisodeChapterData":
        ret = cls(b"\x00" * 99, 0)
        ret.episode_chapter_id = data['EpisodeChapterId']
        ret.episode_part_id = data['EpisodePartId']
        ret.display_name = data['DisplayName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.episode_chapter_id) \
        + encode_int(self.episode_part_id) \
        + encode_str(self.display_name)

class EpisodePartData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.episode_part_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EpisodePartData":
        ret = cls(b"\x00" * 99, 0)
        ret.episode_part_id = data['EpisodePartId']
        ret.display_name = data['DisplayName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.episode_part_id) \
        + encode_str(self.display_name)

class TrialTowerData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.trial_tower_id = decode_short(data, off)
        off += SHORT_OFF

        self.release_trial_tower_id = decode_int(data, off)
        off += INT_OFF

        self.ex_bonus_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.recommend_lv = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TrialTowerData":
        ret = cls(b"\x00" * 99, 0)
        ret.trial_tower_id = data['TrialTowerId']
        ret.release_trial_tower_id = data['ReleaseTrialTowerId']
        ret.ex_bonus_table_sub_id = data['ExBonusTableSubId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.recommend_lv = data['RecommendLv']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.trial_tower_id) \
        + encode_int(self.release_trial_tower_id) \
        + encode_int(self.ex_bonus_table_sub_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.recommend_lv)

class ExTowerData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_tower_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.release_trial_tower_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ExTowerData":
        ret = cls(b"\x00" * 99, 0)
        ret.ex_tower_id = data['ExTowerId']
        ret.title = data['Title']
        ret.release_trial_tower_id = data['ReleaseTrialTowerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_tower_id) \
        + encode_str(self.title) \
        + encode_int(self.release_trial_tower_id)

class ExTowerQuestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_tower_quest_id = decode_int(data, off)
        off += INT_OFF

        self.ex_tower_id = decode_int(data, off)
        off += INT_OFF

        self.release_ex_tower_quest_id = decode_int(data, off)
        off += INT_OFF

        self.level_num = decode_short(data, off)
        off += SHORT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.ex_bonus_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.recommend_lv = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ExTowerQuestData":
        ret = cls(b"\x00" * 99, 0)
        ret.ex_tower_quest_id = data['ExTowerQuestId']
        ret.ex_tower_id = data['ExTowerId']
        ret.release_ex_tower_quest_id = data['ReleaseExTowerQuestId']
        ret.level_num = data['LevelNum']
        ret.title = data['Title']
        ret.ex_bonus_table_sub_id = data['ExBonusTableSubId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.recommend_lv = data['RecommendLv']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_tower_quest_id) \
        + encode_int(self.ex_tower_id) \
        + encode_int(self.release_ex_tower_quest_id) \
        + encode_short(self.level_num) \
        + encode_str(self.title) \
        + encode_int(self.ex_bonus_table_sub_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.recommend_lv)

class MenuDisplayEnemyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.menu_display_enemy_id = decode_short(data, off)
        off += SHORT_OFF

        self.menu_display_enemy_set_id = decode_int(data, off)
        off += INT_OFF

        self.boss_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.enemy_kind_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MenuDisplayEnemyData":
        ret = cls(b"\x00" * 99, 0)
        ret.menu_display_enemy_id = data['MenuDisplayEnemyId']
        ret.menu_display_enemy_set_id = data['MenuDisplayEnemySetId']
        ret.boss_flag = data['BossFlag']
        ret.enemy_kind_id = data['EnemyKindId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.menu_display_enemy_id) \
        + encode_int(self.menu_display_enemy_set_id) \
        + encode_byte(self.boss_flag) \
        + encode_int(self.enemy_kind_id)

class MissionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.mission_id = decode_short(data, off)
        off += SHORT_OFF

        self.mission_difficulty_id = decode_int(data, off)
        off += INT_OFF

        self.mission_name, new_off = decode_str(data, off)
        off += new_off

        self.time_limit = decode_int(data, off)
        off += INT_OFF

        self.condition = decode_short(data, off)
        off += SHORT_OFF

        self.enemy_set_id = decode_int(data, off)
        off += INT_OFF

        self.value1 = decode_int(data, off)
        off += INT_OFF

        self.value2 = decode_int(data, off)
        off += INT_OFF

        self.enemy_hide = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MissionData":
        ret = cls(b"\x00" * 99, 0)
        ret.mission_id = data['MissionId']
        ret.mission_difficulty_id = data['MissionDifficultyId']
        ret.mission_name = data['MissionName']
        ret.time_limit = data['TimeLimit']
        ret.condition = data['Condition']
        ret.enemy_set_id = data['EnemySetId']
        ret.value1 = data['Value1']
        ret.value2 = data['Value2']
        ret.enemy_hide = data['EnemyHide']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.mission_id) \
        + encode_int(self.mission_difficulty_id) \
        + encode_str(self.mission_name) \
        + encode_int(self.time_limit) \
        + encode_short(self.condition) \
        + encode_int(self.enemy_set_id) \
        + encode_int(self.value1) \
        + encode_int(self.value2) \
        + encode_byte(self.enemy_hide)

class MissionTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.mission_table_id = decode_int(data, off)
        off += INT_OFF

        self.mission_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.mission_id = decode_int(data, off)
        off += INT_OFF

        self.rate = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MissionTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.mission_table_id = data['MissionTableId']
        ret.mission_table_sub_id = data['MissionTableSubId']
        ret.mission_id = data['MissionId']
        ret.rate = data['Rate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.mission_table_id) \
        + encode_int(self.mission_table_sub_id) \
        + encode_int(self.mission_id) \
        + encode_int(self.rate)

class MissionDifficultyData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.mission_difficulty_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_exp = decode_int(data, off)
        off += INT_OFF

        self.unanalyzed_log_exp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "MissionDifficultyData":
        ret = cls(b"\x00" * 99, 0)
        ret.mission_difficulty_id = data['MissionDifficultyId']
        ret.skill_exp = data['SkillExp']
        ret.unanalyzed_log_exp = data['UnanalyzedLogExp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.mission_difficulty_id) \
        + encode_int(self.skill_exp) \
        + encode_int(self.unanalyzed_log_exp)

class BattleCameraData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.battle_camera_id = decode_short(data, off)
        off += SHORT_OFF

        self.offset_x, new_off = decode_str(data, off)
        off += new_off

        self.offset_y, new_off = decode_str(data, off)
        off += new_off

        self.offset_z, new_off = decode_str(data, off)
        off += new_off

        self.rot_h, new_off = decode_str(data, off)
        off += new_off

        self.rot_v, new_off = decode_str(data, off)
        off += new_off

        self.distance, new_off = decode_str(data, off)
        off += new_off

        self.near, new_off = decode_str(data, off)
        off += new_off

        self.far, new_off = decode_str(data, off)
        off += new_off

        self.fov, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BattleCameraData":
        ret = cls(b"\x00" * 99, 0)
        ret.battle_camera_id = data['BattleCameraId']
        ret.offset_x = data['OffsetX']
        ret.offset_y = data['OffsetY']
        ret.offset_z = data['OffsetZ']
        ret.rot_h = data['RotH']
        ret.rot_v = data['RotV']
        ret.distance = data['Distance']
        ret.near = data['Near']
        ret.far = data['Far']
        ret.fov = data['Fov']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.battle_camera_id) \
        + encode_str(self.offset_x) \
        + encode_str(self.offset_y) \
        + encode_str(self.offset_z) \
        + encode_str(self.rot_h) \
        + encode_str(self.rot_v) \
        + encode_str(self.distance) \
        + encode_str(self.near) \
        + encode_str(self.far) \
        + encode_str(self.fov)

class ChatMainStoryData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chat_main_story_id = decode_int(data, off)
        off += INT_OFF

        self.release_condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.release_condition_value = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.first_reward_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ChatMainStoryData":
        ret = cls(b"\x00" * 99, 0)
        ret.chat_main_story_id = data['ChatMainStoryId']
        ret.release_condition_type = data['ReleaseConditionType']
        ret.release_condition_value = data['ReleaseConditionValue']
        ret.display_name = data['DisplayName']
        ret.first_reward_vp = data['FirstRewardVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.chat_main_story_id) \
        + encode_byte(self.release_condition_type) \
        + encode_int(self.release_condition_value) \
        + encode_str(self.display_name) \
        + encode_int(self.first_reward_vp)

class ChatSideStoryData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chat_side_story_id = decode_int(data, off)
        off += INT_OFF

        self.unlock_side_quest_id = decode_int(data, off)
        off += INT_OFF

        self.release_condition_chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.release_condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.release_condition_value1 = decode_int(data, off)
        off += INT_OFF

        self.release_condition_value2 = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.first_reward_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ChatSideStoryData":
        ret = cls(b"\x00" * 99, 0)
        ret.chat_side_story_id = data['ChatSideStoryId']
        ret.unlock_side_quest_id = data['UnlockSideQuestId']
        ret.release_condition_chara_id = data['ReleaseConditionCharaId']
        ret.release_condition_type = data['ReleaseConditionType']
        ret.release_condition_value1 = data['ReleaseConditionValue1']
        ret.release_condition_value2 = data['ReleaseConditionValue2']
        ret.display_name = data['DisplayName']
        ret.first_reward_vp = data['FirstRewardVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.chat_side_story_id) \
        + encode_int(self.unlock_side_quest_id) \
        + encode_short(self.release_condition_chara_id) \
        + encode_byte(self.release_condition_type) \
        + encode_int(self.release_condition_value1) \
        + encode_int(self.release_condition_value2) \
        + encode_str(self.display_name) \
        + encode_int(self.first_reward_vp)

class ChatEventStoryData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chat_event_story_id = decode_int(data, off)
        off += INT_OFF

        self.event_id = decode_int(data, off)
        off += INT_OFF

        self.release_condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.release_condition_value = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.first_reward_vp = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ChatEventStoryData":
        ret = cls(b"\x00" * 99, 0)
        ret.chat_event_story_id = data['ChatEventStoryId']
        ret.event_id = data['EventId']
        ret.release_condition_type = data['ReleaseConditionType']
        ret.release_condition_value = data['ReleaseConditionValue']
        ret.display_name = data['DisplayName']
        ret.first_reward_vp = data['FirstRewardVp']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.chat_event_story_id) \
        + encode_int(self.event_id) \
        + encode_byte(self.release_condition_type) \
        + encode_int(self.release_condition_value) \
        + encode_str(self.display_name) \
        + encode_int(self.first_reward_vp)

class NavigatorCharaData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.navigator_chara_id = decode_int(data, off)
        off += INT_OFF

        self.condition_start_episode_id = decode_int(data, off)
        off += INT_OFF

        self.condition_end_episode_id = decode_int(data, off)
        off += INT_OFF

        self.disp_chara = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "NavigatorCharaData":
        ret = cls(b"\x00" * 99, 0)
        ret.navigator_chara_id = data['NavigatorCharaId']
        ret.condition_start_episode_id = data['ConditionStartEpisodeId']
        ret.condition_end_episode_id = data['ConditionEndEpisodeId']
        ret.disp_chara = data['DispChara']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.navigator_chara_id) \
        + encode_int(self.condition_start_episode_id) \
        + encode_int(self.condition_end_episode_id) \
        + encode_int(self.disp_chara)

class NavigatorCommentData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.navigator_comment_id = decode_int(data, off)
        off += INT_OFF

        self.menu_id = decode_int(data, off)
        off += INT_OFF

        self.draw_type = decode_int(data, off)
        off += INT_OFF

        self.condition_past_menu = decode_int(data, off)
        off += INT_OFF

        self.priority = decode_int(data, off)
        off += INT_OFF

        self.condition_start_episode_id = decode_int(data, off)
        off += INT_OFF

        self.condition_end_episode_id = decode_int(data, off)
        off += INT_OFF

        self.only_once = decode_byte(data, off)
        off += BYTE_OFF

        self.only_rico = decode_byte(data, off)
        off += BYTE_OFF

        self.comment_ai, new_off = decode_str(data, off)
        off += new_off

        self.comment_rico, new_off = decode_str(data, off)
        off += new_off

        self.expression = decode_int(data, off)
        off += INT_OFF

        self.voice_id, new_off = decode_str(data, off)
        off += new_off

        self.show_start_time, new_off = decode_str(data, off)
        off += new_off

        self.show_end_time, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "NavigatorCommentData":
        ret = cls(b"\x00" * 99, 0)
        ret.navigator_comment_id = data['NavigatorCommentId']
        ret.menu_id = data['MenuId']
        ret.draw_type = data['DrawType']
        ret.condition_past_menu = data['ConditionPastMenu']
        ret.priority = data['Priority']
        ret.condition_start_episode_id = data['ConditionStartEpisodeId']
        ret.condition_end_episode_id = data['ConditionEndEpisodeId']
        ret.only_once = data['OnlyOnce']
        ret.only_rico = data['OnlyRico']
        ret.comment_ai = data['CommentAi']
        ret.comment_rico = data['CommentRico']
        ret.expression = data['Expression']
        ret.voice_id = data['VoiceId']
        ret.show_start_time = data['ShowStartTime']
        ret.show_end_time = data['ShowEndTime']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.navigator_comment_id) \
        + encode_int(self.menu_id) \
        + encode_int(self.draw_type) \
        + encode_int(self.condition_past_menu) \
        + encode_int(self.priority) \
        + encode_int(self.condition_start_episode_id) \
        + encode_int(self.condition_end_episode_id) \
        + encode_byte(self.only_once) \
        + encode_byte(self.only_rico) \
        + encode_str(self.comment_ai) \
        + encode_str(self.comment_rico) \
        + encode_int(self.expression) \
        + encode_str(self.voice_id) \
        + encode_str(self.show_start_time) \
        + encode_str(self.show_end_time)

class ExBonusTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_bonus_table_id = decode_int(data, off)
        off += INT_OFF

        self.ex_bonus_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.ex_bonus_condition_id = decode_int(data, off)
        off += INT_OFF

        self.condition_value1 = decode_int(data, off)
        off += INT_OFF

        self.condition_value2 = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ExBonusTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.ex_bonus_table_id = data['ExBonusTableId']
        ret.ex_bonus_table_sub_id = data['ExBonusTableSubId']
        ret.ex_bonus_condition_id = data['ExBonusConditionId']
        ret.condition_value1 = data['ConditionValue1']
        ret.condition_value2 = data['ConditionValue2']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_bonus_table_id) \
        + encode_int(self.ex_bonus_table_sub_id) \
        + encode_int(self.ex_bonus_condition_id) \
        + encode_int(self.condition_value1) \
        + encode_int(self.condition_value2) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class ExBonusConditionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ex_bonus_condition_id = decode_int(data, off)
        off += INT_OFF

        self.format, new_off = decode_str(data, off)
        off += new_off

        self.hud_format, new_off = decode_str(data, off)
        off += new_off

        self.format_param_size = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ExBonusConditionData":
        ret = cls(b"\x00" * 99, 0)
        ret.ex_bonus_condition_id = data['ExBonusConditionId']
        ret.format = data['Format']
        ret.hud_format = data['HudFormat']
        ret.format_param_size = data['FomatParamSize']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ex_bonus_condition_id) \
        + encode_str(self.format) \
        + encode_str(self.hud_format) \
        + encode_int(self.format_param_size)

class BeginnerMissionProgressesUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_condition_id = decode_int(data, off)
        off += INT_OFF

        self.achievement_num = decode_short(data, off)
        off += SHORT_OFF

        self.complete_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.complete_date, new_off = decode_date_str(data, off)
        off += new_off

        self.reward_received_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.reward_received_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionProgressesUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_condition_id = data['BeginnerMissionConditionId']
        ret.achievement_num = data['AchievementNum']
        ret.complete_flag = data['CompleteFlag']
        ret.complete_date = data['CompleteDate']
        ret.reward_received_flag = data['RewardReceivedFlag']
        ret.reward_received_date = data['RewardReceivedDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_condition_id) \
        + encode_short(self.achievement_num) \
        + encode_byte(self.complete_flag) \
        + encode_date_str(self.complete_date) \
        + encode_byte(self.reward_received_flag) \
        + encode_date_str(self.reward_received_date)

class BeginnerMissionSeatProgressesUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_seat_condition_id = decode_int(data, off)
        off += INT_OFF

        self.achievement_num = decode_short(data, off)
        off += SHORT_OFF

        self.complete_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.complete_date, new_off = decode_date_str(data, off)
        off += new_off

        self.reward_received_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.reward_received_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionSeatProgressesUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_seat_condition_id = data['BeginnerMissionSeatConditionId']
        ret.achievement_num = data['AchievementNum']
        ret.complete_flag = data['CompleteFlag']
        ret.complete_date = data['CompleteDate']
        ret.reward_received_flag = data['RewardReceivedFlag']
        ret.reward_received_date = data['RewardReceivedDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_seat_condition_id) \
        + encode_short(self.achievement_num) \
        + encode_byte(self.complete_flag) \
        + encode_date_str(self.complete_date) \
        + encode_byte(self.reward_received_flag) \
        + encode_date_str(self.reward_received_date)

class LinkedSiteRegCampaignUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.reward_received_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.reward_received_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "LinkedSiteRegCampaignUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.reward_received_flag = data['RewardReceivedFlag']
        ret.reward_received_date = data['RewardReceivedDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.reward_received_flag) \
        + encode_date_str(self.reward_received_date)

class HeroLogUnitUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.leader_appointment_normal_card_num = decode_int(data, off)
        off += INT_OFF

        self.leader_appointment_holographic_card_num = decode_int(data, off)
        off += INT_OFF

        self.skill_slot_max_release_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "HeroLogUnitUserData":
        ret = cls(b"\x00" * 13, 0)
        ret.hero_log_id = data['HeroLogId']
        ret.leader_appointment_normal_card_num = data['LeaderAppointmentNormalCardNum']
        ret.leader_appointment_holographic_card_num = data['LeaderAppointmentHolographicCardNum']
        ret.skill_slot_max_release_flag = data['SkillSlotMaxReleaseFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.hero_log_id) \
        + encode_int(self.leader_appointment_normal_card_num) \
        + encode_int(self.leader_appointment_holographic_card_num) \
        + encode_byte(self.skill_slot_max_release_flag)

class CharaUnitUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.reliability_1 = decode_int(data, off)
        off += INT_OFF

        self.reliability_2 = decode_int(data, off)
        off += INT_OFF

        self.motivation_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "CharaUnitUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.chara_id = data['CharaId']
        ret.reliability_1 = data['Reliability1']
        ret.reliability_2 = data['Reliability2']
        ret.motivation_flag = data['MotivationFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.chara_id) \
        + encode_int(self.reliability_1) \
        + encode_int(self.reliability_2) \
        + encode_byte(self.motivation_flag)

class AdventureExecUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.status = decode_byte(data, off)
        off += BYTE_OFF

        self.adventure_id = decode_int(data, off)
        off += INT_OFF

        self.adventure_difficulty_id = decode_int(data, off)
        off += INT_OFF

        self.last_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.remaining_sec_to_complete = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AdventureExecUserData":
        ret = cls(b"\x00" * 99, 0)
        ret.status = data['Status']
        ret.adventure_id = data['AdventureId']
        ret.adventure_difficulty_id = data['AdventureDifficultyId']
        ret.last_start_date = data['LastStartDate']
        ret.remaining_sec_to_complete = data['RemainingSecToComplete']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.status) \
        + encode_int(self.adventure_id) \
        + encode_int(self.adventure_difficulty_id) \
        + encode_date_str(self.last_start_date) \
        + encode_int(self.remaining_sec_to_complete)

class QuestRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_rare_drop_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.strength_min = decode_int(data, off)
        off += INT_OFF

        self.strength_max = decode_int(data, off)
        off += INT_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.drop_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestRareDropData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_rare_drop_id = data['QuestRareDropId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.unit_id = data['UnitId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength_min = data['StrengthMin']
        ret.strength_max = data['StrengthMax']
        ret.property_table_sub_id = data['PropertyTableSubId']
        ret.drop_rate = data['DropRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_rare_drop_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.strength_min) \
        + encode_int(self.strength_max) \
        + encode_int(self.property_table_sub_id) \
        + encode_str(self.drop_rate)

class QuestSpecialRareDropSettingData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_special_rare_drop_setting_id = decode_int(data, off)
        off += INT_OFF

        self.tower_type = decode_byte(data, off)
        off += BYTE_OFF

        self.start_trial_tower_id = decode_short(data, off)
        off += SHORT_OFF

        self.end_trial_tower_id = decode_short(data, off)
        off += SHORT_OFF

        self.rare_drop_upward_rate, new_off = decode_str(data, off)
        off += new_off

        self.quest_special_rare_drop_sub_id = decode_int(data, off)
        off += INT_OFF

        self.generic_campaign_period_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSpecialRareDropSettingData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_special_rare_drop_setting_id = data['QuestSpecialRareDropSettingId']
        ret.tower_type = data['TowerType']
        ret.start_trial_tower_id = data['StartTrialTowerId']
        ret.end_trial_tower_id = data['EndTrialTowerId']
        ret.rare_drop_upward_rate = data['RareDropUpwardRate']
        ret.quest_special_rare_drop_sub_id = data['QuestSpecialRareDropSubId']
        ret.generic_campaign_period_id = data['GenericCampaignPeriodId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_special_rare_drop_setting_id) \
        + encode_byte(self.tower_type) \
        + encode_short(self.start_trial_tower_id) \
        + encode_short(self.end_trial_tower_id) \
        + encode_str(self.rare_drop_upward_rate) \
        + encode_int(self.quest_special_rare_drop_sub_id) \
        + encode_int(self.generic_campaign_period_id)

class QuestSpecialRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_special_rare_drop_id = decode_int(data, off)
        off += INT_OFF

        self.quest_special_rare_drop_sub_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.strength_min = decode_int(data, off)
        off += INT_OFF

        self.strength_max = decode_int(data, off)
        off += INT_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.drop_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestSpecialRareDropData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_special_rare_drop_id = data['QuestSpecialRareDropId']
        ret.quest_special_rare_drop_sub_id = data['QuestSpecialRareDropSubId']
        ret.unit_id = data['UnitId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength_min = data['StrengthMin']
        ret.strength_max = data['StrengthMax']
        ret.property_table_sub_id = data['PropertyTableSubId']
        ret.drop_rate = data['DropRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_special_rare_drop_id) \
        + encode_int(self.quest_special_rare_drop_sub_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.strength_min) \
        + encode_int(self.strength_max) \
        + encode_int(self.property_table_sub_id) \
        + encode_str(self.drop_rate)

class QuestTutorialData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_tutorial_id = decode_short(data, off)
        off += SHORT_OFF

        self.trigger = decode_int(data, off)
        off += INT_OFF

        self.trigger_delay, new_off = decode_str(data, off)
        off += new_off

        self.trigger_during, new_off = decode_str(data, off)
        off += new_off

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.unit_range, new_off = decode_str(data, off)
        off += new_off

        self.comment_text, new_off = decode_str(data, off)
        off += new_off

        self.voice_id, new_off = decode_str(data, off)
        off += new_off

        self.comment_pos, new_off = decode_str(data, off)
        off += new_off

        self.yui_face, new_off = decode_str(data, off)
        off += new_off

        self.arrow_direct, new_off = decode_str(data, off)
        off += new_off

        self.arrow_position, new_off = decode_str(data, off)
        off += new_off

        self.image_plus, new_off = decode_str(data, off)
        off += new_off

        self.image_plus_pos, new_off = decode_str(data, off)
        off += new_off

        self.stick_info, new_off = decode_str(data, off)
        off += new_off

        self.mark_effect, new_off = decode_str(data, off)
        off += new_off

        self.mark_pos, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestTutorialData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_tutorial_id = data['Id']
        ret.trigger = data['Trigger']
        ret.trigger_delay = data['TriggerDelay']
        ret.trigger_during = data['TriggerDuring']
        ret.unit_id = data['UnitId']
        ret.unit_range = data['UnitRange']
        ret.comment_text = data['CommentText']
        ret.voice_id = data['VoiceID']
        ret.comment_pos = data['CommentPos']
        ret.yui_face = data['YuiFace']
        ret.arrow_direct = data['ArrowDirect']
        ret.arrow_position = data['ArrowPosition']
        ret.image_plus = data['ImagePlus']
        ret.image_plus_pos = data['ImagePlusPos']
        ret.stick_info = data['StickInfo']
        ret.mark_effect = data['MarkEffect']
        ret.mark_pos = data['MarkPos']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.quest_tutorial_id) \
        + encode_int(self.trigger) \
        + encode_str(self.trigger_delay) \
        + encode_str(self.trigger_during) \
        + encode_int(self.unit_id) \
        + encode_str(self.unit_range) \
        + encode_str(self.comment_text) \
        + encode_str(self.voice_id) \
        + encode_str(self.comment_pos) \
        + encode_str(self.yui_face) \
        + encode_str(self.arrow_direct) \
        + encode_str(self.arrow_position) \
        + encode_str(self.image_plus) \
        + encode_str(self.image_plus_pos) \
        + encode_str(self.stick_info) \
        + encode_str(self.mark_effect) \
        + encode_str(self.mark_pos)

class QuestPlayerTraceTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.player_trace_table_id = decode_short(data, off)
        off += SHORT_OFF

        self.player_trace_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.rate = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestPlayerTraceTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.player_trace_table_id = data['PlayerTraceTableId']
        ret.player_trace_table_sub_id = data['PlayerTraceTableSubId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.rate = data['Rate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.player_trace_table_id) \
        + encode_int(self.player_trace_table_sub_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.rate)

class QuestStillData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.still_id = decode_int(data, off)
        off += INT_OFF

        self.file_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestStillData":
        ret = cls(b"\x00" * 99, 0)
        ret.still_id = data['StillId']
        ret.file_name = data['FileName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.still_id) \
        + encode_str(self.file_name)

class GashaData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.description, new_off = decode_str(data, off)
        off += new_off

        self.gasha_type = decode_byte(data, off)
        off += BYTE_OFF

        self.open_type = decode_byte(data, off)
        off += BYTE_OFF

        self.free_target_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.reset_hour_list, new_off = decode_str(data, off)
        off += new_off

        self.limit_num = decode_short(data, off)
        off += SHORT_OFF

        self.open_days = decode_short(data, off)
        off += SHORT_OFF

        self.sort_num = decode_int(data, off)
        off += INT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_id = data['GashaId']
        ret.name = data['Name']
        ret.description = data['Description']
        ret.gasha_type = data['GashaType']
        ret.open_type = data['OpenType']
        ret.free_target_flag = data['FreeTargetFlag']
        ret.reset_hour_list = data['ResetHourList']
        ret.limit_num = data['LimitNum']
        ret.open_days = data['OpenDays']
        ret.sort_num = data['SortNum']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_id) \
        + encode_str(self.name) \
        + encode_str(self.description) \
        + encode_byte(self.gasha_type) \
        + encode_byte(self.open_type) \
        + encode_byte(self.free_target_flag) \
        + encode_str(self.reset_hour_list) \
        + encode_short(self.limit_num) \
        + encode_short(self.open_days) \
        + encode_int(self.sort_num) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class GashaHeaderData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_header_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_id = decode_int(data, off)
        off += INT_OFF

        self.step_no = decode_byte(data, off)
        off += BYTE_OFF

        self.step_progress_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.platform = decode_byte(data, off)
        off += BYTE_OFF

        self.use_type_1 = decode_byte(data, off)
        off += BYTE_OFF

        self.use_type_2 = decode_byte(data, off)
        off += BYTE_OFF

        self.provision_num = decode_byte(data, off)
        off += BYTE_OFF

        self.premium_lottery_num = decode_byte(data, off)
        off += BYTE_OFF

        self.premium_lottery_executable_num = decode_byte(data, off)
        off += BYTE_OFF

        self.use_type_1_first_use_num = decode_int(data, off)
        off += INT_OFF

        self.use_type_1_base_use_num = decode_int(data, off)
        off += INT_OFF

        self.use_type_1_extra_use_num = decode_int(data, off)
        off += INT_OFF

        self.use_type_2_first_use_num = decode_int(data, off)
        off += INT_OFF

        self.use_type_2_base_use_num = decode_int(data, off)
        off += INT_OFF

        self.use_type_2_extra_use_num = decode_int(data, off)
        off += INT_OFF

        self.yui_chance_log_open_rate, new_off = decode_str(data, off)
        off += new_off

        self.yui_chance_rarity_up_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaHeaderData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_header_id = data['GashaHeaderId']
        ret.gasha_id = data['GashaId']
        ret.step_no = data['StepNo']
        ret.step_progress_flag = data['StepProgressFlag']
        ret.platform = data['Platform']
        ret.use_type_1 = data['UseType1']
        ret.use_type_2 = data['UseType2']
        ret.provision_num = data['ProvisionNum']
        ret.premium_lottery_num = data['PremiumLotteryNum']
        ret.premium_lottery_executable_num = data['PremiumLotteryExecutableNum']
        ret.use_type_1_first_use_num = data['UseType1FirstUseNum']
        ret.use_type_1_base_use_num = data['UseType1BaseUseNum']
        ret.use_type_1_extra_use_num = data['UseType1ExtraUseNum']
        ret.use_type_2_first_use_num = data['UseType2FirstUseNum']
        ret.use_type_2_base_use_num = data['UseType2BaseUseNum']
        ret.use_type_2_extra_use_num = data['UseType2ExtraUseNum']
        ret.yui_chance_log_open_rate = data['YuiChanceLogOpenRate']
        ret.yui_chance_rarity_up_rate = data['YuiChanceRarityUpRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_header_id) \
        + encode_int(self.gasha_id) \
        + encode_byte(self.step_no) \
        + encode_byte(self.step_progress_flag) \
        + encode_byte(self.platform) \
        + encode_byte(self.use_type_1) \
        + encode_byte(self.use_type_2) \
        + encode_byte(self.provision_num) \
        + encode_byte(self.premium_lottery_num) \
        + encode_byte(self.premium_lottery_executable_num) \
        + encode_int(self.use_type_1_first_use_num) \
        + encode_int(self.use_type_1_base_use_num) \
        + encode_int(self.use_type_1_extra_use_num) \
        + encode_int(self.use_type_2_first_use_num) \
        + encode_int(self.use_type_2_base_use_num) \
        + encode_int(self.use_type_2_extra_use_num) \
        + encode_str(self.yui_chance_log_open_rate) \
        + encode_str(self.yui_chance_rarity_up_rate)

class GashaLotteryRarityData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_lottery_rarity_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_header_id = decode_int(data, off)
        off += INT_OFF

        self.lottery_rarity_type = decode_byte(data, off)
        off += BYTE_OFF

        self.lottery_rarity_rate, new_off = decode_str(data, off)
        off += new_off

        self.premium_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaLotteryRarityData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_lottery_rarity_id = data['GashaLotteryRarityId']
        ret.gasha_id = data['GashaId']
        ret.gasha_header_id = data['GashaHeaderId']
        ret.lottery_rarity_type = data['LotteryRarityType']
        ret.lottery_rarity_rate = data['LotteryRarityRate']
        ret.premium_rate = data['PremiumRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_lottery_rarity_id) \
        + encode_int(self.gasha_id) \
        + encode_int(self.gasha_header_id) \
        + encode_byte(self.lottery_rarity_type) \
        + encode_str(self.lottery_rarity_rate) \
        + encode_str(self.premium_rate)

class GashaPrizeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_prize_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_id = decode_int(data, off)
        off += INT_OFF

        self.lottery_rarity_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.unanalyzed_log_grade_id = decode_int(data, off)
        off += INT_OFF

        self.correction_rate = decode_short(data, off)
        off += SHORT_OFF

        self.pickup_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaPrizeData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_prize_id = data['GashaPrizeId']
        ret.gasha_id = data['GashaId']
        ret.lottery_rarity_type = data['LotteryRarityType']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.unanalyzed_log_grade_id = data['UnanalyzedLogGradeId']
        ret.correction_rate = data['CorrectionRate']
        ret.pickup_flag = data['PickupFlag']
        ret.property_table_sub_id = data['PropertyTableSubId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_prize_id) \
        + encode_int(self.gasha_id) \
        + encode_byte(self.lottery_rarity_type) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.unanalyzed_log_grade_id) \
        + encode_short(self.correction_rate) \
        + encode_byte(self.pickup_flag) \
        + encode_int(self.property_table_sub_id)

class ComebackEventData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.comeback_event_id = decode_int(data, off)
        off += INT_OFF

        self.comeback_event_sub_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.reward_set_sub_id = decode_int(data, off)
        off += INT_OFF

        self.require_days = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ComebackEventData":
        ret = cls(b"\x00" * 99, 0)
        ret.comeback_event_id = data['ComebackEventId']
        ret.comeback_event_sub_id = data['ComebackEventSubId']
        ret.display_name = data['DisplayName']
        ret.reward_set_sub_id = data['RewardSetSubId']
        ret.require_days = data['RequireDays']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.comeback_event_id) \
        + encode_int(self.comeback_event_sub_id) \
        + encode_str(self.display_name) \
        + encode_int(self.reward_set_sub_id) \
        + encode_short(self.require_days)

class AdBannerData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self.category = decode_byte(data, off)
        off += BYTE_OFF

        self.sort_num = decode_int(data, off)
        off += INT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.active_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AdBannerData":
        ret = cls(b"\x00" * 99, 0)
        ret.ad_banner_id = data['AdBannerId']
        ret.category = data['Category']
        ret.sort_num = data['SortNum']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        ret.active_flag = data['ActiveFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ad_banner_id) \
        + encode_byte(self.category) \
        + encode_int(self.sort_num) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date) \
        + encode_byte(self.active_flag)

class EventsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.event_id = decode_int(data, off)
        off += INT_OFF

        self.event_type = decode_byte(data, off)
        off += BYTE_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.param_1, new_off = decode_str(data, off)
        off += new_off

        self.param_2, new_off = decode_str(data, off)
        off += new_off

        self.param_3, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.chat_open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.chat_open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.news_id = decode_int(data, off)
        off += INT_OFF

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EventsData":
        ret = cls(b"\x00" * 99, 0)
        ret.event_id = data['EventId']
        ret.event_type = data['EventType']
        ret.title = data['Title']
        ret.param_1 = data['Param1']
        ret.param_2 = data['Param2']
        ret.param_3 = data['Param3']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.posting_start_date = data['PostingStartDate']
        ret.posting_end_date = data['PostingEndDate']
        ret.chat_open_start_date = data['ChatOpenStartDate']
        ret.chat_open_end_date = data['ChatOpenEndDate']
        ret.news_id = data['NewId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.event_id) \
        + encode_byte(self.event_type) \
        + encode_str(self.title) \
        + encode_str(self.param_1) \
        + encode_str(self.param_2) \
        + encode_str(self.param_3) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_date_str(self.posting_start_date) \
        + encode_date_str(self.posting_end_date) \
        + encode_date_str(self.chat_open_start_date) \
        + encode_date_str(self.chat_open_end_date) \
        + encode_int(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class TreasureHuntsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntsData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.title = data['Title']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_id) \
        + encode_str(self.title)

class TreasureHuntWholeTasksData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_whole_task_id = decode_int(data, off)
        off += INT_OFF

        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.task_type = decode_byte(data, off)
        off += BYTE_OFF

        self.achievement_possible_num = decode_short(data, off)
        off += SHORT_OFF

        self.get_event_point = decode_int(data, off)
        off += INT_OFF

        self.condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_value_accumulation_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_value_1, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_2, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_3, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_4, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_5, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntWholeTasksData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_whole_task_id = data['TreasureHuntWholeTaskId']
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.task_type = data['TaskType']
        ret.achievement_possible_num = data['AchievementPossibleNum']
        ret.get_event_point = data['GetEventPoint']
        ret.condition_type = data['ConditionType']
        ret.condition_value_accumulation_flag = data['ConditionValueAccumulationFlag']
        ret.condition_value_1 = data['ConditionValue1']
        ret.condition_value_2 = data['ConditionValue2']
        ret.condition_value_3 = data['ConditionValue3']
        ret.condition_value_4 = data['ConditionValue4']
        ret.condition_value_5 = data['ConditionValue5']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_whole_task_id) \
        + encode_int(self.treasure_hunt_id) \
        + encode_byte(self.task_type) \
        + encode_short(self.achievement_possible_num) \
        + encode_int(self.get_event_point) \
        + encode_byte(self.condition_type) \
        + encode_byte(self.condition_value_accumulation_flag) \
        + encode_str(self.condition_value_1) \
        + encode_str(self.condition_value_2) \
        + encode_str(self.condition_value_3) \
        + encode_str(self.condition_value_4) \
        + encode_str(self.condition_value_5) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date)

class TreasureHuntIndividualTasksData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_individual_task_id = decode_int(data, off)
        off += INT_OFF

        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.task_type = decode_byte(data, off)
        off += BYTE_OFF

        self.quest_scene_id = decode_short(data, off)
        off += SHORT_OFF

        self.achievement_possible_num = decode_short(data, off)
        off += SHORT_OFF

        self.get_event_point = decode_int(data, off)
        off += INT_OFF

        self.condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_value_accumulation_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_value_1, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_2, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_3, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_4, new_off = decode_str(data, off)
        off += new_off

        self.condition_value_5, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntIndividualTasksData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_individual_task_id = data['TreasureHuntIndividualTaskId']
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.task_type = data['TaskType']
        ret.quest_scene_id = data['QuestSceneId']
        ret.achievement_possible_num = data['AchievementPossibleNum']
        ret.get_event_point = data['GetEventPoint']
        ret.condition_type = data['ConditionType']
        ret.condition_value_accumulation_flag = data['ConditionValueAccumulationFlag']
        ret.condition_value_1 = data['ConditionValue1']
        ret.condition_value_2 = data['ConditionValue2']
        ret.condition_value_3 = data['ConditionValue3']
        ret.condition_value_4 = data['ConditionValue4']
        ret.condition_value_5 = data['ConditionValue5']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_individual_task_id) \
        + encode_int(self.treasure_hunt_id) \
        + encode_byte(self.task_type) \
        + encode_short(self.quest_scene_id) \
        + encode_short(self.achievement_possible_num) \
        + encode_int(self.get_event_point) \
        + encode_byte(self.condition_type) \
        + encode_byte(self.condition_value_accumulation_flag) \
        + encode_str(self.condition_value_1) \
        + encode_str(self.condition_value_2) \
        + encode_str(self.condition_value_3) \
        + encode_str(self.condition_value_4) \
        + encode_str(self.condition_value_5) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date)

class TreasureHuntSpecialEffectsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_special_effect_id = decode_int(data, off)
        off += INT_OFF

        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.special_effect_type = decode_byte(data, off)
        off += BYTE_OFF

        self.special_effect_coefficient, new_off = decode_str(data, off)
        off += new_off

        self.target_common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.target_common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.obtaining_location_type = decode_byte(data, off)
        off += BYTE_OFF

        self.obtaining_location_param, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntSpecialEffectsData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_special_effect_id = data['TreasureHuntSpecialEffectId']
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.special_effect_type = data['SpecialEffectType']
        ret.special_effect_coefficient = data['SpecialEffectCoefficient']
        ret.target_common_reward_type = data['TargetCommonRewardType']
        ret.target_common_reward_id = data['TargetCommonRewardId']
        ret.obtaining_location_type = data['ObtainingLocationType']
        ret.obtaining_location_param = data['ObtainingLocationParam']
        ret.open_start_date = data['OpenStartDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_special_effect_id) \
        + encode_int(self.treasure_hunt_id) \
        + encode_byte(self.special_effect_type) \
        + encode_str(self.special_effect_coefficient) \
        + encode_byte(self.target_common_reward_type) \
        + encode_int(self.target_common_reward_id) \
        + encode_byte(self.obtaining_location_type) \
        + encode_str(self.obtaining_location_param) \
        + encode_date_str(self.open_start_date)

class TreasureHuntEventPointRewardCommonRewardsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_event_point_reward_common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.need_event_point = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntEventPointRewardCommonRewardsData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_event_point_reward_common_reward_id = data['TreasureHuntEventPointRewardCommonRewardId']
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.need_event_point = data['NeedEventPoint']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_event_point_reward_common_reward_id) \
        + encode_int(self.treasure_hunt_id) \
        + encode_int(self.need_event_point) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class TreasureHuntEventPointRewardTitlesData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_event_point_reward_title_id = decode_int(data, off)
        off += INT_OFF

        self.treasure_hunt_id = decode_int(data, off)
        off += INT_OFF

        self.need_event_point = decode_int(data, off)
        off += INT_OFF

        self.title_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntEventPointRewardTitlesData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_event_point_reward_title_id = data['TreasureHuntEventPointRewardTitleId']
        ret.treasure_hunt_id = data['TreasureHuntId']
        ret.need_event_point = data['NeedEventPoint']
        ret.title_id = data['TitleId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_event_point_reward_title_id) \
        + encode_int(self.treasure_hunt_id) \
        + encode_int(self.need_event_point) \
        + encode_int(self.title_id)

class TreasureHuntTaskTextData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.treasure_hunt_task_text_id = decode_int(data, off)
        off += INT_OFF

        self.task_type = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.format, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "TreasureHuntTaskTextData":
        ret = cls(b"\x00" * 99, 0)
        ret.treasure_hunt_task_text_id = data['TreasureHuntTaskTextId']
        ret.task_type = data['TaskType']
        ret.condition_type = data['ConditionType']
        ret.format = data['Format']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.treasure_hunt_task_text_id) \
        + encode_byte(self.task_type) \
        + encode_byte(self.condition_type) \
        + encode_str(self.format)

class BnidSerialCodeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.bnid_item_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_code_type = decode_byte(data, off)
        off += BYTE_OFF

        self.category = decode_byte(data, off)
        off += BYTE_OFF

        self.description, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BnidSerialCodeData":
        ret = cls(b"\x00" * 99, 0)
        ret.bnid_item_id = data['BnidItemId']
        ret.serial_code_type = data['SerialCodeType']
        ret.category = data['Category']
        ret.description = data['Description']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.bnid_item_id) \
        + encode_byte(self.serial_code_type) \
        + encode_byte(self.category) \
        + encode_str(self.description) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date)

class BnidSerialCodeRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.bnid_item_id, new_off = decode_str(data, off)
        off += new_off

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BnidSerialCodeRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.bnid_item_id = data['BnidItemId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.bnid_item_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class SupportLogData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.support_log_id = decode_int(data, off)
        off += INT_OFF

        self.chara_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.rarity = decode_byte(data, off)
        off += BYTE_OFF

        self.support_log_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.sale_price = decode_int(data, off)
        off += INT_OFF

        self.composition_exp = decode_int(data, off)
        off += INT_OFF

        self.awakening_exp = decode_int(data, off)
        off += INT_OFF

        self.use_rank = decode_short(data, off)
        off += SHORT_OFF

        self.group_no = decode_short(data, off)
        off += SHORT_OFF

        self.adaptable_appear_append = decode_short(data, off)
        off += SHORT_OFF

        self.punisher_appear_append = decode_short(data, off)
        off += SHORT_OFF

        self.state, new_off = decode_str(data, off)
        off += new_off

        self.passive_state, new_off = decode_str(data, off)
        off += new_off

        self.power_default_value = decode_int(data, off)
        off += INT_OFF

        self.clt_default_value = decode_int(data, off)
        off += INT_OFF

        self.awakening_1_power = decode_int(data, off)
        off += INT_OFF

        self.awakening_1_clt = decode_int(data, off)
        off += INT_OFF

        self.awakening_2_power = decode_int(data, off)
        off += INT_OFF

        self.awakening_2_clt = decode_int(data, off)
        off += INT_OFF

        self.awakening_3_power = decode_int(data, off)
        off += INT_OFF

        self.awakening_3_clt = decode_int(data, off)
        off += INT_OFF

        self.awakening_4_power = decode_int(data, off)
        off += INT_OFF

        self.awakening_4_clt = decode_int(data, off)
        off += INT_OFF

        self.awakening_5_power = decode_int(data, off)
        off += INT_OFF

        self.awakening_5_clt = decode_int(data, off)
        off += INT_OFF

        self.normal_leader = decode_int(data, off)
        off += INT_OFF

        self.holo_leader = decode_int(data, off)
        off += INT_OFF

        self.ui_display_power_title, new_off = decode_str(data, off)
        off += new_off

        self.ui_display_power_content, new_off = decode_str(data, off)
        off += new_off

        self.prefab, new_off = decode_str(data, off)
        off += new_off

        self.cutin_mode, new_off = decode_str(data, off)
        off += new_off

        self.skill_voice_id, new_off = decode_str(data, off)
        off += new_off

        self.skill_name, new_off = decode_str(data, off)
        off += new_off

        self.name_in_skill_cutin, new_off = decode_str(data, off)
        off += new_off

        self.skill_text, new_off = decode_str(data, off)
        off += new_off

        self.skill_text_in_skill_cutin, new_off = decode_str(data, off)
        off += new_off

        self.chara_info, new_off = decode_str(data, off)
        off += new_off

        self.cutin_image, new_off = decode_str(data, off)
        off += new_off

        self.cutin_image_awake, new_off = decode_str(data, off)
        off += new_off

        self.status_chara_icon, new_off = decode_str(data, off)
        off += new_off

        self.status_chara_icon_awake, new_off = decode_str(data, off)
        off += new_off

        self.collection_display_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.collection_empty_frame_display_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SupportLogData":
        ret = cls(b"\x00" * 99, 0)
        ret.support_log_id = data['SupportLogId']
        ret.chara_id = data['CharaId']
        ret.name = data['Name']
        ret.rarity = data['Rarity']
        ret.support_log_type_id = data['SupportLogTypeId']
        ret.sale_price = data['SalePrice']
        ret.composition_exp = data['CompositionExp']
        ret.awakening_exp = data['AwakeningExp']
        ret.use_rank = data['UseRank']
        ret.group_no = data['GroupNo']
        ret.adaptable_appear_append = data['AdaptableAppearAppend']
        ret.punisher_appear_append = data['PunisherAppearAppend']
        ret.state = data['State']
        ret.passive_state = data['PassiveState']
        ret.power_default_value = data['PowerDefaultValue']
        ret.clt_default_value = data['CltDefaultValue']
        ret.awakening_1_power = data['Awakening1Power']
        ret.awakening_1_clt = data['Awakening1Clt']
        ret.awakening_2_power = data['Awakening2Power']
        ret.awakening_2_clt = data['Awakening2Clt']
        ret.awakening_3_power = data['Awakening3Power']
        ret.awakening_3_clt = data['Awakening3Clt']
        ret.awakening_4_power = data['Awakening4Power']
        ret.awakening_4_clt = data['Awakening4Clt']
        ret.awakening_5_power = data['Awakening5Power']
        ret.awakening_5_clt = data['Awakening5Clt']
        ret.normal_leader = data['NormalLeader']
        ret.holo_leader = data['HoloLeader']
        ret.ui_display_power_title = data['UiDisplayPowerTitle']
        ret.ui_display_power_content = data['UiDisplayPowerContent']
        ret.prefab = data['Prefab']
        ret.cutin_mode = data['CutinMode']
        ret.skill_voice_id = data['SkillVoiceId']
        ret.skill_name = data['SkillName']
        ret.name_in_skill_cutin = data['NameInSkillCutin']
        ret.skill_text = data['SkillText']
        ret.skill_text_in_skill_cutin = data['SkillTextInSkillCutin']
        ret.chara_info = data['CharaInfo']
        ret.cutin_image = data['CutinImage']
        ret.cutin_image_awake = data['CutinImageAwake']
        ret.status_chara_icon = data['StatusCharaIcon']
        ret.status_chara_icon_awake = data['StatusCharaIconAwake']
        ret.collection_display_start_date = data['CollectionDisplayStartDate']
        ret.collection_empty_frame_display_flag = data['CollectionEmptyFrameDisplayFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.support_log_id) \
        + encode_short(self.chara_id) \
        + encode_str(self.name) \
        + encode_byte(self.rarity) \
        + encode_short(self.support_log_type_id) \
        + encode_int(self.sale_price) \
        + encode_int(self.composition_exp) \
        + encode_int(self.awakening_exp) \
        + encode_short(self.use_rank) \
        + encode_short(self.group_no) \
        + encode_short(self.adaptable_appear_append) \
        + encode_short(self.punisher_appear_append) \
        + encode_str(self.state) \
        + encode_str(self.passive_state) \
        + encode_int(self.power_default_value) \
        + encode_int(self.clt_default_value) \
        + encode_int(self.awakening_1_power) \
        + encode_int(self.awakening_1_clt) \
        + encode_int(self.awakening_2_power) \
        + encode_int(self.awakening_2_clt) \
        + encode_int(self.awakening_3_power) \
        + encode_int(self.awakening_3_clt) \
        + encode_int(self.awakening_4_power) \
        + encode_int(self.awakening_4_clt) \
        + encode_int(self.awakening_5_power) \
        + encode_int(self.awakening_5_clt) \
        + encode_int(self.normal_leader) \
        + encode_int(self.holo_leader) \
        + encode_str(self.ui_display_power_title) \
        + encode_str(self.ui_display_power_content) \
        + encode_str(self.prefab) \
        + encode_str(self.cutin_mode) \
        + encode_str(self.skill_voice_id) \
        + encode_str(self.skill_name) \
        + encode_str(self.name_in_skill_cutin) \
        + encode_str(self.skill_text) \
        + encode_str(self.skill_text_in_skill_cutin) \
        + encode_str(self.chara_info) \
        + encode_str(self.cutin_image) \
        + encode_str(self.cutin_image_awake) \
        + encode_str(self.status_chara_icon) \
        + encode_str(self.status_chara_icon_awake) \
        + encode_date_str(self.collection_display_start_date) \
        + encode_byte(self.collection_empty_frame_display_flag)

class SupportLogTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.support_log_type_id = decode_short(data, off)
        off += SHORT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "SupportLogTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.support_log_type_id = data['SupportLogTypeId']
        ret.name = data['Name']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_short(self.support_log_type_id) \
        + encode_str(self.name)

class EpisodeAppendData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.episode_append_id = decode_int(data, off)
        off += INT_OFF

        self.episode_append_type = decode_byte(data, off)
        off += BYTE_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.sale_possible_flag = decode_int(data, off)
        off += INT_OFF

        self.sale_price = decode_int(data, off)
        off += INT_OFF

        self.episode_append_icon, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EpisodeAppendData":
        ret = cls(b"\x00" * 99, 0)
        ret.episode_append_id = data['EpisodeAppendId']
        ret.episode_append_type = data['EpisodeAppendType']
        ret.name = data['Name']
        ret.flavor_text = data['FlavorText']
        ret.sale_possible_flag = data['SalePossibleFlag']
        ret.sale_price = data['SalePrice']
        ret.episode_append_icon = data['EpisodeAppendIcon']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.episode_append_id) \
        + encode_byte(self.episode_append_type) \
        + encode_str(self.name) \
        + encode_str(self.flavor_text) \
        + encode_int(self.sale_possible_flag) \
        + encode_int(self.sale_price) \
        + encode_str(self.episode_append_icon)

class QuestDefragMatchQuestData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_quest_id = decode_int(data, off)
        off += INT_OFF

        self.quest_scene_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_quest_boss_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.display_name, new_off = decode_str(data, off)
        off += new_off

        self.map_no = decode_int(data, off)
        off += INT_OFF

        self.unit_data1, new_off = decode_str(data, off)
        off += new_off

        self.unit_data2, new_off = decode_str(data, off)
        off += new_off

        self.unit_data3, new_off = decode_str(data, off)
        off += new_off

        self.adaptable_rate, new_off = decode_str(data, off)
        off += new_off

        self.punisher_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.comment_details, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestDefragMatchQuestData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_quest_id = data['DefragMatchQuestId']
        ret.quest_scene_id = data['QuestSceneId']
        ret.defrag_match_quest_boss_table_sub_id = data['DefragMatchBossTableSubId']
        ret.display_name = data['DisplayName']
        ret.map_no = data['VsModeNo']
        ret.unit_data1 = data['UnitData1']
        ret.unit_data2 = data['UnitData2']
        ret.unit_data3 = data['UnitData3']
        ret.adaptable_rate = data['AdaptableRate']
        ret.punisher_flag = data['PunisherFlag']
        ret.comment_details = data['CommentDetails']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_quest_id) \
        + encode_int(self.quest_scene_id) \
        + encode_int(self.defrag_match_quest_boss_table_sub_id) \
        + encode_str(self.display_name) \
        + encode_int(self.map_no) \
        + encode_str(self.unit_data1) \
        + encode_str(self.unit_data2) \
        + encode_str(self.unit_data3) \
        + encode_str(self.adaptable_rate) \
        + encode_byte(self.punisher_flag) \
        + encode_str(self.comment_details)

class QuestDefragMatchQuestBossTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_quest_boss_table_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_quest_boss_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.wave = decode_int(data, off)
        off += INT_OFF

        self.type = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.rate = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestDefragMatchQuestBossTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_quest_boss_table_id = data['DefragMatchBossTableId']
        ret.defrag_match_quest_boss_table_sub_id = data['DefragMatchBossTableSubId']
        ret.wave = data['Wave']
        ret.type = data['Type']
        ret.unit_id = data['UnitId']
        ret.rate = data['Rate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_quest_boss_table_id) \
        + encode_int(self.defrag_match_quest_boss_table_sub_id) \
        + encode_int(self.wave) \
        + encode_int(self.type) \
        + encode_int(self.unit_id) \
        + encode_int(self.rate)

class DefragMatchData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.season_no = decode_short(data, off)
        off += SHORT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.first_attack_bonus_coefficient, new_off = decode_str(data, off)
        off += new_off

        self.last_attack_bonus_coefficient, new_off = decode_str(data, off)
        off += new_off

        self.memo, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_id = data['DefragMatchId']
        ret.season_no = data['SeasonNo']
        ret.title = data['Title']
        ret.first_attack_bonus_coefficient = data['FirstAttackBonusCoefficient']
        ret.last_attack_bonus_coefficient = data['LastAttackBonusCoefficient']
        ret.memo = data['Memo']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_id) \
        + encode_short(self.season_no) \
        + encode_str(self.title) \
        + encode_str(self.first_attack_bonus_coefficient) \
        + encode_str(self.last_attack_bonus_coefficient) \
        + encode_str(self.memo)

class DefragMatchSeedData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_seed_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.check_type = decode_byte(data, off)
        off += BYTE_OFF

        self.need_class_num = decode_short(data, off)
        off += SHORT_OFF

        self.need_cleared_trial_tower_id = decode_short(data, off)
        off += SHORT_OFF

        self.get_league_point = decode_int(data, off)
        off += INT_OFF

        self.get_league_score = decode_short(data, off)
        off += SHORT_OFF

        self.set_class_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchSeedData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_seed_id = data['DefragMatchSeedId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.check_type = data['CheckType']
        ret.need_class_num = data['NeedClassNum']
        ret.need_cleared_trial_tower_id = data['NeedClearedTrialTowerId']
        ret.get_league_point = data['GetLeaguePoint']
        ret.get_league_score = data['GetLeagueScore']
        ret.set_class_num = data['SetClassNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_seed_id) \
        + encode_int(self.defrag_match_id) \
        + encode_byte(self.check_type) \
        + encode_short(self.need_class_num) \
        + encode_short(self.need_cleared_trial_tower_id) \
        + encode_int(self.get_league_point) \
        + encode_short(self.get_league_score) \
        + encode_short(self.set_class_num)

class DefragMatchSpecialEffectData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_special_effec_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.special_effect_type = decode_byte(data, off)
        off += BYTE_OFF

        self.special_effect_coefficient, new_off = decode_str(data, off)
        off += new_off

        self.target_chara_id = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchSpecialEffectData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_special_effec_id = data['DefragMatchSpecialEffectsId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.special_effect_type = data['SpecialEffectType']
        ret.special_effect_coefficient = data['SpecialEffectCoefficient']
        ret.target_chara_id = data['TargetCharaId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_special_effec_id) \
        + encode_int(self.defrag_match_id) \
        + encode_byte(self.special_effect_type) \
        + encode_str(self.special_effect_coefficient) \
        + encode_short(self.target_chara_id)

class DefragMatchGradeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_grade_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.class_num = decode_short(data, off)
        off += SHORT_OFF

        self.grade_name, new_off = decode_str(data, off)
        off += new_off

        self.class_name, new_off = decode_str(data, off)
        off += new_off

        self.promotion_line_league_score = decode_short(data, off)
        off += SHORT_OFF

        self.demotion_line_league_score = decode_short(data, off)
        off += SHORT_OFF

        self.league_score_decrease_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.target_league_point_1 = decode_int(data, off)
        off += INT_OFF

        self.target_league_point_2 = decode_int(data, off)
        off += INT_OFF

        self.mvp_add_league_point = decode_int(data, off)
        off += INT_OFF

        self.mob_level = decode_short(data, off)
        off += SHORT_OFF

        self.normal_boss_level = decode_short(data, off)
        off += SHORT_OFF

        self.adaptable_level = decode_short(data, off)
        off += SHORT_OFF

        self.punisher_level = decode_short(data, off)
        off += SHORT_OFF

        self.punisher_appearance_rate, new_off = decode_str(data, off)
        off += new_off

        self.cpu_level = decode_short(data, off)
        off += SHORT_OFF

        self.record_medal_drop_num = decode_short(data, off)
        off += SHORT_OFF

        self.target_league_point_coefficient, new_off = decode_str(data, off)
        off += new_off

        self.reward_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchGradeData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_grade_id = data['DefragMatchGradeId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.class_num = data['ClassNum']
        ret.grade_name = data['GradeName']
        ret.class_name = data['ClassName']
        ret.promotion_line_league_score = data['PromotionLineLeagueScore']
        ret.demotion_line_league_score = data['DemotionLineLeagueScore']
        ret.league_score_decrease_flag = data['LeagueScoreDecreaseFlag']
        ret.target_league_point_1 = data['TargetLeaguePoint1']
        ret.target_league_point_2 = data['TargetLeaguePoint2']
        ret.mvp_add_league_point = data['MvpAddLeaguePoint']
        ret.mob_level = data['MobLevel']
        ret.normal_boss_level = data['NormalBossLevel']
        ret.adaptable_level = data['AdaptableLevel']
        ret.punisher_level = data['PunisherLevel']
        ret.punisher_appearance_rate = data['PunisherAppearanceRate']
        ret.cpu_level = data['CpuLevel']
        ret.record_medal_drop_num = data['RecordMedalDropNum']
        ret.target_league_point_coefficient = data['TargetLeaguePointCoefficient']
        ret.reward_table_sub_id = data['RewardTableSubId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_grade_id) \
        + encode_int(self.defrag_match_id) \
        + encode_short(self.class_num) \
        + encode_str(self.grade_name) \
        + encode_str(self.class_name) \
        + encode_short(self.promotion_line_league_score) \
        + encode_short(self.demotion_line_league_score) \
        + encode_byte(self.league_score_decrease_flag) \
        + encode_int(self.target_league_point_1) \
        + encode_int(self.target_league_point_2) \
        + encode_int(self.mvp_add_league_point) \
        + encode_short(self.mob_level) \
        + encode_short(self.normal_boss_level) \
        + encode_short(self.adaptable_level) \
        + encode_short(self.punisher_level) \
        + encode_str(self.punisher_appearance_rate) \
        + encode_short(self.cpu_level) \
        + encode_short(self.record_medal_drop_num) \
        + encode_str(self.target_league_point_coefficient) \
        + encode_int(self.reward_table_sub_id)

class DefragMatchCpuUnitData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_cpu_unit_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_start_defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_end_defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_start_class_num = decode_int(data, off)
        off += INT_OFF

        self.appearance_end_class_num = decode_int(data, off)
        off += INT_OFF

        self.hero_log_hero_log_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_log_level = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.hero_log_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.hero_log_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_equipment_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_enhancement_value = decode_short(data, off)
        off += SHORT_OFF

        self.main_weapon_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.main_weapon_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.main_weapon_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_equipment_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_enhancement_value = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equipment_awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self.sub_equipment_property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.sub_equipment_property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.skill_slot1_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_slot2_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_slot3_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_slot4_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self.skill_slot5_skill_id = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchCpuUnitData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_cpu_unit_id = data['DefragMatchCpuUnitsId']
        ret.appearance_start_defrag_match_id = data['AppearanceStartDefragMatchId']
        ret.appearance_end_defrag_match_id = data['AppearanceEndDefragMatchId']
        ret.appearance_start_class_num = data['AppearanceStartClassNum']
        ret.appearance_end_class_num = data['AppearanceEndClassNum']
        ret.hero_log_hero_log_id = data['HeroLogHeroLogId']
        ret.hero_log_log_level = data['HeroLogLogLevel']
        ret.hero_log_awakening_stage = data['HeroLogAwakeningStage']
        ret.hero_log_property1_property_id = data['HeroLogProperty1PropertyId']
        ret.hero_log_property1_value1 = data['HeroLogProperty1Value1']
        ret.hero_log_property1_value2 = data['HeroLogProperty1Value2']
        ret.hero_log_property2_property_id = data['HeroLogProperty2PropertyId']
        ret.hero_log_property2_value1 = data['HeroLogProperty2Value1']
        ret.hero_log_property2_value2 = data['HeroLogProperty2Value2']
        ret.hero_log_property3_property_id = data['HeroLogProperty3PropertyId']
        ret.hero_log_property3_value1 = data['HeroLogProperty3Value1']
        ret.hero_log_property3_value2 = data['HeroLogProperty3Value2']
        ret.hero_log_property4_property_id = data['HeroLogProperty4PropertyId']
        ret.hero_log_property4_value1 = data['HeroLogProperty4Value1']
        ret.hero_log_property4_value2 = data['HeroLogProperty4Value2']
        ret.main_weapon_equipment_id = data['MainWeaponEquipmentId']
        ret.main_weapon_enhancement_value = data['MainWeaponEnhancementValue']
        ret.main_weapon_awakening_stage = data['MainWeaponAwakeningStage']
        ret.main_weapon_property1_property_id = data['MainWeaponProperty1PropertyId']
        ret.main_weapon_property1_value1 = data['MainWeaponProperty1Value1']
        ret.main_weapon_property1_value2 = data['MainWeaponProperty1Value2']
        ret.main_weapon_property2_property_id = data['MainWeaponProperty2PropertyId']
        ret.main_weapon_property2_value1 = data['MainWeaponProperty2Value1']
        ret.main_weapon_property2_value2 = data['MainWeaponProperty2Value2']
        ret.main_weapon_property3_property_id = data['MainWeaponProperty3PropertyId']
        ret.main_weapon_property3_value1 = data['MainWeaponProperty3Value1']
        ret.main_weapon_property3_value2 = data['MainWeaponProperty3Value2']
        ret.main_weapon_property4_property_id = data['MainWeaponProperty4PropertyId']
        ret.main_weapon_property4_value1 = data['MainWeaponProperty4Value1']
        ret.main_weapon_property4_value2 = data['MainWeaponProperty4Value2']
        ret.sub_equipment_equipment_id = data['SubEquipmentEquipmentId']
        ret.sub_equipment_enhancement_value = data['SubEquipmentEnhancementValue']
        ret.sub_equipment_awakening_stage = data['SubEquipmentAwakeningStage']
        ret.sub_equipment_property1_property_id = data['SubEquipmentProperty1PropertyId']
        ret.sub_equipment_property1_value1 = data['SubEquipmentProperty1Value1']
        ret.sub_equipment_property1_value2 = data['SubEquipmentProperty1Value2']
        ret.sub_equipment_property2_property_id = data['SubEquipmentProperty2PropertyId']
        ret.sub_equipment_property2_value1 = data['SubEquipmentProperty2Value1']
        ret.sub_equipment_property2_value2 = data['SubEquipmentProperty2Value2']
        ret.sub_equipment_property3_property_id = data['SubEquipmentProperty3PropertyId']
        ret.sub_equipment_property3_value1 = data['SubEquipmentProperty3Value1']
        ret.sub_equipment_property3_value2 = data['SubEquipmentProperty3Value2']
        ret.sub_equipment_property4_property_id = data['SubEquipmentProperty4PropertyId']
        ret.sub_equipment_property4_value1 = data['SubEquipmentProperty4Value1']
        ret.sub_equipment_property4_value2 = data['SubEquipmentProperty4Value2']
        ret.skill_slot1_skill_id = data['SkillSlot1SkillId']
        ret.skill_slot2_skill_id = data['SkillSlot2SkillId']
        ret.skill_slot3_skill_id = data['SkillSlot3SkillId']
        ret.skill_slot4_skill_id = data['SkillSlot4SkillId']
        ret.skill_slot5_skill_id = data['SkillSlot5SkillId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_cpu_unit_id) \
        + encode_int(self.appearance_start_defrag_match_id) \
        + encode_int(self.appearance_end_defrag_match_id) \
        + encode_int(self.appearance_start_class_num) \
        + encode_int(self.appearance_end_class_num) \
        + encode_int(self.hero_log_hero_log_id) \
        + encode_short(self.hero_log_log_level) \
        + encode_short(self.hero_log_awakening_stage) \
        + encode_int(self.hero_log_property1_property_id) \
        + encode_int(self.hero_log_property1_value1) \
        + encode_int(self.hero_log_property1_value2) \
        + encode_int(self.hero_log_property2_property_id) \
        + encode_int(self.hero_log_property2_value1) \
        + encode_int(self.hero_log_property2_value2) \
        + encode_int(self.hero_log_property3_property_id) \
        + encode_int(self.hero_log_property3_value1) \
        + encode_int(self.hero_log_property3_value2) \
        + encode_int(self.hero_log_property4_property_id) \
        + encode_int(self.hero_log_property4_value1) \
        + encode_int(self.hero_log_property4_value2) \
        + encode_int(self.main_weapon_equipment_id) \
        + encode_short(self.main_weapon_enhancement_value) \
        + encode_short(self.main_weapon_awakening_stage) \
        + encode_int(self.main_weapon_property1_property_id) \
        + encode_int(self.main_weapon_property1_value1) \
        + encode_int(self.main_weapon_property1_value2) \
        + encode_int(self.main_weapon_property2_property_id) \
        + encode_int(self.main_weapon_property2_value1) \
        + encode_int(self.main_weapon_property2_value2) \
        + encode_int(self.main_weapon_property3_property_id) \
        + encode_int(self.main_weapon_property3_value1) \
        + encode_int(self.main_weapon_property3_value2) \
        + encode_int(self.main_weapon_property4_property_id) \
        + encode_int(self.main_weapon_property4_value1) \
        + encode_int(self.main_weapon_property4_value2) \
        + encode_int(self.sub_equipment_equipment_id) \
        + encode_short(self.sub_equipment_enhancement_value) \
        + encode_short(self.sub_equipment_awakening_stage) \
        + encode_int(self.sub_equipment_property1_property_id) \
        + encode_int(self.sub_equipment_property1_value1) \
        + encode_int(self.sub_equipment_property1_value2) \
        + encode_int(self.sub_equipment_property2_property_id) \
        + encode_int(self.sub_equipment_property2_value1) \
        + encode_int(self.sub_equipment_property2_value2) \
        + encode_int(self.sub_equipment_property3_property_id) \
        + encode_int(self.sub_equipment_property3_value1) \
        + encode_int(self.sub_equipment_property3_value2) \
        + encode_int(self.sub_equipment_property4_property_id) \
        + encode_int(self.sub_equipment_property4_value1) \
        + encode_int(self.sub_equipment_property4_value2) \
        + encode_short(self.skill_slot1_skill_id) \
        + encode_short(self.skill_slot2_skill_id) \
        + encode_short(self.skill_slot3_skill_id) \
        + encode_short(self.skill_slot4_skill_id) \
        + encode_short(self.skill_slot5_skill_id)

class DefragMatchCpuSupportLogData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_cpu_support_log_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_start_defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_end_defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.appearance_start_class_num = decode_int(data, off)
        off += INT_OFF

        self.appearance_end_class_num = decode_int(data, off)
        off += INT_OFF

        self.support_log_id = decode_int(data, off)
        off += INT_OFF

        self.awakening_stage = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchCpuSupportLogData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_cpu_support_log_id = data['DefragMatchCpuSupportLogId']
        ret.appearance_start_defrag_match_id = data['AppearanceStartDefragMatchId']
        ret.appearance_end_defrag_match_id = data['AppearanceEndDefragMatchId']
        ret.appearance_start_class_num = data['AppearanceStartClassNum']
        ret.appearance_end_class_num = data['AppearanceEndClassNum']
        ret.support_log_id = data['SupportLogId']
        ret.awakening_stage = data['AwakeningStage']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_cpu_support_log_id) \
        + encode_int(self.appearance_start_defrag_match_id) \
        + encode_int(self.appearance_end_defrag_match_id) \
        + encode_int(self.appearance_start_class_num) \
        + encode_int(self.appearance_end_class_num) \
        + encode_int(self.support_log_id) \
        + encode_short(self.awakening_stage)

class DefragMatchPeriodBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_period_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.bonus_type = decode_byte(data, off)
        off += BYTE_OFF

        self.param_1, new_off = decode_str(data, off)
        off += new_off

        self.param_2, new_off = decode_str(data, off)
        off += new_off

        self.param_3, new_off = decode_str(data, off)
        off += new_off

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchPeriodBonusData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_period_bonus_id = data['DefragMatchPeriodBonusId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.bonus_type = data['BonusType']
        ret.param_1 = data['Param1']
        ret.param_2 = data['Param2']
        ret.param_3 = data['Param3']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_period_bonus_id) \
        + encode_int(self.defrag_match_id) \
        + encode_byte(self.bonus_type) \
        + encode_str(self.param_1) \
        + encode_str(self.param_2) \
        + encode_str(self.param_3) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class DefragMatchRandomBonusTableData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_random_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_random_bonus_condition_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.condition_value1 = decode_int(data, off)
        off += INT_OFF

        self.condition_value2 = decode_int(data, off)
        off += INT_OFF

        self.get_league_point = decode_int(data, off)
        off += INT_OFF

        self.random_bonus_num = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchRandomBonusTableData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_random_bonus_id = data['DefragMatchRandomBonusId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.defrag_match_random_bonus_condition_id = data['DefragMatchRandomBonusConditionId']
        ret.name = data['Name']
        ret.condition_value1 = data['ConditionValue1']
        ret.condition_value2 = data['ConditionValue2']
        ret.get_league_point = data['GetLeaguePoint']
        ret.random_bonus_num = data['RandomBonusNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_random_bonus_id) \
        + encode_int(self.defrag_match_id) \
        + encode_int(self.defrag_match_random_bonus_condition_id) \
        + encode_str(self.name) \
        + encode_int(self.condition_value1) \
        + encode_int(self.condition_value2) \
        + encode_int(self.get_league_point) \
        + encode_byte(self.random_bonus_num)

class DefragMatchRandomBonusConditionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_random_bonus_condition_id = decode_int(data, off)
        off += INT_OFF

        self.format, new_off = decode_str(data, off)
        off += new_off

        self.hud_format, new_off = decode_str(data, off)
        off += new_off

        self.format_param_size = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchRandomBonusConditionData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_random_bonus_condition_id = data['DefragMatchRandomBonusConditionId']
        ret.format = data['Format']
        ret.hud_format = data['HudFormat']
        ret.format_param_size = data['FormatParamSize']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_random_bonus_condition_id) \
        + encode_str(self.format) \
        + encode_str(self.hud_format) \
        + encode_int(self.format_param_size)

class DefragMatchRareDropData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.defrag_match_rare_drop_id = decode_int(data, off)
        off += INT_OFF

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_int(data, off)
        off += INT_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_int(data, off)
        off += INT_OFF

        self.strength_min = decode_int(data, off)
        off += INT_OFF

        self.strength_max = decode_int(data, off)
        off += INT_OFF

        self.property_table_sub_id = decode_int(data, off)
        off += INT_OFF

        self.drop_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "DefragMatchRareDropData":
        ret = cls(b"\x00" * 99, 0)
        ret.defrag_match_rare_drop_id = data['DefragMatchRareDropId']
        ret.defrag_match_id = data['DefragMatchId']
        ret.unit_id = data['UnitId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength_min = data['StrengthMin']
        ret.strength_max = data['StrengthMax']
        ret.property_table_sub_id = data['PropertyTableSubId']
        ret.drop_rate = data['DropRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.defrag_match_rare_drop_id) \
        + encode_int(self.defrag_match_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_int(self.common_reward_num) \
        + encode_int(self.strength_min) \
        + encode_int(self.strength_max) \
        + encode_int(self.property_table_sub_id) \
        + encode_str(self.drop_rate)

class YuiMedalShopData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.yui_medal_shop_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.description, new_off = decode_str(data, off)
        off += new_off

        self.selling_yui_medal = decode_short(data, off)
        off += SHORT_OFF

        self.selling_col = decode_int(data, off)
        off += INT_OFF

        self.selling_event_item_id = decode_int(data, off)
        off += INT_OFF

        self.selling_event_item_num = decode_int(data, off)
        off += INT_OFF

        self.selling_ticket_num = decode_int(data, off)
        off += INT_OFF

        self.purchase_limit = decode_short(data, off)
        off += SHORT_OFF

        self.pick_up_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.product_category = decode_byte(data, off)
        off += BYTE_OFF

        self.sales_type = decode_byte(data, off)
        off += BYTE_OFF

        self.target_days = decode_byte(data, off)
        off += BYTE_OFF

        self.target_hour = decode_byte(data, off)
        off += BYTE_OFF

        self.interval_hour = decode_byte(data, off)
        off += BYTE_OFF

        self.sales_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.sales_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.sort = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "YuiMedalShopData":
        ret = cls(b"\x00" * 99, 0)
        ret.yui_medal_shop_id = data['YuiMedalShopId']
        ret.name = data['Name']
        ret.description = data['Description']
        ret.selling_yui_medal = data['SellingYuiMedal']
        ret.selling_col = data['SellingCol']
        ret.selling_event_item_id = data['SellingEventItemId']
        ret.selling_event_item_num = data['SellingEventItemNum']
        ret.selling_ticket_num = data['SellingTicketNum']
        ret.purchase_limit = data['PurchaseLimit']
        ret.pick_up_flag = data['PickUpFlag']
        ret.product_category = data['ProductCategory']
        ret.sales_type = data['SalesType']
        ret.target_days = data['TargetDays']
        ret.target_hour = data['TargetHour']
        ret.interval_hour = data['IntervalHour']
        ret.sales_start_date = data['SalesStartDate']
        ret.sales_end_date = data['SalesEndDate']
        ret.sort = data['Sort']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.yui_medal_shop_id) \
        + encode_str(self.name) \
        + encode_str(self.description) \
        + encode_short(self.selling_yui_medal) \
        + encode_int(self.selling_col) \
        + encode_int(self.selling_event_item_id) \
        + encode_int(self.selling_event_item_num) \
        + encode_int(self.selling_ticket_num) \
        + encode_short(self.purchase_limit) \
        + encode_byte(self.pick_up_flag) \
        + encode_byte(self.product_category) \
        + encode_byte(self.sales_type) \
        + encode_byte(self.target_days) \
        + encode_byte(self.target_hour) \
        + encode_byte(self.interval_hour) \
        + encode_date_str(self.sales_start_date) \
        + encode_date_str(self.sales_end_date) \
        + encode_byte(self.sort)

class YuiMedalShopItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.yui_medal_shop_item_id = decode_int(data, off)
        off += INT_OFF

        self.yui_medal_shop_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "YuiMedalShopItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.yui_medal_shop_item_id = data['YuiMedalShopItemId']
        ret.yui_medal_shop_id = data['YuiMedalShopId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.yui_medal_shop_item_id) \
        + encode_int(self.yui_medal_shop_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class EventSceneData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.event_scene_id = decode_int(data, off)
        off += INT_OFF

        self.event_id = decode_int(data, off)
        off += INT_OFF

        self.scene_type = decode_byte(data, off)
        off += BYTE_OFF

        self.episode_no = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.param_1, new_off = decode_str(data, off)
        off += new_off

        self.param_2, new_off = decode_str(data, off)
        off += new_off

        self.param_3, new_off = decode_str(data, off)
        off += new_off

        self.adv_name, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EventSceneData":
        ret = cls(b"\x00" * 99, 0)
        ret.event_scene_id = data['EventSceneId']
        ret.event_id = data['EventId']
        ret.scene_type = data['SceneType']
        ret.episode_no = data['EpisodeNo']
        ret.title = data['Title']
        ret.param_1 = data['Param1']
        ret.param_2 = data['Param2']
        ret.param_3 = data['Param3']
        ret.adv_name = data['AdvName']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.event_scene_id) \
        + encode_int(self.event_id) \
        + encode_byte(self.scene_type) \
        + encode_int(self.episode_no) \
        + encode_str(self.title) \
        + encode_str(self.param_1) \
        + encode_str(self.param_2) \
        + encode_str(self.param_3) \
        + encode_str(self.adv_name)

class GenericCampaignPeriodData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.generic_campaign_period_id = decode_int(data, off)
        off += INT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GenericCampaignPeriodData":
        ret = cls(b"\x00" * 99, 0)
        ret.generic_campaign_period_id = data['GenericCampaignPeriodId']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.generic_campaign_period_id) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class BeginnerMissionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_id = data['BeginnerMissionId']
        ret.name = data['Name']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_id) \
        + encode_str(self.name) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class BeginnerMissionConditionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_condition_id = decode_int(data, off)
        off += INT_OFF

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

        self.seat_num = decode_short(data, off)
        off += SHORT_OFF

        self.mission_num = decode_short(data, off)
        off += SHORT_OFF

        self.display_content, new_off = decode_str(data, off)
        off += new_off

        self.display_tips, new_off = decode_str(data, off)
        off += new_off

        self.condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_param_1, new_off = decode_str(data, off)
        off += new_off

        self.condition_param_2, new_off = decode_str(data, off)
        off += new_off

        self.condition_param_3, new_off = decode_str(data, off)
        off += new_off

        self.required_achievement_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionConditionData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_condition_id = data['BeginnerMissionConditionId']
        ret.beginner_mission_id = data['BeginnerMissionId']
        ret.seat_num = data['SeatNum']
        ret.mission_num = data['MissionNum']
        ret.display_content = data['DisplayContent']
        ret.display_tips = data['DisplayTips']
        ret.condition_type = data['ConditionType']
        ret.condition_param_1 = data['ConditionParam1']
        ret.condition_param_2 = data['ConditionParam2']
        ret.condition_param_3 = data['ConditionParam3']
        ret.required_achievement_num = data['RequiredAchievementNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_condition_id) \
        + encode_int(self.beginner_mission_id) \
        + encode_short(self.seat_num) \
        + encode_short(self.mission_num) \
        + encode_str(self.display_content) \
        + encode_str(self.display_tips) \
        + encode_byte(self.condition_type) \
        + encode_str(self.condition_param_1) \
        + encode_str(self.condition_param_2) \
        + encode_str(self.condition_param_3) \
        + encode_short(self.required_achievement_num)

class BeginnerMissionRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

        self.beginner_mission_condition_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_id = data['BeginnerMissionId']
        ret.beginner_mission_condition_id = data['BeginnerMissionConditionId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_id) \
        + encode_int(self.beginner_mission_condition_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class BeginnerMissionSeatConditionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

        self.beginner_mission_seat_condition_id = decode_int(data, off)
        off += INT_OFF

        self.seat_num = decode_short(data, off)
        off += SHORT_OFF

        self.mission_seat_num = decode_short(data, off)
        off += SHORT_OFF

        self.display_content, new_off = decode_str(data, off)
        off += new_off

        self.display_tips, new_off = decode_str(data, off)
        off += new_off

        self.condition_type = decode_byte(data, off)
        off += BYTE_OFF

        self.condition_param_1, new_off = decode_str(data, off)
        off += new_off

        self.condition_param_2, new_off = decode_str(data, off)
        off += new_off

        self.condition_param_3, new_off = decode_str(data, off)
        off += new_off

        self.required_achievement_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionSeatConditionData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_id = data['BeginnerMissionId']
        ret.beginner_mission_seat_condition_id = data['BeginnerMissionSeatConditionId']
        ret.seat_num = data['SeatNum']
        ret.mission_seat_num = data['MissionSeatNum']
        ret.display_content = data['DisplayContent']
        ret.display_tips = data['DisplayTips']
        ret.condition_type = data['ConditionType']
        ret.condition_param_1 = data['ConditionParam1']
        ret.condition_param_2 = data['ConditionParam2']
        ret.condition_param_3 = data['ConditionParam3']
        ret.required_achievement_num = data['RequiredAchievementNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_id) \
        + encode_int(self.beginner_mission_seat_condition_id) \
        + encode_short(self.seat_num) \
        + encode_short(self.mission_seat_num) \
        + encode_str(self.display_content) \
        + encode_str(self.display_tips) \
        + encode_byte(self.condition_type) \
        + encode_str(self.condition_param_1) \
        + encode_str(self.condition_param_2) \
        + encode_str(self.condition_param_3) \
        + encode_short(self.required_achievement_num)

class BeginnerMissionSeatRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

        self.beginner_mission_seat_condition_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "BeginnerMissionSeatRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.beginner_mission_id = data['BeginnerMissionId']
        ret.beginner_mission_seat_condition_id = data['BeginnerMissionSeatConditionId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.beginner_mission_id) \
        + encode_int(self.beginner_mission_seat_condition_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class EventItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.event_item_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.flavor_text, new_off = decode_str(data, off)
        off += new_off

        self.event_item_icon, new_off = decode_str(data, off)
        off += new_off

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EventItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.event_item_id = data['EventItemId']
        ret.name = data['Name']
        ret.flavor_text = data['FlavorText']
        ret.event_item_icon = data['EventItemIcon']
        ret.unit_id = data['UnitId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.event_item_id) \
        + encode_str(self.name) \
        + encode_str(self.flavor_text) \
        + encode_str(self.event_item_icon) \
        + encode_int(self.unit_id)

class EventMonsterData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.event_monster_id = decode_int(data, off)
        off += INT_OFF

        self.event_id = decode_int(data, off)
        off += INT_OFF

        self.unit_id = decode_int(data, off)
        off += INT_OFF

        self.event_item_id = decode_int(data, off)
        off += INT_OFF

        self.drop_rate, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "EventMonsterData":
        ret = cls(b"\x00" * 99, 0)
        ret.event_monster_id = data['EventMonsterId']
        ret.event_id = data['EventId']
        ret.unit_id = data['UnitId']
        ret.event_item_id = data['EventItemId']
        ret.drop_rate = data['DropRate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.event_monster_id) \
        + encode_int(self.event_id) \
        + encode_int(self.unit_id) \
        + encode_int(self.event_item_id) \
        + encode_str(self.drop_rate)

class YuiMedalBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.yui_medal_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "YuiMedalBonusData":
        ret = cls(b"\x00" * 99, 0)
        ret.yui_medal_bonus_id = data['YuiMedalBonusId']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.yui_medal_bonus_id) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class YuiMedalBonusConditionData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.yui_medal_bonus_condition_id = decode_int(data, off)
        off += INT_OFF

        self.yui_medal_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.target_days = decode_int(data, off)
        off += INT_OFF

        self.get_num = decode_int(data, off)
        off += INT_OFF

        self.loop_flag = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "YuiMedalBonusConditionData":
        ret = cls(b"\x00" * 99, 0)
        ret.yui_medal_bonus_condition_id = data['YuiMedalBonusConditionId']
        ret.yui_medal_bonus_id = data['YuiMedalBonusId']
        ret.target_days = data['TargetDays']
        ret.get_num = data['GetNum']
        ret.loop_flag = data['LoopFlag']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.yui_medal_bonus_condition_id) \
        + encode_int(self.yui_medal_bonus_id) \
        + encode_int(self.target_days) \
        + encode_int(self.get_num) \
        + encode_byte(self.loop_flag)

class GashaMedalData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_medal_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_medal_type = decode_byte(data, off)
        off += BYTE_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_medal_id = data['GashaMedalId']
        ret.gasha_medal_type = data['GashaMedalType']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_medal_id) \
        + encode_byte(self.gasha_medal_type)

class GashaMedalTypeData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_medal_type = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.medal_icon, new_off = decode_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalTypeData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_medal_type = data['GashaMedalType']
        ret.name = data['Name']
        ret.medal_icon = data['MedalIcon']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_medal_type) \
        + encode_str(self.name) \
        + encode_str(self.medal_icon)

class GashaMedalSettingData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_medal_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalSettingData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_id = data['GashaId']
        ret.gasha_medal_id = data['GashaMedalId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_id) \
        + encode_int(self.gasha_medal_id)

class GashaMedalBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.analyze_amount = decode_byte(data, off)
        off += BYTE_OFF

        self.get_gasha_medal_num = decode_int(data, off)
        off += INT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalBonusData":
        ret = cls(b"\x00" * 99, 0)
        ret.analyze_amount = data['AnalyzeAmount']
        ret.get_gasha_medal_num = data['GetGashaMedalNum']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.analyze_amount) \
        + encode_int(self.get_gasha_medal_num) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class GashaMedalShopData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_medal_shop_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.gasha_medal_id = decode_int(data, off)
        off += INT_OFF

        self.use_gasha_medal_num = decode_int(data, off)
        off += INT_OFF

        self.purchase_limit = decode_short(data, off)
        off += SHORT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalShopData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_medal_shop_id = data['GashaMedalShopId']
        ret.name = data['Name']
        ret.gasha_medal_id = data['GashaMedalId']
        ret.use_gasha_medal_num = data['UseGashaMedalNum']
        ret.purchase_limit = data['PurchaseLimit']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_medal_shop_id) \
        + encode_str(self.name) \
        + encode_int(self.gasha_medal_id) \
        + encode_int(self.use_gasha_medal_num) \
        + encode_short(self.purchase_limit) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class GashaMedalShopItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_medal_shop_item_id = decode_int(data, off)
        off += INT_OFF

        self.gasha_medal_shop_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaMedalShopItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_medal_shop_item_id = data['GashaMedalShopItemId']
        ret.gasha_medal_shop_id = data['GashaMedalShopId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_medal_shop_item_id) \
        + encode_int(self.gasha_medal_shop_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class ResEarnCampaignApplicationData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.res_earn_campaign_application_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.news_id, new_off = decode_str(data, off)
        off += new_off

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ResEarnCampaignApplicationData":
        ret = cls(b"\x00" * 99, 0)
        ret.res_earn_campaign_application_id = data['ResEarnCampaignApplicationId']
        ret.title = data['Title']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.posting_start_date = data['PostingStartDate']
        ret.posting_end_date = data['PostingEndDate']
        ret.news_id = data['NewsId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.res_earn_campaign_application_id) \
        + encode_str(self.title) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_date_str(self.posting_start_date) \
        + encode_date_str(self.posting_end_date) \
        + encode_str(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class ResEarnCampaignApplicationProductData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.res_earn_campaign_application_product_id = decode_int(data, off)
        off += INT_OFF

        self.res_earn_campaign_application_id = decode_int(data, off)
        off += INT_OFF

        self.award_name, new_off = decode_str(data, off)
        off += new_off

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.need_application_point = decode_short(data, off)
        off += SHORT_OFF

        self.winning_num = decode_short(data, off)
        off += SHORT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ResEarnCampaignApplicationProductData":
        ret = cls(b"\x00" * 99, 0)
        ret.res_earn_campaign_application_product_id = data['ResEarnCampaignApplicationProductId']
        ret.res_earn_campaign_application_id = data['ResEarnCampaignApplicationId']
        ret.award_name = data['AwardName']
        ret.name = data['Name']
        ret.need_application_point = data['NeedApplicationPoint']
        ret.winning_num = data['WinningNum']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.res_earn_campaign_application_product_id) \
        + encode_int(self.res_earn_campaign_application_id) \
        + encode_str(self.award_name) \
        + encode_str(self.name) \
        + encode_short(self.need_application_point) \
        + encode_short(self.winning_num)

class ResEarnCampaignShopData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.res_earn_campaign_shop_id = decode_int(data, off)
        off += INT_OFF

        self.res_earn_campaign_application_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.selling_yui_medal = decode_short(data, off)
        off += SHORT_OFF

        self.selling_col = decode_int(data, off)
        off += INT_OFF

        self.selling_event_item_id = decode_int(data, off)
        off += INT_OFF

        self.selling_event_item_num = decode_int(data, off)
        off += INT_OFF

        self.purchase_limit = decode_short(data, off)
        off += SHORT_OFF

        self.get_application_point = decode_short(data, off)
        off += SHORT_OFF

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ResEarnCampaignShopData":
        ret = cls(b"\x00" * 99, 0)
        ret.res_earn_campaign_shop_id = data['ResEarnCampaignShopId']
        ret.res_earn_campaign_application_id = data['ResEarnCampaignApplicationId']
        ret.name = data['Name']
        ret.selling_yui_medal = data['SellingYuiMedal']
        ret.selling_col = data['SellingCol']
        ret.selling_event_item_id = data['SellingEventItemId']
        ret.selling_event_item_num = data['SellingEventItemNum']
        ret.purchase_limit = data['PurchaseLimit']
        ret.get_application_point = data['GetApplicationPoint']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.res_earn_campaign_shop_id) \
        + encode_int(self.res_earn_campaign_application_id) \
        + encode_str(self.name) \
        + encode_short(self.selling_yui_medal) \
        + encode_int(self.selling_col) \
        + encode_int(self.selling_event_item_id) \
        + encode_int(self.selling_event_item_num) \
        + encode_short(self.purchase_limit) \
        + encode_short(self.get_application_point) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class ResEarnCampaignShopItemData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.res_earn_campaign_shop_item_id = decode_int(data, off)
        off += INT_OFF

        self.res_earn_campaign_shop_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "ResEarnCampaignShopItemData":
        ret = cls(b"\x00" * 99, 0)
        ret.res_earn_campaign_shop_item_id = data['ResEarnCampaignShopItemId']
        ret.res_earn_campaign_shop_id = data['ResEarnCampaignShopId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.res_earn_campaign_shop_item_id) \
        + encode_int(self.res_earn_campaign_shop_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class PayingYuiMedalBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.paying_yui_medal_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.reward_yui_medal_num = decode_int(data, off)
        off += INT_OFF

        self.news_id, new_off = decode_str(data, off)
        off += new_off

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PayingYuiMedalBonusData":
        ret = cls(b"\x00" * 99, 0)
        ret.paying_yui_medal_bonus_id = data['PayingYuiMedalBonusId']
        ret.title = data['Title']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.reward_yui_medal_num = data['RewardYuiMedalNum']
        ret.news_id = data['NewsId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.paying_yui_medal_bonus_id) \
        + encode_str(self.title) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_int(self.reward_yui_medal_num) \
        + encode_str(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class AcLoginBonusData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.ac_login_bonus_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.reward_set_sub_id = decode_int(data, off)
        off += INT_OFF

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "AcLoginBonusData":
        ret = cls(b"\x00" * 99, 0)
        ret.ac_login_bonus_id = data['AcLoginBonusId']
        ret.title = data['Title']
        ret.reward_set_sub_id = data['RewardSetSubId']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.ac_login_bonus_id) \
        + encode_str(self.title) \
        + encode_int(self.reward_set_sub_id) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date)

class PlayCampaignData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.play_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.campaign_type = decode_byte(data, off)
        off += BYTE_OFF

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.news_id, new_off = decode_str(data, off)
        off += new_off

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PlayCampaignData":
        ret = cls(b"\x00" * 99, 0)
        ret.play_campaign_id = data['PlayCampaignId']
        ret.title = data['Title']
        ret.campaign_type = data['CampaignType']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.posting_start_date = data['PostingStartDate']
        ret.posting_end_date = data['PostingEndDate']
        ret.news_id = data['NewsId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.play_campaign_id) \
        + encode_str(self.title) \
        + encode_byte(self.campaign_type) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_date_str(self.posting_start_date) \
        + encode_date_str(self.posting_end_date) \
        + encode_str(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class PlayCampaignRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.play_campaign_reward_id = decode_int(data, off)
        off += INT_OFF

        self.play_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.product_no = decode_int(data, off)
        off += INT_OFF

        self.product_name, new_off = decode_str(data, off)
        off += new_off

        self.product_type = decode_byte(data, off)
        off += BYTE_OFF

        self.resource_type = decode_byte(data, off)
        off += BYTE_OFF

        self.required_credit_num = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self.title_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "PlayCampaignRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.play_campaign_reward_id = data['PlayCampaignRewardId']
        ret.play_campaign_id = data['PlayCampaignId']
        ret.product_no = data['ProductNo']
        ret.product_name = data['ProductName']
        ret.product_type = data['ProductType']
        ret.resource_type = data['ResourceType']
        ret.required_credit_num = data['RequiredCreditNum']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        ret.title_id = data['TitleId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.play_campaign_reward_id) \
        + encode_int(self.play_campaign_id) \
        + encode_int(self.product_no) \
        + encode_str(self.product_name) \
        + encode_byte(self.product_type) \
        + encode_byte(self.resource_type) \
        + encode_int(self.required_credit_num) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2) \
        + encode_int(self.title_id)

class GashaFreeCampaignData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.gasha_free_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "GashaFreeCampaignData":
        ret = cls(b"\x00" * 99, 0)
        ret.gasha_free_campaign_id = data['GashaFreeCampaignId']
        ret.name = data['Name']
        ret.start_date = data['StartDate']
        ret.end_date = data['EndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.gasha_free_campaign_id) \
        + encode_str(self.name) \
        + encode_date_str(self.start_date) \
        + encode_date_str(self.end_date)

class QuestDropBoostCampaignData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.quest_drop_boost_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.name, new_off = decode_str(data, off)
        off += new_off

        self.consume_ticket_num = decode_int(data, off)
        off += INT_OFF

        self.drop_magnification = decode_byte(data, off)
        off += BYTE_OFF

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "QuestDropBoostCampaignData":
        ret = cls(b"\x00" * 99, 0)
        ret.quest_drop_boost_campaign_id = data['QuestDropBoostCampaignId']
        ret.name = data['Name']
        ret.consume_ticket_num = data['ConsumeTicketNum']
        ret.drop_magnification = data['DropMagnification']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.quest_drop_boost_campaign_id) \
        + encode_str(self.name) \
        + encode_int(self.consume_ticket_num) \
        + encode_byte(self.drop_magnification) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date)

class FirstTicketPurchaseCampaignData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.first_ticket_purchase_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.not_target_applying_base_date, new_off = decode_date_str(data, off)
        off += new_off

        self.target_ticket_purchase_id_list, new_off = decode_str(data, off)
        off += new_off

        self.news_id, new_off = decode_str(data, off)
        off += new_off

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "FirstTicketPurchaseCampaignData":
        ret = cls(b"\x00" * 99, 0)
        ret.first_ticket_purchase_campaign_id = data['FirstTicketPurchaseCampaignId']
        ret.title = data['Title']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.not_target_applying_base_date = data['NotTargetApplyingBaseDate']
        ret.target_ticket_purchase_id_list = data['TargetTicketPurchaseIdList']
        ret.news_id = data['NewsId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.first_ticket_purchase_campaign_id) \
        + encode_str(self.title) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_date_str(self.not_target_applying_base_date) \
        + encode_str(self.target_ticket_purchase_id_list) \
        + encode_str(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class LinkedSiteRegCampaignsData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.linked_site_reg_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.title, new_off = decode_str(data, off)
        off += new_off

        self.open_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.open_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_start_date, new_off = decode_date_str(data, off)
        off += new_off

        self.posting_end_date, new_off = decode_date_str(data, off)
        off += new_off

        self.news_id, new_off = decode_str(data, off)
        off += new_off

        self.help_id = decode_int(data, off)
        off += INT_OFF

        self.ad_banner_id = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "LinkedSiteRegCampaignsData":
        ret = cls(b"\x00" * 99, 0)
        ret.linked_site_reg_campaign_id = data['LinkedSiteRegCampaignId']
        ret.title = data['Title']
        ret.open_start_date = data['OpenStartDate']
        ret.open_end_date = data['OpenEndDate']
        ret.posting_start_date = data['PostingStartDate']
        ret.posting_end_date = data['PostingEndDate']
        ret.news_id = data['NewsId']
        ret.help_id = data['HelpId']
        ret.ad_banner_id = data['AdBannerId']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.linked_site_reg_campaign_id) \
        + encode_str(self.title) \
        + encode_date_str(self.open_start_date) \
        + encode_date_str(self.open_end_date) \
        + encode_date_str(self.posting_start_date) \
        + encode_date_str(self.posting_end_date) \
        + encode_str(self.news_id) \
        + encode_int(self.help_id) \
        + encode_int(self.ad_banner_id)

class LinkedSiteRegCampaignRewardData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.linked_site_reg_campaign_reward_id = decode_int(data, off)
        off += INT_OFF

        self.linked_site_reg_campaign_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_type = decode_byte(data, off)
        off += BYTE_OFF

        self.common_reward_id = decode_int(data, off)
        off += INT_OFF

        self.common_reward_num = decode_short(data, off)
        off += SHORT_OFF

        self.strength = decode_int(data, off)
        off += INT_OFF

        self.property1_property_id = decode_int(data, off)
        off += INT_OFF

        self.property1_value1 = decode_int(data, off)
        off += INT_OFF

        self.property1_value2 = decode_int(data, off)
        off += INT_OFF

        self.property2_property_id = decode_int(data, off)
        off += INT_OFF

        self.property2_value1 = decode_int(data, off)
        off += INT_OFF

        self.property2_value2 = decode_int(data, off)
        off += INT_OFF

        self.property3_property_id = decode_int(data, off)
        off += INT_OFF

        self.property3_value1 = decode_int(data, off)
        off += INT_OFF

        self.property3_value2 = decode_int(data, off)
        off += INT_OFF

        self.property4_property_id = decode_int(data, off)
        off += INT_OFF

        self.property4_value1 = decode_int(data, off)
        off += INT_OFF

        self.property4_value2 = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, data: Dict) -> "LinkedSiteRegCampaignRewardData":
        ret = cls(b"\x00" * 99, 0)
        ret.linked_site_reg_campaign_reward_id = data['LinkedSiteRegCampaignRewardId']
        ret.linked_site_reg_campaign_id = data['LinkedSiteRegCampaignId']
        ret.common_reward_type = data['CommonRewardType']
        ret.common_reward_id = data['CommonRewardId']
        ret.common_reward_num = data['CommonRewardNum']
        ret.strength = data['Strength']
        ret.property1_property_id = data['Property1PropertyId']
        ret.property1_value1 = data['Property1Value1']
        ret.property1_value2 = data['Property1Value2']
        ret.property2_property_id = data['Property2PropertyId']
        ret.property2_value1 = data['Property2Value1']
        ret.property2_value2 = data['Property2Value2']
        ret.property3_property_id = data['Property3PropertyId']
        ret.property3_value1 = data['Property3Value1']
        ret.property3_value2 = data['Property3Value2']
        ret.property4_property_id = data['Property4PropertyId']
        ret.property4_value1 = data['Property4Value1']
        ret.property4_value2 = data['Property4Value2']
        return ret

    def make(self) -> bytes:
        return super().make() \
        + encode_int(self.linked_site_reg_campaign_reward_id) \
        + encode_int(self.linked_site_reg_campaign_id) \
        + encode_byte(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_short(self.common_reward_num) \
        + encode_int(self.strength) \
        + encode_int(self.property1_property_id) \
        + encode_int(self.property1_value1) \
        + encode_int(self.property1_value2) \
        + encode_int(self.property2_property_id) \
        + encode_int(self.property2_value1) \
        + encode_int(self.property2_value2) \
        + encode_int(self.property3_property_id) \
        + encode_int(self.property3_value1) \
        + encode_int(self.property3_value2) \
        + encode_int(self.property4_property_id) \
        + encode_int(self.property4_value1) \
        + encode_int(self.property4_value2)

class EpisodeAppendUserData(BaseHelper):
    def __init__(self, data: bytes, offset: int):
        off = offset
        self.user_episode_append_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.episode_append_id = decode_int(data, off)
        off += INT_OFF

        self.own_num = decode_int(data, off)
        off += INT_OFF

        self._sz = off - offset

    @classmethod
    def from_args(cls, episode_id: int = 0, user_id: int = 0, episode_append_id: int = 0, own_num: int = 99) -> "EpisodeAppendUserData":
        ret = cls(b"\x00" * 996, 0)
        ret.user_episode_append_id = episode_id
        ret.user_id = user_id
        ret.episode_append_id = episode_append_id
        ret.own_num = own_num

    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.user_episode_append_id) \
        + encode_str(self.user_id) \
        + encode_int(self.episode_append_id) \
        + encode_int(self.own_num)
