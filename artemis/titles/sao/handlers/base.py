import struct
from datetime import datetime
from typing import List, Union
from .helpers import *

from ..const import GameconnectCmd

class SaoRequestHeader:
    def __init__(self, data: bytes) -> None:
        collection = struct.unpack_from("!HHIIII16sI", data)
        self.cmd: int = collection[0]
        self.err_status = collection[1]
        self.error_type = collection[2]
        self.vendor_id: int = collection[3]
        self.game_id: int = collection[4]
        self.version_id: int = collection[5]
        self.hash: str = collection[6]
        self.data_len: str = collection[7]

class SaoBaseRequest:
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        self.header = header

class SaoResponseHeader:
    def __init__(self, cmd_id: GameconnectCmd) -> None:
        self.cmd = cmd_id
        self.err_status = 0
        self.error_type = 0
        self.vendor_id = 5
        self.game_id = 1
        self.version_id = 1
        self.length = 1
    
    def make(self) -> bytes:
        return struct.pack("!HHIIIII", self.cmd, self.err_status, self.error_type, self.vendor_id, self.game_id, self.version_id, self.length)

class SaoBaseResponse:
    def __init__(self, cmd_id: Union[GameconnectCmd, int]) -> None:
        if type(cmd_id) == int:
            cmd = GameconnectCmd(cmd_id)
        else:
            cmd = cmd_id
        self.header = SaoResponseHeader(cmd)
    
    def make(self) -> bytes:
        return self.header.make()

class SaoGenericUserTicketRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        ticket_id = decode_str(data, off)
        self.ticket_id = ticket_id[0]
        off += ticket_id[1]

        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

class SaoGenericUserRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoNoopRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.dummy = decode_byte(data, 0)

class SaoNoopResponse(SaoBaseResponse):
    def __init__(self, cmd: int) -> None:
        super().__init__(cmd)      
        self.result = 1
        self.length = 5

    def make(self) -> bytes:
        return super().make() + struct.pack("!bI", self.result, 0)

class SaoTicketRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoTicketResponse(SaoBaseResponse):
    def __init__(self, ticket_id: str = "9") -> None:
        super().__init__(GameconnectCmd.TICKET_RESPONSE)
        self.result = "1"
        self.ticket_id = ticket_id
    
    def make(self) -> bytes:
        return super().make() \
        + encode_str(self.result) \
        + encode_str(self.ticket_id)

class SaoGetMaintenanceInfoResponse(SaoBaseResponse):
    def __init__(self, maint_start: datetime = datetime.fromtimestamp(0), maint_end: datetime = datetime.fromtimestamp(0)) -> None:
        super().__init__(GameconnectCmd.GET_MAINTENANCE_INFO_RESPONSE)
        self.result = 1
        self.maint_begin = maint_start
        self.maint_end = maint_end
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_date_str(self.maint_begin) \
        + encode_date_str(self.maint_end)

class SaoCommonAcCabinetBootNotificationRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.current_version_app_id = decode_int(data, off)
        off += INT_OFF

        self.current_master_data_version = decode_int(data, off)
        off += INT_OFF

class SaoMasterDataVersionCheckRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        self.current_data_version = decode_int(data, 0)

class SaoMasterDataVersionCheckResponse(SaoBaseResponse):
    def __init__(self, current_ver: int, game_ver: int) -> None:
        super().__init__(GameconnectCmd.MASTER_DATA_VERSION_CHECK_RESPONSE)
        self.result = 1
        self.update_flag = 1 if game_ver != current_ver else 0
        self.data_version = current_ver
    
    def make(self) -> bytes:
        resp_data = encode_byte(self.result)
        resp_data += encode_byte(self.update_flag)
        resp_data += encode_int(self.data_version)
        return super().make() + resp_data

class SaoGetAppVersionsResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_APP_VERSIONS_RESPONSE)
        self.result = 1
        self.data_list: List[AppVersionData] = []
    
    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.data_list)
        return super().make() + ret

class SaoPayingPlayStartRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.paying_user_id, new_off = decode_str(data, off)
        off += new_off

        self.game_sub_id, new_off = decode_str(data, off)
        off += new_off

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

class SaoPayingPlayStartResponse(SaoBaseResponse):
    def __init__(self, session_id: str = "1") -> None:
        super().__init__(GameconnectCmd.PAYING_PLAY_START_RESPONSE)
        self.result = 1
        self.paying_session_id = session_id
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.paying_session_id)

class SaoPayingPlayEndRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.paying_session_id, new_off = decode_str(data, off)
        off += new_off

        self.paying_user_id, new_off = decode_str(data, off)
        off += new_off

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.played_date, new_off = decode_str(data, off)
        off += new_off

        self.played_type = decode_short(data, off)
        off += SHORT_OFF

        self.played_amount = decode_short(data, off)
        off += SHORT_OFF

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

class SaoGetAuthCardDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.auth_type = AuthType(decode_byte(data, off)) # 0 is unknown, 1 is card (banapass, aime, AICC), 2 is moble
        off += BYTE_OFF

        store_id = decode_str(data, off)
        self.store_id = store_id[0]
        off += store_id[1]

        serial_no = decode_str(data, off)
        self.serial_no = serial_no[0]
        off += serial_no[1]

        access_code = decode_str(data, off)
        self.access_code = access_code[0]
        off += access_code[1]

        chip_id = decode_str(data, off)
        self.chip_id = chip_id[0]
        off += chip_id[1]

class SaoGetAuthCardDataResponse(SaoBaseResponse):
    def __init__(self, nicknname: str, user_id: int) -> None:
        super().__init__(GameconnectCmd.GET_AUTH_CARD_DATA_RESPONSE)
        self.result = 1
        self.unused_card_flag = ""
        self.first_play_flag = 0
        self.tutorial_complete_flag = 1
        self.nick_name = nicknname
        self.personal_id = str(user_id)
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.unused_card_flag) \
        + encode_byte(self.first_play_flag) \
        + encode_byte(self.tutorial_complete_flag) \
        + encode_str(self.nick_name) \
        + encode_str(self.personal_id)

class SaoGetAccessCodeByKeitaiRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.auth_type = AuthType(decode_byte(data, off))  # 0 is unknown, 1 is card (banapass, aime, AICC), 2 is moble
        off += BYTE_OFF

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.chip_id, new_off = decode_str(data, off)
        off += new_off

class SaoGetAccessCodeByKeitaiResponse(SaoBaseResponse):
    def __init__(self, access_code: str) -> None:
        super().__init__(GameconnectCmd.GET_ACCESS_CODE_BY_KEITAI_RESPONSE)
        self.result = 1
        self.access_code = access_code
        self.ba_id_flag = 1
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.access_code) \
        + encode_byte(self.ba_id_flag)

class SaoCheckAcLoginBonusResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.CHECK_AC_LOGIN_BONUS_RESPONSE)
        self.result = 1
        self.reward_get_flag = 1

        self.get_ac_login_bonus_id_list: List[int] = [] # "2020年7月9日～（アニメ＆リコリス記念）"
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_byte(self.reward_get_flag) \
        + encode_arr_num(self.get_ac_login_bonus_id_list, INT_OFF) \

class SaoGetQuestSceneMultiPlayPhotonServerResponse(SaoBaseResponse):
    def __init__(self, app_id: str = "7df3a2f6-d69d-4073-aafe-810ee61e1cea") -> None:
        super().__init__(GameconnectCmd.GET_QUEST_SCENE_MULTI_PLAY_PHOTON_SERVER_RESPONSE)
        self.result = 1
        self.application_id = app_id
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.application_id)

class SaoLoginRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.auth_type = AuthType(decode_byte(data, off))  # 0 is unknown, 1 is card (banapass, aime, AICC), 2 is moble
        off += BYTE_OFF

        store_id = decode_str(data, off)
        self.store_id = store_id[0]
        off += store_id[1]

        store_name = decode_str(data, off)
        self.store_name = store_name[0]
        off += store_name[1]

        serial_no = decode_str(data, off)
        self.serial_no = serial_no[0]
        off += serial_no[1]

        access_code = decode_str(data, off)
        self.access_code = access_code[0]
        off += access_code[1]

        chip_id = decode_str(data, off)
        self.chip_id = chip_id[0]
        off += chip_id[1]

        self.free_ticket_distribution_target_flag = decode_byte(data, off)
        off += BYTE_OFF

class SaoLoginResponse(SaoBaseResponse):
    def __init__(self, user_id: int, first_play: bool = False, logged_in_today: bool = True) -> None:
        super().__init__(GameconnectCmd.LOGIN_RESPONSE)
        self.result = 1
        self.user_id = str(user_id)
        self.first_play_flag = first_play
        self.grantable_free_ticket_flag = not logged_in_today
        self.login_reward_vp = 0 if logged_in_today else 100
        self.today_paying_flag = logged_in_today
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.user_id) \
        + encode_byte(self.first_play_flag) \
        + encode_byte(self.grantable_free_ticket_flag) \
        + encode_short(self.login_reward_vp) \
        + encode_byte(self.today_paying_flag)

class SaoLogoutRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off) # 0 satalite, 1 terminal
        off += BYTE_OFF

        self.remaining_ticket_num = decode_short(data, off)
        off += SHORT_OFF

class SaoPurchaseTicketRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.discount_type = decode_byte(data, off)
        off += BYTE_OFF
        self.purchase_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoConsumeTicketRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.discount_type = decode_byte(data, off)
        off += BYTE_OFF
        self.act_type = ActTypeConsumeTicket(decode_byte(data, off))
        off += BYTE_OFF
        self.consume_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoAddCreditRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.add_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoConsumeCreditRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.act_type = ActTypeConsumeCredit(decode_byte(data, off))
        off += BYTE_OFF
        self.consume_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoPurchaseTicketGuestRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.discount_type = decode_byte(data, off)
        off += BYTE_OFF
        self.purchase_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoConsumeTicketGuestRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.discount_type = decode_byte(data, off)
        off += BYTE_OFF
        self.act_type = ActTypeConsumeTicket(decode_byte(data, off))
        off += BYTE_OFF
        self.consume_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoAddCreditGuestRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.add_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoConsumeCreditGuestRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF
        self.act_type = ActTypeConsumeCredit(decode_byte(data, off))
        off += BYTE_OFF
        self.consume_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoCheckComebackEventResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.CHECK_COMEBACK_EVENT_RESPONSE)
        self.result = 1
        self.get_flag = 1
        self.get_comeback_event_id_list: List[int] = [] # Array of events apparently
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_byte(self.get_flag) \
        + encode_arr_num(self.get_comeback_event_id_list, INT_OFF)

class SaoChangeMyStoreRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

class SaoCheckTitleGetDecisionRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_offset = decode_str(data, off)
        off += new_offset

        self.user_id, new_offset = decode_str(data, off)
        off += new_offset

class SaoCheckTitleGetDecisionResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.CHECK_TITLE_GET_DECISION_RESPONSE)
        self.result = 1
        self.get_title_id_list: List[int] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_num(self.get_title_id_list, INT_OFF)

class SaoGetUserBasicDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoGetUserBasicDataResponse(SaoBaseResponse):
    def __init__(self, profile_data) -> None:
        super().__init__(GameconnectCmd.GET_USER_BASIC_DATA_RESPONSE)
        self.result = 1
        self.user_basic_data: List[UserBasicData] = [UserBasicData.from_args(profile_data)]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.user_basic_data)

class SaoGetVpGashaTicketDataListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoGetVpGashaTicketDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_VP_GASHA_TICKET_DATA_LIST_RESPONSE)
        self.result = 1
        self.vp_gasha_ticket_data_list: List[VpGashaTicketData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.vp_gasha_ticket_data_list)

class SaoChangeTitleRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_title_id, new_off = decode_str(data, off)
        off += new_off

class SaoGetPresentBoxNumResponse(SaoBaseResponse):
    def __init__(self, num_box: int = 0, max_num: int = 0) -> None:
        super().__init__(GameconnectCmd.GET_PRESENT_BOX_NUM_RESPONSE)
        self.result = 1
        self.num = num_box
        self.max_num = max_num
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_short(self.num) \
        + encode_short(self.max_num)

class SaoGetHeroLogUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_HERO_LOG_USER_DATA_LIST_RESPONSE)
        self.result = 1
        
        self.hero_log_user_data_list: List[HeroLogUserData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.hero_log_user_data_list)

class SaoGetEquipmentUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_EQUIPMENT_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.equipment_user_data_list: List[EquipmentUserData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.equipment_user_data_list)

class SaoGetItemUserDataListResponse(SaoBaseResponse):
    def __init__(self, item_data: List[Dict] = []) -> None:
        super().__init__(GameconnectCmd.GET_ITEM_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.item_user_data_list: List[ItemUserData] = []

        if item_data:
            for item in item_data:
                self.item_user_data_list.append(ItemUserData.from_args(item))
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.item_user_data_list)

class SaoGetSupportLogUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_SUPPORT_LOG_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.support_log_user_data_list: List[SupportLogUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.support_log_user_data_list)

class SaoGetTitleUserDataListResponse(SaoBaseResponse):
    def __init__(self, user_id: str, titles: List[int]) -> None:
        super().__init__(GameconnectCmd.GET_TITLE_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.title_user_data_list: List[TitleUserData] = []

        if titles:
            for x in titles:
                self.title_user_data_list.append(TitleUserData.from_args(user_id + str(x), x))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.title_user_data_list)

class SaoGetEpisodeAppendDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_EPISODE_APPEND_DATA_LIST_RESPONSE)
        self.result = 1
        self.episode_append_data_list: List[EpisodeAppendUserData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.episode_append_data_list)

class SaoGetEventItemDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_EVENT_ITEM_DATA_LIST_RESPONSE)
        self.result = 1
        self.event_item_data_list: List[EventItemUserData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.event_item_data_list)

class SaoGetGashaMedalUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_GASHA_MEDAL_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalUserData] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetPartyDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_PARTY_DATA_LIST_RESPONSE)
        self.result = 1
        self.party_data_list: List[PartyData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.party_data_list)

class SaoGetSupportLogPartyDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_SUPPORT_LOG_PARTY_DATA_LIST_RESPONSE)
        self.result = 1
        self.support_log_party_data_list: List[SupportLogPartyData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.support_log_party_data_list)

class SaoGetQuestScenePrevScanProfileCardResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_QUEST_SCENE_PREV_SCAN_PROFILE_CARD_RESPONSE)
        self.result = 1
        self.profile_card_data: List[ReadProfileCardData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.profile_card_data)

class SaoGetResourcePathInfoResponse(SaoBaseResponse):
    def __init__(self, base_url: str) -> None:
        super().__init__(GameconnectCmd.GET_RESOURCE_PATH_INFO_RESPONSE)
        self.result = 1
        self.resource_base_url = base_url
        self.gasha_base_dir = "gasha"
        self.ad_base_dir = "ad"
        self.event_base_dir = "event"
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.resource_base_url) \
        + encode_str(self.gasha_base_dir) \
        + encode_str(self.ad_base_dir) \
        + encode_str(self.event_base_dir)

class SaoValidationErrorNotificationRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.send_protocol_name, new_off = decode_str(data, off)
        off += new_off

        self.send_data_to_fraud_value, new_off = decode_str(data, off)
        off += new_off

        self.send_data_to_modification_value, new_off = decode_str(data, off)
        off += new_off

class SaoGetBeginnerMissionUserDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

class SaoGetBeginnerMissionUserDataResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_BEGINNER_MISSION_USER_DATA_RESPONSE)
        self.result = 1
        self.data: List[BeginnerMissionUserData] = [BeginnerMissionUserData.from_args(datetime.now())]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data)

class SaoMatchingErrorNotificationRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.matching_error_data_list: List[MatchingErrorData]
        self.matching_error_data_list, new_off = decode_arr_cls(data, off, MatchingErrorData)

class SaoPowerCuttingReturnNotification(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

        self.net_id, new_off = decode_str(data, off)
        off += new_off

        self.place_id, new_off = decode_str(data, off)
        off += new_off

        self.store_id, new_off = decode_str(data, off)
        off += new_off

        self.store_name, new_off = decode_str(data, off)
        off += new_off

        self.serial_no, new_off = decode_str(data, off)
        off += new_off

        self.last_act_type = decode_byte(data, off)
        off += BYTE_OFF

        self.remaining_ticket_num = decode_short(data, off)
        off += SHORT_OFF

        self.remaining_credit_num = decode_short(data, off)
        off += SHORT_OFF

class SaoEpisodePlayStartRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.episode_id = decode_int(data, off)
        off += INT_OFF

        self.play_mode = decode_byte(data, off)
        off += BYTE_OFF

        self.play_start_request_data: List[QuestScenePlayStartRequestData] = []
        self.play_start_request_data, new_off = decode_arr_cls(data, off, QuestScenePlayStartRequestData)
        off += new_off

        self.multi_play_start_request_data: List[QuestSceneMultiPlayStartRequestData] = []
        self.multi_play_start_request_data, new_off = decode_arr_cls(data, off, QuestSceneMultiPlayStartRequestData)
        off += new_off

class SaoEpisodePlayStartResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.EPISODE_PLAY_START_RESPONSE)
        self.result = 1
        self.play_start_response_data: List[QuestScenePlayStartResponseData] = []
        self.multi_play_start_response_data: List[QuestSceneMultiPlayStartResponseData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_start_response_data) \
        + encode_arr_cls(self.multi_play_start_response_data)

class SaoEpisodePlayEndRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.episode_id = decode_int(data, off)
        off += INT_OFF

        self.play_end_request_data: List[QuestScenePlayEndRequestData] = []
        self.play_end_request_data, new_off = decode_arr_cls(data, off, QuestScenePlayEndRequestData)
        off += new_off

        self.multi_play_end_request_data: List[QuestSceneMultiPlayEndRequestData] = []
        self.multi_play_end_request_data, new_off = decode_arr_cls(data, off, QuestSceneMultiPlayEndRequestData)
        off += new_off

class SaoEpisodePlayEndResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.EPISODE_PLAY_END_RESPONSE)
        self.result = 1
        self.play_end_response_data: List[QuestScenePlayEndResponseData] = [QuestScenePlayEndResponseData.from_args()]
        self.multi_play_end_response_data: List[QuestSceneMultiPlayEndResponseData] = [QuestSceneMultiPlayEndResponseData.from_args()]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_end_response_data) \
        + encode_arr_cls(self.multi_play_end_response_data)

class SaoTrialTowerPlayStartRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        ticket_id = decode_str(data, off)
        self.ticket_id = ticket_id[0]
        off += ticket_id[1]

        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

        self.trial_tower_id = decode_int(data, off)
        off += INT_OFF

        self.play_mode = decode_byte(data, off)
        off += BYTE_OFF

        self.play_start_request_data_count = decode_int(data, off)
        off += INT_OFF

        self.play_start_request_data: List[PlayStartRequestData] = []
        for _ in range(self.play_start_request_data_count):
            tmp = PlayStartRequestData(data, off)
            self.play_start_request_data.append(tmp)
            off += tmp.get_size()
        
        self.multi_play_start_request_data_count = decode_int(data, off)
        off += INT_OFF
        
        self.multi_play_start_request_data: List[MultiPlayStartRequestData] = []
        for _ in range(self.multi_play_start_request_data_count):
            tmp = MultiPlayStartRequestData(data, off)
            off += tmp.get_size()
            self.multi_play_start_request_data.append(tmp)

class SaoTrialTowerPlayStartResponse(SaoBaseResponse):
    def __init__(self, sesh_id: int, nickname: str) -> None:
        super().__init__(GameconnectCmd.TRIAL_TOWER_PLAY_START_RESPONSE)
        self.result = 1
        self.play_start_response_data: List[QuestScenePlayStartResponseData] = [QuestScenePlayStartResponseData.from_args(sesh_id, nickname)]
        self.multi_play_start_response_data: List[QuestSceneMultiPlayStartResponseData] = [QuestSceneMultiPlayStartResponseData.from_args()]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_start_response_data) \
        + encode_arr_cls(self.multi_play_start_response_data)

class SaoTrialTowerPlayEndRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.trial_tower_id = decode_int(data, off)
        off += INT_OFF

        self.play_end_request_data: List[QuestScenePlayEndRequestData] = []
        self.play_end_request_data, new_off = decode_arr_cls(data, off, QuestScenePlayEndRequestData)
        off += new_off

        self.multi_play_end_request_data: List[QuestSceneMultiPlayEndRequestData]
        self.multi_play_end_request_data, new_off = decode_arr_cls(data, off, QuestSceneMultiPlayEndRequestData)
        off += new_off

class SaoTrialTowerPlayEndResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.TRIAL_TOWER_PLAY_END_RESPONSE)
        self.result = 1
        self.play_end_response_data: List[QuestScenePlayEndResponseData] = [QuestScenePlayEndResponseData.from_args()]
        self.multi_play_end_response_data: List[QuestSceneMultiPlayEndResponseData] = [QuestSceneMultiPlayEndResponseData.from_args()]
        self.trial_tower_play_end_updated_notification_data: List[QuestTrialTowerPlayEndUpdatedNotificationData] = [QuestTrialTowerPlayEndUpdatedNotificationData.from_args()]
        self.treasure_hunt_play_end_response_data: List[QuestTreasureHuntPlayEndResponseData] = [QuestTreasureHuntPlayEndResponseData.from_args()]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_end_response_data) \
        + encode_arr_cls(self.multi_play_end_response_data) \
        + encode_arr_cls(self.trial_tower_play_end_updated_notification_data) \
        + encode_arr_cls(self.treasure_hunt_play_end_response_data)

class SaoEpisodePlayEndUnanalyzedLogFixedRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        ticket_id = decode_str(data, off)
        self.ticket_id = ticket_id[0]
        off += ticket_id[1]

        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

        self.episode_id = decode_int(data, off)
        off += INT_OFF

        self.rarity_up_exec_flag = decode_byte(data, off)
        off += BYTE_OFF

class SaoEpisodePlayEndUnanalyzedLogFixedResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.EPISODE_PLAY_END_UNANALYZED_LOG_FIXED_RESPONSE)
        self.result = 1
        self.play_end_unanalyzed_log_reward_data_list: List[QuestScenePlayEndUnanalyzedLogRewardData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_end_unanalyzed_log_reward_data_list)

class SaoGetQuestSceneUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_QUEST_SCENE_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.quest_scene_user_data_list: List[QuestSceneUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.quest_scene_user_data_list)

class SaoCheckYuiMedalGetConditionRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoCheckYuiMedalGetConditionResponse(SaoBaseResponse):
    def __init__(self, elapsed_days: int = 0, get_num: int = 0) -> None:
        super().__init__(GameconnectCmd.CHECK_YUI_MEDAL_GET_CONDITION_RESPONSE)
        self.result = 1
        self.get_flag = int(get_num > 0)
        self.elapsed_days = elapsed_days
        self.get_yui_medal_num = get_num
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_byte(self.get_flag) \
        + encode_short(self.elapsed_days) \
        + encode_short(self.get_yui_medal_num) \

class SaoGetYuiMedalBonusUserDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.yui_medal_bonus_id = decode_int(data, off)
        off += INT_OFF

class SaoGetYuiMedalBonusUserDataResponse(SaoBaseResponse):
    def __init__(self, elapsed_days: int = 0, loop_num: int = 0) -> None:
        super().__init__(GameconnectCmd.GET_YUI_MEDAL_BONUS_USER_DATA_RESPONSE)
        self.result = 1
        self.data: List[YuiMedalBonusUserData] = [YuiMedalBonusUserData.from_args(elapsed_days, loop_num)]
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data)

class SaoCheckProfileCardUsedRewardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        self.user_id, new_off = decode_str(data, off)
        off += new_off

class SaoCheckProfileCardUsedRewardResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.CHECK_PROFILE_CARD_USED_REWARD_RESPONSE)
        self.result = 1
        self.get_flag = 0
        self.used_num = 0
        self.get_vp = 0
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_byte(self.get_flag) \
        + encode_int(self.used_num) \
        + encode_int(self.get_vp)

class SaoDisposalResourceRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.disposal_common_reward_user_data_list: List[CommonRewardUserData] = []
        self.disposal_common_reward_user_data_list, new_off = decode_arr_cls(data, off, CommonRewardUserData)
        off += new_off

class SaoDisposalResourceResponse(SaoBaseResponse):
    def __init__(self, get_col: int = 0) -> None:
        super().__init__(GameconnectCmd.DISPOSAL_RESOURCE_RESPONSE)
        self.result = 1
        self.get_col = get_col

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_int(self.get_col)

class SaoSynthesizeEnhancementHeroLogRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.origin_user_hero_log_id, new_off = decode_str(data, off)
        off += new_off

        self.material_common_reward_user_data_list: List[CommonRewardUserData] = []
        self.material_common_reward_user_data_list, new_off = decode_arr_cls(data, off, CommonRewardUserData)
        off += new_off

class SaoSynthesizeEnhancementHeroLogResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.SYNTHESIZE_ENHANCEMENT_HERO_LOG_RESPONSE)
        self.result = 1
        self.after_hero_log_user_data: List[HeroLogUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.after_hero_log_user_data)

class SaoSynthesizeEnhancementEquipmentRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.origin_user_equipment_id, new_off = decode_str(data, off)
        off += new_off

        self.material_common_reward_user_data_list: List[CommonRewardUserData] = []
        self.material_common_reward_user_data_list, new_off = decode_arr_cls(data, off, CommonRewardUserData)
        off += new_off

class SaoSynthesizeEnhancementEquipmentResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.SYNTHESIZE_ENHANCEMENT_EQUIPMENT_RESPONSE)
        self.result = 1
        self.after_equipment_user_data: List[EquipmentUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.after_equipment_user_data)

class SaoGetAdventureExecUserDataResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_ADVENTURE_EXEC_USER_DATA_RESPONSE)
        self.result = 1
        self.adventure_exec_user_data: List[AdventureExecUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.adventure_exec_user_data)

class SaoGetChatSideStoryUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_CHAT_SIDE_STORY_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.chat_side_story_user_data_list: List[ChatSideStoryUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.chat_side_story_user_data_list)

class SaoBeginnerMissionAdConfirmNotificationRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

class SaoGetDefragMatchBasicDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

class SaoGetDefragMatchBasicDataResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_DEFRAG_MATCH_BASIC_DATA_RESPONSE)
        self.result = 1
        self.defrag_match_basic_user_data: List[DefragMatchBasicUserData] = []
    
    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.defrag_match_basic_user_data)
        return super().make() + ret

class SaoGetDefragMatchRankingUserDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

class SaoGetDefragMatchRankingUserDataResponse(SaoBaseResponse):
    def __init__(self, profile: Dict) -> None:
        super().__init__(GameconnectCmd.GET_DEFRAG_MATCH_RANKING_USER_DATA_RESPONSE)
        self.result = 1
        self.ranking_user_data: List[DefragMatchRankingUserData] = [DefragMatchRankingUserData.from_args(profile)]

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.ranking_user_data)

class SaoGetDefragMatchLeaguePointRankingListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.get_rank_start_num = decode_short(data, off)
        off += SHORT_OFF

        self.get_rank_end_num = decode_short(data, off)
        off += SHORT_OFF

class SaoGetDefragMatchLeaguePointRankingListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_DEFRAG_MATCH_LEAGUE_POINT_RANKING_LIST_RESPONSE)
        self.result = 1
        self.ranking_data_list: List[DefragMatchLeaguePointRankingData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.ranking_data_list)

class SaoGetDefragMatchLeagueScoreRankingListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id = decode_int(data, off)
        off += INT_OFF

        self.get_rank_start_num = decode_short(data, off)
        off += SHORT_OFF

        self.get_rank_end_num = decode_short(data, off)
        off += SHORT_OFF

class SaoGetDefragMatchLeagueScoreRankingListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_DEFRAG_MATCH_LEAGUE_SCORE_RANKING_LIST_RESPONSE)
        self.result = 1
        self.ranking_user_data: List[DefragMatchLeagueScoreRankingList] = []
    
    def make(self) -> bytes:
        # create a resp struct
        resp_data = encode_byte(self.result)
        resp_data += encode_arr_cls(self.ranking_user_data)
        return super().make() + resp_data

class SaoGetBeginnerMissionProgressesUserDataListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

class SaoGetBeginnerMissionProgressesUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_BEGINNER_MISSION_PROGRESSES_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionProgressesUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetBeginnerMissionSeatProgressesUserDataListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

class SaoGetBeginnerMissionSeatProgressesUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_BEGINNER_MISSION_SEAT_PROGRESSES_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionSeatProgressesUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetLinkedSiteRegCampaignUserDataRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.linked_site_reg_campaign_id = decode_int(data, off)
        off += INT_OFF

class SaoGetLinkedSiteRegCampaignUserDataResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_LINKED_SITE_REG_CAMPAIGN_USER_DATA_RESPONSE)
        self.result = 1
        self.data: List[LinkedSiteRegCampaignUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data)

class SaoGetHeroLogUnitUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_HERO_LOG_UNIT_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.hero_log_unit_user_data_list: List[HeroLogUnitUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.hero_log_unit_user_data_list)

class SaoGetCharaUnitUserDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_CHARA_UNIT_USER_DATA_LIST_RESPONSE)
        self.result = 1
        self.chara_unit_user_data_list: List[CharaUnitUserData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.chara_unit_user_data_list)

class SaoBeginnerMissionAdConfirmNotificationRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.beginner_mission_id = decode_int(data, off)
        off += INT_OFF

class SaoBnidSerialCodeCheckRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.bnid_serial_code, new_off = decode_str(data, off)
        off += new_off

class SaoBnidSerialCodeCheckResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.BNID_SERIAL_CODE_CHECK_RESPONSE)
        self.result = 1
        self.bnid_item_id = ""
        self.use_status = 0

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.bnid_item_id) \
        + encode_byte(self.use_status)

class SaoBnidSerialCodeEntryByAppendixCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.bnid_serial_code, new_off = decode_str(data, off)
        off += new_off

class SaoBnidSerialCodeEntryByAppendixCardResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.BNID_SERIAL_CODE_ENTRY_BY_APPENDIX_CARD_RESPONSE)
        self.result = 1
        self.get_bnid_item_id = ""

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.get_bnid_item_id)

class SaoDischargeProfileCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.hero_log_user_hero_log_id, new_off = decode_str(data, off)
        off += new_off

        self.main_weapon_user_equipment_id, new_off = decode_str(data, off)
        off += new_off

        self.sub_equipment_user_equipment_id, new_off = decode_str(data, off)
        off += new_off

        self.skill_id = decode_int(data, off)
        off += INT_OFF
        self.text_chara_message_id = decode_int(data, off)
        off += INT_OFF

        self.holographic_flag = decode_byte(data, off)
        off += BYTE_OFF
        self.execute_print_type = PrintType(decode_byte(data, off))
        off += BYTE_OFF

class SaoDischargeProfileCardResponse(SaoBaseResponse):
    def __init__(self, serial: str) -> None:
        super().__init__(GameconnectCmd.DISCHARGE_PROFILE_CARD_RESPONSE)
        self.result = 1
        self.profile_card_code = serial

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.profile_card_code)

class SaoDischargeResourceCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.holographic_flag = decode_byte(data, off)
        off += BYTE_OFF

        self.execute_print_type = PrintType(decode_byte(data, off))
        off += BYTE_OFF

        self.common_reward_user_data: List[MaterialCommonRewardUserData] = [] # typing lol
        self.common_reward_user_data, new_off = decode_arr_cls(data, off, MaterialCommonRewardUserData)
        off += new_off

class SaoDischargeResourceCardResponse(SaoBaseResponse):
    def __init__(self, serial: str) -> None:
        super().__init__(GameconnectCmd.DISCHARGE_RESOURCE_CARD_RESPONSE)
        self.result = 1
        self.profile_card_code = serial

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_str(self.profile_card_code)

class SaoDischargeResourceCardCompleteRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off

        self.user_id, new_off = decode_str(data, off)
        off += new_off

        self.resource_card_code, new_off = decode_str(data, off)
        off += new_off

class SaoScanQrQuestProfileCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.profile_card_code, new_off = decode_str(data, off)
        off += new_off

class SaoScanQrQuestProfileCardResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.SCAN_QR_QUEST_PROFILE_CARD_RESPONSE)
        self.result = 1
        self.profile_card_data: List[ReadProfileCard] = []
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.profile_card_data)

class SaoScanQrShopResourceCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.resource_card_code, new_off = decode_str(data, off)
        off += new_off

class SaoScanQrQuestResourceCardRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.resource_card_code, new_off = decode_str(data, off)
        off += new_off

class SaoScanQrQuestResourceCardResponse(SaoBaseResponse):
    def __init__(self, reward_type: int = 0, reward_id: int = 0, is_holo: bool = False) -> None:
        super().__init__(GameconnectCmd.SCAN_QR_QUEST_RESOURCE_CARD_RESPONSE)
        self.result = 1
        self.common_reward_type = reward_type
        self.common_reward_id = reward_id
        self.holographic_flag = is_holo
    
    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_short(self.common_reward_type) \
        + encode_int(self.common_reward_id) \
        + encode_bool(self.holographic_flag)

class SaoConsumeCreditGuestRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        shop_id = decode_str(data, off)
        self.shop_id = shop_id[0]
        off += shop_id[1]
        
        serial_num = decode_str(data, off)
        self.serial_num = serial_num[0]
        off += serial_num[1]
        
        self.cab_type = decode_byte(data, off)
        off += BYTE_OFF
        
        self.act_type = ActTypeConsumeCredit(decode_byte(data, off))
        off += BYTE_OFF
        
        self.consume_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoChangePartyRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        ticket_id = decode_str(data, off)
        self.ticket_id = ticket_id[0]
        off += ticket_id[1]

        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

        self.act_type = ActTypeChangeParty(decode_byte(data, off))
        off += BYTE_OFF

        self.party_data_list: List[PartyData] = []
        self.party_data_list, new_off = decode_arr_cls(data, off, PartyData)
        off += new_off

class SaoTrialTowerPlayEndUnanalyzedLogFixedRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        ticket_id = decode_str(data, off)
        self.ticket_id = ticket_id[0]
        off += ticket_id[1]

        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

        self.trial_tower_id = decode_int(data, off)
        off += INT_OFF

        self.rarity_up_exec_flag = decode_byte(data, off)
        off += BYTE_OFF

class SaoTrialTowerPlayEndUnanalyzedLogFixedResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.TRIAL_TOWER_PLAY_END_UNANALYZED_LOG_FIXED_RESPONSE)
        self.result = 1
        self.play_end_unanalyzed_log_reward_data_list: List[QuestScenePlayEndUnanalyzedLogRewardData] = []

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.play_end_unanalyzed_log_reward_data_list)

class SaoGetShopResourceSalesDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_SHOP_RESOURCE_SALES_DATA_LIST_RESPONSE)
        self.result = 1 # byte
        self.shop_resource_sales_data: List[ShopResourceSalesData] = []

    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.shop_resource_sales_data)
        
        self.header.length = len(ret)
        return super().make() + ret

class SaoPurchaseShopResourceRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_shop_resource_id, new_off = decode_str(data, off)
        off += new_off

class GetYuiMedalShopUserDataListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

class GetYuiMedalShopUserDataListResponse(SaoBaseResponse):
    def __init__(self, cmd_id: int) -> None:
        super().__init__(cmd_id)
        self.result = 1 # byte
        self.user_data_list: List[YuiMedalShopUserData] = []

    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.user_data_list)
        
        self.header.length = len(ret)
        return super().make() + ret

class GetGashaMedalShopUserDataListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        user_id = decode_str(data, off)
        self.user_id = user_id[0]
        off += user_id[1]

class GetGashaMedalShopUserDataListResponse(SaoBaseResponse):
    def __init__(self, cmd_id: int) -> None:
        super().__init__(cmd_id)
        self.result = 1 # byte
        self.data_list: List[GashaMedalShopUserData] = []

    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.data_list)
        
        self.header.length = len(ret)
        return super().make() + ret

class SaoGiveFreeTicketRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.give_num = decode_byte(data, off)
        off += BYTE_OFF

class SaoLogoutTicketUnpurchasedRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        
        self.cabinet_type = decode_byte(data, off)
        off += BYTE_OFF

class SaoGetQuestHierarchyProgressDegreesRankingListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off
        
        self.get_rank_start_num = decode_short(data, off)
        off += SHORT_OFF
        
        self.get_rank_end_num = decode_short(data, off)
        off += SHORT_OFF

class SaoGetQuestHierarchyProgressDegreesRankingListResponse(SaoBaseResponse):
    def __init__(self, cmd_id: int) -> None:
        super().__init__(cmd_id)
        self.result = 1 # byte
        self.quest_hierarchy_progress_degrees_ranking_data_list: List[QuestHierarchyProgressDegreesRankingData] = []
    
    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.quest_hierarchy_progress_degrees_ranking_data_list)
        return super().make() + ret

class SaoGetQuestPopularHeroLogRankingListRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.store_id, new_off = decode_str(data, off)
        off += new_off
        
        self.get_rank_start_num = decode_short(data, off)
        off += SHORT_OFF
        
        self.get_rank_end_num = decode_short(data, off)
        off += SHORT_OFF

class SaoGetQuestPopularHeroLogRankingListResponse(SaoBaseResponse):
    def __init__(self, cmd_id: int) -> None:
        super().__init__(cmd_id)
        self.result = 1 # byte
        self.quest_popular_hero_log_ranking_data_list: List[PopularHeroLogRankingData] = []
    
    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_cls(self.quest_popular_hero_log_ranking_data_list)
        return super().make() + ret

class SaoGetVariousTutorialDataListResponse(SaoBaseResponse):
    def __init__(self) -> None:
        super().__init__(GameconnectCmd.GET_VARIOUS_TUTORIAL_DATA_LIST_RESPONSE)
        self.result = 1
        self.end_tutorial_type_list: List[int] = []
    
    def make(self) -> bytes:
        ret = encode_byte(self.result)
        ret += encode_arr_num(self.end_tutorial_type_list, BYTE_OFF)
        return super().make() + ret

class SaoVariousTutorialEndRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ticket_id, new_off = decode_str(data, off)
        off += new_off
        self.user_id, new_off = decode_str(data, off)
        off += new_off
        self.tutorial_type = decode_byte(data, off)
        off += BYTE_OFF

class SaoGetMExTowersRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ex_tower_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMExTowerQuestsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.ex_tower_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMChatEventStoriesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.event_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntWholeTasksRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntIndividualTasksRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntSpecialEffectsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntEventPointRewardCommonRewardsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMTreasureHuntEventPointRewardTitlesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.treasure_hunt_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchSeedRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchSpecialEffectsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchGradesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchPeriodBonusesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchRandomBonusTablesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMDefragMatchRareDropsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.defrag_match_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMEventScenesRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.event_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMBeginnerMissionConditionsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.beginner_mission_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMBeginnerMissionRewardsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.beginner_mission_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMBeginnerMissionSeatConditionsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.beginner_mission_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMBeginnerMissionSeatRewardsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.beginner_mission_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMEventMonstersRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.event_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMGashaMedalSettingsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.gasha_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMGashaMedalShopItemsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.gasha_medal_shop_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMResEarnCampaignApplicationProductsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.res_earn_campaign_application_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMResEarnCampaignShopItemsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.res_earn_campaign_shop_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMPlayCampaignRewardsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.play_campaign_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMLinkedSiteRegCampaignRewardsRequest(SaoBaseRequest):
    def __init__(self, header: SaoRequestHeader, data: bytes) -> None:
        super().__init__(header, data)
        off = 0
        self.linked_site_reg_campaign_id_list, new_off = decode_arr_num(data, off, INT_OFF)
        off += new_off

class SaoGetMPlayerRanksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PLAYER_RANKS_RESPONSE)
        self.result = 1
        self.data_list: List[PlayerRankData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PlayerRankData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTitlesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TITLES_RESPONSE)
        self.result = 1
        self.data_list: List[TitleData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TitleData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMFragmentsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_FRAGMENTS_RESPONSE)
        self.result = 1
        self.data_list: List[FragmentData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(FragmentData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMRewardTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_REWARD_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[RewardTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(RewardTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMRewardSetsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_REWARD_SETS_RESPONSE)
        self.result = 1
        self.data_list: List[RewardSetData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(RewardSetData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMUnanalyzedLogGradesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_UNANALYZED_LOG_GRADES_RESPONSE)
        self.result = 1
        self.data_list: List[UnanalyzedLogGradeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(UnanalyzedLogGradeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAppointLeaderParamsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_APPOINT_LEADER_PARAMS_RESPONSE)
        self.result = 1
        self.data_list: List[AppointLeaderParamData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AppointLeaderParamData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAppointLeaderEffectsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_APPOINT_LEADER_EFFECTS_RESPONSE)
        self.result = 1
        self.data_list: List[AppointLeaderEffectData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AppointLeaderEffectData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAppointLeaderEffectTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_APPOINT_LEADER_EFFECT_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[AppointLeaderEffectTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AppointLeaderEffectTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMRaritiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_RARITIES_RESPONSE)
        self.result = 1
        self.data_list: List[RarityData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(RarityData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCompositionEventsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_COMPOSITION_EVENTS_RESPONSE)
        self.result = 1
        self.data_list: List[CompositionEventData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CompositionEventData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCompositionParamsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_COMPOSITION_PARAMS_RESPONSE)
        self.result = 1
        self.data_list: List[CompositionParamData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CompositionParamData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGamePlayPricesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GAME_PLAY_PRICES_RESPONSE)
        self.result = 1
        self.data_list: List[GamePlayPriceData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GamePlayPriceData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBuyTicketsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BUY_TICKETS_RESPONSE)
        self.result = 1
        self.data_list: List[BuyTicketData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BuyTicketData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTipsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TIPS_RESPONSE)
        self.result = 1
        self.data_list: List[TipsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TipsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCapsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CAPS_RESPONSE)
        self.result = 1
        self.data_list: List[CapData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CapData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMHeroLogResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_HERO_LOG_RESPONSE)
        self.result = 1
        self.data_list: List[HeroLogData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(HeroLogData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMHeroLogLevelsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_HERO_LOG_LEVELS_RESPONSE)
        self.result = 1
        self.data_list: List[HeroLogLevelData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(HeroLogLevelData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMHeroLogRolesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_HERO_LOG_ROLES_RESPONSE)
        self.result = 1
        self.data_list: List[HeroLogRoleData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(HeroLogRoleData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMHeroLogTrustRanksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_HERO_LOG_TRUST_RANKS_RESPONSE)
        self.result = 1
        self.data_list: List[HeroLogTrustRankData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(HeroLogTrustRankData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCharasResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHARAS_RESPONSE)
        self.result = 1
        self.data_list: List[CharaData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CharaData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCharaFriendlyRanksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHARA_FRIENDLY_RANKS_RESPONSE)
        self.result = 1
        self.data_list: List[CharaFriendlyRankData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CharaFriendlyRankData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEquipmentsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EQUIPMENTS_RESPONSE)
        self.result = 1
        self.data_list: List[EquipmentData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EquipmentData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEquipmentLevelsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EQUIPMENT_LEVELS_RESPONSE)
        self.result = 1
        self.data_list: List[EquipmentLevelData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EquipmentLevelData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMWeaponTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_WEAPON_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[WeaponTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(WeaponTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[ItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMItemTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ITEM_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[ItemTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ItemTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBuffItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BUFF_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[BuffItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BuffItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEnemiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ENEMIES_RESPONSE)
        self.result = 1
        self.data_list: List[EnemyData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EnemyData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEnemySetsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ENEMY_SETS_RESPONSE)
        self.result = 1
        self.data_list: List[EnemySetData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EnemySetData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEnemyKindsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ENEMY_KINDS_RESPONSE)
        self.result = 1
        self.data_list: List[EnemyKindData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EnemyKindData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEnemyCategoriesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_ENEMY_CATEGORIES_RESPONSE)
        self.result = 1
        self.data_list: List[EnemyCategoryData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EnemyCategoryData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMUnitsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_UNITS_RESPONSE)
        self.result = 1
        self.data_list: List[UnitData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(UnitData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMUnitGimmicksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_UNIT_GIMMICKS_RESPONSE)
        self.result = 1
        self.data_list: List[UnitGimmickData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(UnitGimmickData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMUnitCollisionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_UNIT_COLLISIONS_RESPONSE)
        self.result = 1
        self.data_list: List[UnitCollisionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(UnitCollisionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMUnitPowersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_UNIT_POWERS_RESPONSE)
        self.result = 1
        self.data_list: List[UnitPowerData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(UnitPowerData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGimmickAttacksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GIMMICK_ATTACKS_RESPONSE)
        self.result = 1
        self.data_list: List[GimmickAttackData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GimmickAttackData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMCharaAttacksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHARA_ATTACKS_RESPONSE)
        self.result = 1
        self.data_list: List[CharaAttackData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(CharaAttackData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBossAttacksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BOSS_ATTACKS_RESPONSE)
        self.result = 1
        self.data_list: List[BossAttackData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BossAttackData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMonsterAttacksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MONSTER_ATTACKS_RESPONSE)
        self.result = 1
        self.data_list: List[MonsterAttackData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MonsterAttackData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMonsterActionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MONSTER_ACTIONS_RESPONSE)
        self.result = 1
        self.data_list: List[MonsterActionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MonsterActionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPropertiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PROPERTIES_RESPONSE)
        self.result = 1
        self.data_list: List[PropertyData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PropertyData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPropertyTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PROPERTY_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[PropertyTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PropertyTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPropertyTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PROPERTY_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[PropertyTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PropertyTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSkillsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SKILLS_RESPONSE)
        self.result = 1
        self.data_list: List[SkillData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SkillData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSkillTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SKILL_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[SkillTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SkillTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSkillLevelsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SKILL_LEVELS_RESPONSE)
        self.result = 1
        self.data_list: List[SkillLevelData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SkillLevelData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAwakeningsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_AWAKENINGS_RESPONSE)
        self.result = 1
        self.data_list: List[AwakeningData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AwakeningData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSynchroSkillsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SYNCHRO_SKILLS_RESPONSE)
        self.result = 1
        self.data_list: List[SynchroSkillData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SynchroSkillData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSoundSkillCutInVoicesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SOUND_SKILL_CUT_IN_VOICES_RESPONSE)
        self.result = 1
        self.data_list: List[SoundSkillCutInVoiceData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SoundSkillCutInVoiceData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestScenesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_SCENES_RESPONSE)
        self.result = 1
        self.data_list: List[QuestSceneData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestSceneData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestExistUnitsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_EXIST_UNITS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestExistUnitData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestExistUnitData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestEpisodeAppendRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_EPISODE_APPEND_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestEpisodeAppendRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestEpisodeAppendRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSideQuestsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SIDE_QUESTS_RESPONSE)
        self.result = 1
        self.data_list: List[SideQuestData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SideQuestData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEpisodesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EPISODES_RESPONSE)
        self.result = 1
        self.data_list: List[EpisodeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EpisodeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEpisodeChaptersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EPISODE_CHAPTERS_RESPONSE)
        self.result = 1
        self.data_list: List[EpisodeChapterData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EpisodeChapterData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEpisodePartsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EPISODE_PARTS_RESPONSE)
        self.result = 1
        self.data_list: List[EpisodePartData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EpisodePartData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTrialTowersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TRIAL_TOWERS_RESPONSE)
        self.result = 1
        self.data_list: List[TrialTowerData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TrialTowerData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMExTowersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EX_TOWERS_RESPONSE)
        self.result = 1
        self.data_list: List[ExTowerData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ExTowerData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMExTowerQuestsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EX_TOWER_QUESTS_RESPONSE)
        self.result = 1
        self.data_list: List[ExTowerQuestData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ExTowerQuestData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMenuDisplayEnemiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MENU_DISPLAY_ENEMIES_RESPONSE)
        self.result = 1
        self.data_list: List[MenuDisplayEnemyData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MenuDisplayEnemyData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMissionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MISSIONS_RESPONSE)
        self.result = 1
        self.data_list: List[MissionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MissionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMissionTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MISSION_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[MissionTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MissionTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMMissionDifficultiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_MISSION_DIFFICULTIES_RESPONSE)
        self.result = 1
        self.data_list: List[MissionDifficultyData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(MissionDifficultyData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBattleCamerasResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BATTLE_CAMERAS_RESPONSE)
        self.result = 1
        self.data_list: List[BattleCameraData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BattleCameraData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMChatMainStoriesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHAT_MAIN_STORIES_RESPONSE)
        self.result = 1
        self.data_list: List[ChatMainStoryData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ChatMainStoryData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMChatSideStoriesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHAT_SIDE_STORIES_RESPONSE)
        self.result = 1
        self.data_list: List[ChatSideStoryData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ChatSideStoryData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMChatEventStoriesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_CHAT_EVENT_STORIES_RESPONSE)
        self.result = 1
        self.data_list: List[ChatEventStoryData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ChatEventStoryData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMNavigatorCharasResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_NAVIGATOR_CHARAS_RESPONSE)
        self.result = 1
        self.data_list: List[NavigatorCharaData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(NavigatorCharaData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMNavigatorCommentsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_NAVIGATOR_COMMENTS_RESPONSE)
        self.result = 1
        self.data_list: List[NavigatorCommentData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(NavigatorCommentData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMExBonusTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EX_BONUS_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[ExBonusTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ExBonusTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMExBonusConditionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EX_BONUS_CONDITIONS_RESPONSE)
        self.result = 1
        self.data_list: List[ExBonusConditionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ExBonusConditionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestRareDropsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_RARE_DROPS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestRareDropData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestRareDropData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestSpecialRareDropSettingsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_SPECIAL_RARE_DROP_SETTINGS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestSpecialRareDropSettingData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestSpecialRareDropSettingData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestSpecialRareDropsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_SPECIAL_RARE_DROPS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestSpecialRareDropData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestSpecialRareDropData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestTutorialsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_TUTORIALS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestTutorialData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestTutorialData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestPlayerTraceTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_PLAYER_TRACE_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[QuestPlayerTraceTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestPlayerTraceTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestStillsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_STILLS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestStillData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestStillData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashasResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHAS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaHeadersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_HEADERS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaHeaderData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaHeaderData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaLotteryRaritiesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_LOTTERY_RARITIES_RESPONSE)
        self.result = 1
        self.data_list: List[GashaLotteryRarityData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaLotteryRarityData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaPrizesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_PRIZES_RESPONSE)
        self.result = 1
        self.data_list: List[GashaPrizeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaPrizeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMComebackEventsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_COMEBACK_EVENTS_RESPONSE)
        self.result = 1
        self.data_list: List[ComebackEventData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ComebackEventData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAdBannersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_AD_BANNERS_RESPONSE)
        self.result = 1
        self.data_list: List[AdBannerData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AdBannerData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEventsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EVENTS_RESPONSE)
        self.result = 1
        self.data_list: List[EventsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EventsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNTS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntWholeTasksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_WHOLE_TASKS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntWholeTasksData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntWholeTasksData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntIndividualTasksResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_INDIVIDUAL_TASKS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntIndividualTasksData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntIndividualTasksData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntSpecialEffectsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_SPECIAL_EFFECTS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntSpecialEffectsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntSpecialEffectsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntEventPointRewardCommonRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_EVENT_POINT_REWARD_COMMON_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntEventPointRewardCommonRewardsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntEventPointRewardCommonRewardsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntEventPointRewardTitlesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_EVENT_POINT_REWARD_TITLES_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntEventPointRewardTitlesData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntEventPointRewardTitlesData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMTreasureHuntTaskTextsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_TREASURE_HUNT_TASK_TEXTS_RESPONSE)
        self.result = 1
        self.data_list: List[TreasureHuntTaskTextData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(TreasureHuntTaskTextData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBnidSerialCodesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BNID_SERIAL_CODES_RESPONSE)
        self.result = 1
        self.data_list: List[BnidSerialCodeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BnidSerialCodeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBnidSerialCodeRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BNID_SERIAL_CODE_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[BnidSerialCodeRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BnidSerialCodeRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSupportLogResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SUPPORT_LOG_RESPONSE)
        self.result = 1
        self.data_list: List[SupportLogData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SupportLogData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMSupportLogTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_SUPPORT_LOG_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[SupportLogTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(SupportLogTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEpisodeAppendsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EPISODE_APPENDS_RESPONSE)
        self.result = 1
        self.data_list: List[EpisodeAppendData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EpisodeAppendData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestDefragMatchQuestsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_DEFRAG_MATCH_QUESTS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestDefragMatchQuestData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestDefragMatchQuestData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestDefragMatchQuestBossTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_DEFRAG_MATCH_QUEST_BOSS_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[QuestDefragMatchQuestBossTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestDefragMatchQuestBossTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCHES_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchSeedResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_SEED_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchSeedData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchSeedData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchSpecialEffectsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_SPECIAL_EFFECTS_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchSpecialEffectData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchSpecialEffectData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchGradesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_GRADES_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchGradeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchGradeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchCpuUnitsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_CPU_UNITS_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchCpuUnitData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchCpuUnitData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchCpuSupportLogsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_CPU_SUPPORT_LOGS_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchCpuSupportLogData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchCpuSupportLogData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchPeriodBonusesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_PERIOD_BONUSES_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchPeriodBonusData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchPeriodBonusData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchRandomBonusTablesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_RANDOM_BONUS_TABLES_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchRandomBonusTableData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchRandomBonusTableData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchRandomBonusConditionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_RANDOM_BONUS_CONDITIONS_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchRandomBonusConditionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchRandomBonusConditionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMDefragMatchRareDropsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_DEFRAG_MATCH_RARE_DROPS_RESPONSE)
        self.result = 1
        self.data_list: List[DefragMatchRareDropData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(DefragMatchRareDropData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMYuiMedalShopsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_YUI_MEDAL_SHOPS_RESPONSE)
        self.result = 1
        self.data_list: List[YuiMedalShopData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(YuiMedalShopData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMYuiMedalShopItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_YUI_MEDAL_SHOP_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[YuiMedalShopItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(YuiMedalShopItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEventScenesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EVENT_SCENES_RESPONSE)
        self.result = 1
        self.data_list: List[EventSceneData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EventSceneData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGenericCampaignPeriodsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GENERIC_CAMPAIGN_PERIODS_RESPONSE)
        self.result = 1
        self.data_list: List[GenericCampaignPeriodData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GenericCampaignPeriodData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBeginnerMissionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BEGINNER_MISSIONS_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BeginnerMissionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBeginnerMissionConditionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BEGINNER_MISSION_CONDITIONS_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionConditionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BeginnerMissionConditionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBeginnerMissionRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BEGINNER_MISSION_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BeginnerMissionRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBeginnerMissionSeatConditionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BEGINNER_MISSION_SEAT_CONDITIONS_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionSeatConditionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BeginnerMissionSeatConditionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMBeginnerMissionSeatRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_BEGINNER_MISSION_SEAT_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[BeginnerMissionSeatRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(BeginnerMissionSeatRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEventItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EVENT_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[EventItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EventItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMEventMonstersResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_EVENT_MONSTERS_RESPONSE)
        self.result = 1
        self.data_list: List[EventMonsterData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(EventMonsterData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMYuiMedalBonusesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_YUI_MEDAL_BONUSES_RESPONSE)
        self.result = 1
        self.data_list: List[YuiMedalBonusData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(YuiMedalBonusData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMYuiMedalBonusConditionsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_YUI_MEDAL_BONUS_CONDITIONS_RESPONSE)
        self.result = 1
        self.data_list: List[YuiMedalBonusConditionData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(YuiMedalBonusConditionData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDALS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalTypesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDAL_TYPES_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalTypeData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalTypeData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalSettingsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDAL_SETTINGS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalSettingData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalSettingData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalBonusesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDAL_BONUSES_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalBonusData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalBonusData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalShopsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDAL_SHOPS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalShopData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalShopData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaMedalShopItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_MEDAL_SHOP_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaMedalShopItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaMedalShopItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMResEarnCampaignApplicationsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_RES_EARN_CAMPAIGN_APPLICATIONS_RESPONSE)
        self.result = 1
        self.data_list: List[ResEarnCampaignApplicationData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ResEarnCampaignApplicationData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMResEarnCampaignApplicationProductsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_RES_EARN_CAMPAIGN_APPLICATION_PRODUCTS_RESPONSE)
        self.result = 1
        self.data_list: List[ResEarnCampaignApplicationProductData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ResEarnCampaignApplicationProductData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMResEarnCampaignShopsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_RES_EARN_CAMPAIGN_SHOPS_RESPONSE)
        self.result = 1
        self.data_list: List[ResEarnCampaignShopData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ResEarnCampaignShopData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMResEarnCampaignShopItemsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_RES_EARN_CAMPAIGN_SHOP_ITEMS_RESPONSE)
        self.result = 1
        self.data_list: List[ResEarnCampaignShopItemData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(ResEarnCampaignShopItemData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPayingYuiMedalBonusesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PAYING_YUI_MEDAL_BONUSES_RESPONSE)
        self.result = 1
        self.data_list: List[PayingYuiMedalBonusData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PayingYuiMedalBonusData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMAcLoginBonusesResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_AC_LOGIN_BONUSES_RESPONSE)
        self.result = 1
        self.data_list: List[AcLoginBonusData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(AcLoginBonusData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPlayCampaignsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PLAY_CAMPAIGNS_RESPONSE)
        self.result = 1
        self.data_list: List[PlayCampaignData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PlayCampaignData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMPlayCampaignRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_PLAY_CAMPAIGN_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[PlayCampaignRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(PlayCampaignRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMGashaFreeCampaignsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_GASHA_FREE_CAMPAIGNS_RESPONSE)
        self.result = 1
        self.data_list: List[GashaFreeCampaignData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(GashaFreeCampaignData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMQuestDropBoostCampaignsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_QUEST_DROP_BOOST_CAMPAIGNS_RESPONSE)
        self.result = 1
        self.data_list: List[QuestDropBoostCampaignData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(QuestDropBoostCampaignData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMFirstTicketPurchaseCampaignsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_FIRST_TICKET_PURCHASE_CAMPAIGNS_RESPONSE)
        self.result = 1
        self.data_list: List[FirstTicketPurchaseCampaignData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(FirstTicketPurchaseCampaignData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMLinkedSiteRegCampaignsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_LINKED_SITE_REG_CAMPAIGNS_RESPONSE)
        self.result = 1
        self.data_list: List[LinkedSiteRegCampaignsData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(LinkedSiteRegCampaignsData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

class SaoGetMLinkedSiteRegCampaignRewardsResponse(SaoBaseResponse):
    def __init__(self, data_list: List[Dict]) -> None:
        super().__init__(GameconnectCmd.GET_M_LINKED_SITE_REG_CAMPAIGN_REWARDS_RESPONSE)
        self.result = 1
        self.data_list: List[LinkedSiteRegCampaignRewardData] = []

        if data_list:
            for item in data_list:
                self.data_list.append(LinkedSiteRegCampaignRewardData.from_args(item))

    def make(self) -> bytes:
        return super().make() \
        + encode_byte(self.result) \
        + encode_arr_cls(self.data_list)

