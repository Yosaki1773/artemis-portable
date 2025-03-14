import logging
from csv import *
from random import choice, randint
from typing import Dict, List
from os import path
import re
from sqlalchemy.engine import Row

from core import CoreConfig
from .config import SaoConfig
from .database import SaoData
from .const import GameconnectCmd, RewardType, ExBonusCondition, QuestType
from titles.sao.handlers.base import *
import csv

class SaoBase:
    DATA_LIST = {}
    def __init__(self, core_cfg: CoreConfig, game_cfg: SaoConfig) -> None:
        self.core_cfg = core_cfg
        self.game_cfg = game_cfg
        self.data = SaoData(core_cfg)
        self.logger = logging.getLogger("sao")

    def load_data_csv(self, file: str, version: int = 1, base_ver: int = 1) -> List[Dict]:
        if base_ver > version:
            self.logger.warning(f"load_data_csv: Cannot use base version higher then requested version ({base_ver} > {version})")
            return []
        
        for x in range(version, base_ver - 1, -1):
            ret = self.DATA_LIST.get(x, {}).get(file, [])
            if ret:
                break
        
        if not ret and base_ver != 1:
            ret = self.DATA_LIST.get(1, {}).get(file, [])
        
        if ret:
            return ret
        
        found = False
        for x in range(version, base_ver - 1, -1):
            fname = f"./titles/sao/data/{x}/{file}.csv"
            if path.exists(fname):
                found_ver = x
                found = True
                break
        
        if not found and base_ver != 1: # v1 will always be fallback if it isn't already
            fname = f"./titles/sao/data/1/{file}.csv"
            if path.exists(fname):
                found_ver = 1
                found = True
        
        if not found:
            self.logger.warning(f"load_data_csv: Failed to find v{version} csv file {fname}")
            return []
        
        ret = []
        with open(fname, "r", encoding="utf8") as f:
            data = csv.DictReader(f, delimiter=',')
            for x in data:
                newdict = {}
                for k, v in x.items():
                    newkey = k
                    if k.startswith("// "):
                        newkey = k.replace("// ", "")
                    
                    if v.isdigit():
                        newdict[newkey] = int(v)
                    elif v.lower() == "true":
                        newdict[newkey] = True
                    elif v.lower() == "false":
                        newdict[newkey] = False
                    elif re.match(r"^\d\d\d\d\/\d\d\/\d\d \d{1,2}:\d\d:\d\d$", v):
                        newdict[newkey] = datetime.strptime(v, "%Y/%m/%d %H:%M:%S")
                    elif re.match(r"^\d\d\d\d\/\d\d\/\d\d$", v):
                        newdict[newkey] = datetime.strptime(v, "%Y/%m/%d")
                    else:
                        newdict[newkey] = v
                ret.append(newdict)
        
        # Cache the CSV data in memory
        if found_ver not in self.DATA_LIST:
            self.DATA_LIST[found_ver] = {}
        self.DATA_LIST[found_ver][file] = ret
        
        return ret

    async def add_reward(self, reward: Dict, user_id: int):
        reward_type = int(reward.get("CommonRewardType", "0"))
        if reward_type == RewardType.HeroLog:
            reward_hero_data = await self.data.static.get_hero_by_id(reward['CommonRewardId'])
            now_have_skills = await self.hero_default_skills(reward_hero_data['SkillTableSubId'])
                        
            new_hero_id = await self.data.item.put_hero_log(
                user_id, 
                reward['CommonRewardId'], 
                1, 
                0, 
                None, 
                None, 
                now_have_skills[0],
                now_have_skills[1], 
                now_have_skills[2],
                now_have_skills[3],
                now_have_skills[4],
            )
            self.logger.info(f"Rewarded user {user_id} with hero {reward['CommonRewardId']} (ID {new_hero_id})")
            # TODO: add properties
        
        elif reward_type == RewardType.Equipment:
            new_equip_id = await self.data.item.put_equipment(user_id, reward['CommonRewardId'])
            self.logger.info(f"Rewarded user {user_id} with equipment {reward['CommonRewardId']} (ID {new_equip_id})")
        
        elif reward_type == RewardType.Item:
            new_item_id = await self.data.item.put_item(user_id, reward['CommonRewardId'])
            self.logger.info(f"Rewarded user {user_id} with item {reward['CommonRewardId']} (ID {new_item_id})")
        
        elif reward_type == RewardType.Col:
            col_num = int(reward['CommonRewardNum'])
            self.logger.info(f"Rewarded user {user_id} with {col_num} Col")
            await self.data.profile.add_col(user_id, col_num)

        elif reward_type == RewardType.VP:
            vp_num = int(reward['CommonRewardNum'])
            self.logger.info(f"Rewarded user {user_id} with {vp_num} VP")
            await self.data.profile.add_vp(user_id, vp_num)

        elif reward_type == RewardType.YuiMadal:
            medal_num = int(reward['CommonRewardNum'])
            self.logger.info(f"Rewarded user {user_id} with {medal_num} Yui Medals")
            await self.data.profile.add_yui_medals(user_id, medal_num)
        
        else:
            self.logger.warning(f"User {user_id} Unhandled reward type {reward_type} -> {reward}")

    async def hero_default_skills(self, skill_table_id: int) -> List[int]:
        skills = await self.data.static.get_skill_table_by_subid(skill_table_id)
        if not skills:
            self.logger.error(f"Failed to find skill table {skill_table_id}! Please run the reader")
            return [None, None, None, None, None]

        default_skills = []
        now_have_skills = [None, None, None, None, None]
        for skill in skills:
            if skill['LevelObtained'] == 1 and skill['AwakeningId'] == 0:
                default_skills.append(skill['SkillId'])
        
        for skill in default_skills:
            skill_info = await self.data.static.get_skill_by_id(skill)
            skill_slot = skill_info['Level'] - 1
            if now_have_skills[skill_slot] is not None:
                now_have_skills[skill]
        
        return now_have_skills

    async def handle_noop(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        return SaoNoopResponse(header.cmd + 1).make()

    async def handle_c000(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #ticket/ticket
        req = SaoTicketRequest(header, request)
        return SaoTicketResponse().make()

    async def handle_c100(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/get_app_versions
        resp = SaoGetAppVersionsResponse()
        resp.data_list.append(AppVersionData.from_args(self.game_cfg.server.game_version, datetime.fromtimestamp(0)))
        return resp.make()

    async def handle_c102(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/master_data_version_check
        req = SaoMasterDataVersionCheckRequest(header, request)
        self.logger.info(f"Cab at {src_ip} checked in with master data v{req.current_data_version}")
        return SaoMasterDataVersionCheckResponse(self.game_cfg.server.data_version, req.current_data_version).make()

    async def handle_c104(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/login
        req = SaoLoginRequest(header, request)

        user_id = await self.data.card.get_user_id_from_card( req.access_code )
        if not user_id:
            card = await self.data.card.get_card_by_idm(req.chip_id[:16])
            if card:
                user_id = card['user']
                card_id = card['id']
                await self.data.card.set_access_code_by_access_code(card['access_code'], req.access_code)
            
            else:
                user_id = await self.data.user.create_user() #works
                card_id = await self.data.card.create_card(user_id, req.access_code)

            if card_id is None:
                user_id = -1
                self.logger.error("Failed to register card!")
            
            self.logger.info(f"Registered card {req.access_code} to user {user_id} from {req.serial_no}")
            
            if req.access_code.startswith("5"):
                await self.data.card.set_idm_by_access_code(req.access_code, req.chip_id[:16])
            elif (req.access_code.startswith("010") or req.access_code.startswith("3")) and int(req.chip_id[:8], 16) != 0x04030201:
                await self.data.card.set_chip_id_by_access_code(req.access_code, int(req.chip_id[:8], 16))
        
        profile_data = await self.data.profile.get_profile(user_id)

        if not profile_data:
            profile_id = await self.data.profile.create_profile(user_id)
            if profile_id:
                equip1 = await self.data.item.put_equipment(user_id, 101000000)
                equip2 = await self.data.item.put_equipment(user_id, 102000000)
                equip3 = await self.data.item.put_equipment(user_id, 109000000)
                if not equip1 or not equip2 or not equip3:
                    self.logger.error(f"Failed to create profile for user {user_id} from {req.serial_no} (could not add equipment)")
                    return SaoNoopResponse(GameconnectCmd.LOGIN_RESPONSE).make()
                
                hero1 = await self.data.item.put_hero_log(user_id, 101000010, 1, 0, equip1, None, 1002, 1003, 1014, None, None)
                hero2 = await self.data.item.put_hero_log(user_id, 102000010, 1, 0, equip2, None, 3001, 3002, 3004, None, None)
                hero3 = await self.data.item.put_hero_log(user_id, 105000010, 1, 0, equip3, None, 10005, 10002, 10004, None, None)
                if not hero1 or not hero2 or not hero3:
                    self.logger.error(f"Failed to create profile for user {user_id} from {req.serial_no} (could not add heros)")
                    return SaoNoopResponse(GameconnectCmd.LOGIN_RESPONSE).make()
                
                await self.data.item.put_hero_party(user_id, 0, hero1, hero2, hero3)
                self.logger.info(f"Create profile {profile_id} for user {user_id} from {req.serial_no}")
            else:
                self.logger.error(f"Failed to create profile for user {user_id} from {req.serial_no}")
                return SaoNoopResponse(GameconnectCmd.LOGIN_RESPONSE).make()
            resp = SaoLoginResponse(user_id, True, False)
        
        else:
            is_login_today = False
            
            if profile_data['last_login_date']:
                last_login_time = int(profile_data["last_login_date"].timestamp())
                midnight_today_ts = int(
                    datetime.now()
                    .replace(hour=0, minute=0, second=0, microsecond=0)
                    .timestamp()
                )

                if last_login_time > midnight_today_ts:
                    is_login_today = True
                
            if not is_login_today:
                await self.data.profile.add_vp(user_id, 100)
            
            resp = SaoLoginResponse(user_id, profile_data['login_ct'] < 1, is_login_today)
        
        await self.data.profile.user_login(user_id)
        return resp.make()
    
    async def handle_c106(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/logout
        req = SaoLogoutRequest(header, request)
        self.logger.info(f"User {req.user_id} Logout from {'game' if req.cabinet_type == 0 else 'terminal'} @ {src_ip} with {req.remaining_ticket_num} tickets remaining")
        return SaoNoopResponse(GameconnectCmd.LOGOUT_RESPONSE).make()

    async def handle_c108(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/logout_ticket_unpurchased
        req = SaoLogoutTicketUnpurchasedRequest(header, request)
        self.logger.info(f"User {req.user_id} Logout from {'game' if req.cabinet_type == 0 else 'terminal'} @ {src_ip} without buying a ticket")
        return SaoNoopResponse(GameconnectCmd.LOGOUT_TICKET_UNPURCHASED_RESPONSE).make()

    async def handle_c10a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/paying_play_start
        req = SaoPayingPlayStartRequest(header, request)
        self.logger.info(f"User {req.paying_user_id} started paying session @ {req.store_name} ({src_ip}) on cab {req.serial_no}")
        resp = SaoPayingPlayStartResponse()
        # TODO: session management
        return resp.make()
    
    async def handle_c10c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/paying_play_end
        req = SaoPayingPlayEndRequest(header, request)
        self.logger.info(f"User {req.paying_user_id} ended paying session {req.paying_session_id} @ {req.store_name} ({src_ip}) on cab {req.serial_no} after {req.played_amount} {req.played_type} type games")
        return SaoNoopResponse(GameconnectCmd.PAYING_PLAY_END_RESPONSE).make()
    
    async def handle_c10e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/purchase_ticket
        req = SaoPurchaseTicketRequest(header, request)
        self.logger.info(f"User {req.user_id} pruchased {req.purchase_num} tickets (ID {req.ticket_id}) @ {src_ip} with discout type {req.discount_type}")
        return SaoNoopResponse(GameconnectCmd.PURCHASE_TICKET_RESPONSE).make()

    async def handle_c110(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/consume_ticket
        req = SaoConsumeTicketRequest(header, request)
        self.logger.info(f"User {req.user_id} consumed {req.consume_num} tickets (ID {req.ticket_id}) @ {src_ip} with discout type {req.discount_type} on {req.act_type}")
        return SaoNoopResponse(GameconnectCmd.CONSUME_TICKET_RESPONSE).make()

    async def handle_c112(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/add_credit
        req = SaoAddCreditRequest(header, request)
        self.logger.info(f"User {req.user_id} added {req.add_num} credits to a {'game' if req.cabinet_type == 0 else 'terminal'} @ {src_ip}")
        return SaoNoopResponse(GameconnectCmd.ADD_CREDIT_RESPONSE).make()

    async def handle_c114(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/consume_credit
        req = SaoConsumeCreditRequest(header, request)
        self.logger.info(f"User {req.user_id} consumed {req.consume_num} credits on a {'game' if req.cabinet_type == 0 else 'terminal'} @ {req.store_id} ({src_ip}) on {req.act_type}")
        return SaoNoopResponse(GameconnectCmd.CONSUME_CREDIT_RESPONSE).make()

    async def handle_c116(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/purchase_ticket_guest
        req = SaoPurchaseTicketGuestRequest(header, request)
        self.logger.info(f"Guest purchased {req.purchase_num} tickets on a {'game' if req.cabinet_type == 0 else 'terminal'} @ {req.store_id} ({src_ip} | SN {req.serial_no})")
        return SaoNoopResponse(GameconnectCmd.PURCHASE_TICKET_GUEST_RESPONSE).make()

    async def handle_c118(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/consume_ticket_guest
        req = SaoConsumeTicketGuestRequest(header, request)
        self.logger.info(f"Guest consumed {req.consume_num} tickets @ {req.store_id} ({src_ip} | SN {req.serial_no}) with discout type {req.discount_type} on {req.act_type}")
        return SaoNoopResponse(GameconnectCmd.CONSUME_TICKET_GUEST_RESPONSE).make()

    async def handle_c11a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/add_credit_guest
        req = SaoAddCreditGuestRequest(header, request)
        self.logger.info(f"Guest added {req.add_num} credits to a {'game' if req.cabinet_type == 0 else 'terminal'} @ {req.store_id} ({src_ip} | SN {req.serial_no})")
        return SaoNoopResponse(GameconnectCmd.ADD_CREDIT_GUEST_RESPONSE).make()

    async def handle_c11c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/consume_credit_guest
        req = SaoConsumeCreditGuestRequest(header, request)
        self.logger.info(f"Guest consumed {req.consume_num} credits on a {'game' if req.cab_type == 0 else 'terminal'} @ {req.shop_id} ({src_ip} | SN {req.serial_num}) on {req.act_type}")
        return SaoNoopResponse(GameconnectCmd.CONSUME_CREDIT_GUEST_RESPONSE).make()

    async def handle_c11e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/get_auth_card_data
        req = SaoGetAuthCardDataRequest(header, request)

        #Check authentication
        card = await self.data.card.get_card_by_access_code( req.access_code )

        if not card:
            card = await self.data.card.get_card_by_idm(req.chip_id[:16])
            if not card:
                self.logger.info(f"Unregistered card {req.access_code} authenticated from {req.serial_no}")
                return SaoGetAuthCardDataResponse("NEW PLAYER", 0).make()
            
            await self.data.card.set_access_code_by_access_code(card['access_code'], req.access_code)
            
        else:            
            user_id = card['user']
            card_id = card['id']
            
            if req.access_code.startswith("5") and not card['idm']:
                await self.data.card.set_idm_by_access_code(card_id, req.chip_id[:16])
            elif (req.access_code.startswith("010") or req.access_code.startswith("3")) and not card['chip_id'] and int(req.chip_id[:8], 16) != 0x04030201:
                await self.data.card.set_chip_id_by_access_code(card_id, int(req.chip_id[:8], 16))
        
            self.logger.info(f"User Authenticated from {req.serial_no}: { req.access_code } | { user_id }")

        #Grab values from profile
        profile_data = await self.data.profile.get_profile(user_id)

        if not profile_data:
            self.logger.info(f"Unregistered user {user_id} with card {req.access_code} authenticated from {req.serial_no}")
            return SaoGetAuthCardDataResponse("NEW PLAYER", user_id).make()

        return SaoGetAuthCardDataResponse(profile_data['nick_name'], user_id).make()

    async def handle_c120(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/get_access_code_by_keitai
        req = SaoGetAccessCodeByKeitaiRequest(header, request)
        cid = req.chip_id
        idm = cid[:16]
        pmm = cid[16:]
        card = await self.data.card.get_card_by_idm(idm)
        
        # If we don't have that card saved locally, check aimedb
        if not card:
            # Validate that we're talking to a phone
            if not int(pmm[2:4], 16) in self.data.card.moble_os_codes:
                self.logger.warning(f"{req.serial_no} looked up non-moble chip ID {cid}!")
                return SaoGetAccessCodeByKeitaiResponse("").make()
            
            # TODO: Actual felica moble registration
            return SaoGetAccessCodeByKeitaiResponse("").make()
            #ac = await self.data.card.register_felica_moble_ac(idm, pmm)
            # if we didn't get an access code, fail hard
            if not ac:
                self.logger.warning(f"Failed to register access code for chip ID {cid} requested by {req.serial_no}")
                return SaoGetAccessCodeByKeitaiResponse("").make()
            
            self.logger.info(f"Successfully registered moble felica access code {ac} for chip ID {cid} requested by {req.serial_no}")
                
            uid = await self.data.user.create_user()
            if not uid:
                self.logger.error(f"Failed to create user for chip ID {cid} (access code {ac}) @ LoadAccessCode request from {req.serial_no}")
                return SaoGetAccessCodeByKeitaiResponse("").make()
            
            cardid = await self.data.card.create_card(uid, ac)
            if not cardid:
                self.logger.error(f"Failed to create card for user {uid} with chip ID {cid} (access code {ac}) @ LoadAccessCode request from {req.serial_no}")
                await self.data.user.delete_user(uid)
                return SaoGetAccessCodeByKeitaiResponse("").make()
            
            self.logger.info(f"Moble Felica access code lookup for {cid} -> {ac} (user {uid}) requested by {req.serial_no}")
        
        else:            
            ac = card['access_code']
            uid = card['user']
            self.logger.info(f"Moble Felica access code for {cid} -> {ac} (user {uid}) requested by {req.serial_no}")
        
        return SaoGetAccessCodeByKeitaiResponse(ac).make()

    async def handle_c122(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/get_maintenance_info
        resp = SaoGetMaintenanceInfoResponse()
        return resp.make()

    async def handle_c124(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/get_resource_path_info
        resp = SaoGetResourcePathInfoResponse(f"https://{self.core_cfg.server.hostname}/saoresource/")
        return resp.make()

    async def handle_c126(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/validation_error_notification
        req = SaoValidationErrorNotificationRequest(header, request)
        self.logger.warning(f"User {req.user_id} on {'game' if req.cabinet_type == 0 else 'terminal'} {req.serial_no} @ {req.store_name} ({src_ip} | Place ID {req.place_id}) " \
            + f"Validation error: {req.send_protocol_name} || {req.send_data_to_fraud_value} || {req.send_data_to_modification_value}")
        return SaoNoopResponse(GameconnectCmd.VALIDATION_ERROR_NOTIFICATION_RESPONSE).make()

    async def handle_c128(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/power_cutting_return_notification
        req = SaoPowerCuttingReturnNotification(header, request)
        self.logger.warning(f"User {req.user_id} on {'game' if req.cabinet_type == 0 else 'terminal'} {req.serial_no} @ {req.store_name} ({src_ip} | Place ID {req.place_id}) " \
            + f"Power outage return: Act Type {req.last_act_type} || {req.remaining_ticket_num} Remaining Tickets || {req.remaining_credit_num} Remaining Credits")
        return SaoNoopResponse(GameconnectCmd.POWER_CUTTING_RETURN_NOTIFICATION_RESPONSE).make()

    async def handle_c12a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/give_free_ticket
        req = SaoGiveFreeTicketRequest(header, request)
        self.logger.info(f"Give {req.give_num} free tickets (id {req.ticket_id}) to user {req.user_id}")
        resp = SaoNoopResponse(GameconnectCmd.GIVE_FREE_TICKET_RESPONSE)
        return resp.make()

    async def handle_c12c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # common/matching_error_notification
        req = SaoMatchingErrorNotificationRequest(header, request)
        self.logger.warning(f"{'game' if req.cabinet_type == 0 else 'terminal'} {req.serial_no} @ {req.store_name} ({src_ip} | Place ID {req.place_id}) " \
            + f"Matching error: {req.matching_error_data_list[0]}")
        return SaoNoopResponse(GameconnectCmd.MATCHING_ERROR_NOTIFICATION_RESPONSE).make()

    async def handle_c12e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #common/ac_cabinet_boot_notification
        req = SaoCommonAcCabinetBootNotificationRequest(header, request)
        
        if req.current_version_app_id < self.game_cfg.server.game_version:
            self.logger.info(f"!!OUTDATED!! {'Game' if req.cabinet_type == 0 else 'Terminal'} {req.serial_no} Booted v{req.current_version_app_id} (Master data v{req.current_master_data_version}): {req.store_name} ({src_ip} | Place/Shop ID {req.place_id}/{req.store_id})")
        
        if req.current_version_app_id > self.game_cfg.server.game_version:
            self.logger.info(f"!!TOO NEW!! {'Game' if req.cabinet_type == 0 else 'Terminal'} {req.serial_no} Booted v{req.current_version_app_id} (Master data v{req.current_master_data_version}): {req.store_name} ({src_ip} | Place/Shop ID {req.place_id}/{req.store_id})")
        
        self.logger.info(f"{'Game' if req.cabinet_type == 0 else 'Terminal'} {req.serial_no} Booted v{req.current_version_app_id} (Master data v{req.current_master_data_version}): {req.store_name} ({src_ip} | Place/Shop ID {req.place_id}/{req.store_id})")
        resp = SaoNoopResponse(GameconnectCmd.AC_CABINET_BOOT_NOTIFICATION_RESPONSE)
        return resp.make()

    async def handle_c200(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # tutorial/first_tutorial_end
        req = SaoGenericUserTicketRequest(header, request)
        self.logger.info(f"User {req.user_id} (ticket {req.ticket_id}) finished first tutorial")
        return SaoNoopResponse(GameconnectCmd.FIRST_TUTORIAL_END_RESPONSE).make()

    async def handle_c202(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # tutorial/various_tutorial_end
        req = SaoVariousTutorialEndRequest(header, request)
        await self.data.profile.add_tutorial_byte(int(req.user_id), req.tutorial_type)
        return SaoNoopResponse(GameconnectCmd.VARIOUS_TUTORIAL_END_RESPONSE).make()

    async def handle_c204(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # tutorial/get_various_tutorial_data_list
        req = SaoGenericUserRequest(header, request)
        tuts = await self.data.profile.get_tutorial_bytes(int(req.user_id))
        resp = SaoGetVariousTutorialDataListResponse()
        if tuts:
            for t in tuts:
                resp.end_tutorial_type_list.append(t['tutorial_byte'])
        
        return resp.make()

    async def handle_c300(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # card/discharge_profile_card
        req = SaoDischargeProfileCardRequest(header, request)
        # Real cards seem to start with 10-17 as the first 2 digits, so we'll anchor ours with 2 to ensure no overlap
        sn = f"2{str(randint(1, 999999999999999999)).zfill(18)}"
        while await self.data.profile.get_hero_card(sn):
            sn = f"2{str(randint(1, 999999999999999999)).zfill(18)}"
        resp = SaoDischargeProfileCardResponse(sn)
        
        db_hero = await self.data.item.get_hero_log(req.user_id, req.hero_log_user_hero_log_id)
        if not db_hero:
            hero_statc = await self.data.static.get_hero_by_id(db_hero['hero_log_id'])
            if not hero_statc:
                self.logger.error(f"Failed to find hero log {db_hero['hero_log_id']}! Please run the reader")
                resp.header.error_type = ProtocolErrorNum.RESOURCE_CARD_ERR1
                return resp.make()
            
            now_have_skills = await self.hero_default_skills(hero_statc['SkillTableSubId'])

            db_hero_id = await self.data.item.put_hero_log(
                req.user_id,
                db_hero['hero_log_id'],
                1,
                0,
                None,
                None, 
                now_have_skills[0],
                now_have_skills[1],
                now_have_skills[2],
                now_have_skills[3],
                now_have_skills[4]
            )
            if not db_hero_id:
                self.logger.error(f"Failed to give user {req.user_id} hero {db_hero['hero_log_id']}!")
                resp.header.error_type = ProtocolErrorNum.RESOURCE_CARD_ERR6
                return resp.make()
        
        else:
            db_hero_id = db_hero['id']
        
        await self.data.profile.put_hero_card(req.user_id, sn, db_hero_id, req.holographic_flag)
        
        self.logger.info(f"User {req.user_id} printed {'holo ' if req.holographic_flag == 1 else ''}profile card {req.hero_log_user_hero_log_id} {req.execute_print_type}, code {sn}")
        return resp.make()

    async def handle_c302(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # card/discharge_resource_card
        req = SaoDischargeResourceCardRequest(header, request)
        
        for x in req.common_reward_user_data:            
            sn = f"2{str(randint(1, 999999999999999999)).zfill(18)}"
            self.logger.info(f"User {req.user_id} printed {'holo ' if req.holographic_flag == 1 else ''}resource card {x.user_common_reward_id} {req.execute_print_type}, code {sn}")
            await self.data.profile.put_resource_card(req.user_id, sn, x.common_reward_type, x.user_common_reward_id, req.holographic_flag)

        return SaoDischargeProfileCardResponse(sn).make()

    async def handle_c304(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # card/discharge_resource_card_complete
        req = SaoDischargeResourceCardCompleteRequest(header, request)
        self.logger.info(f"User {req.user_id} finished printing resource card {req.resource_card_code}")
        return SaoNoopResponse(GameconnectCmd.DISCHARGE_RESOURCE_CARD_COMPLETE_RESPONSE).make()

    async def handle_c306(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #card/scan_qr_quest_profile_card
        req = SaoScanQrQuestProfileCardRequest(header, request)
        resp = SaoScanQrQuestProfileCardResponse()
        
        card = await self.data.profile.get_hero_card(req.profile_card_code)
        if not card:
            self.logger.warning(f"User {req.user_id} scanned unregistered QR code {req.profile_card_code}")
            return resp.make()
        
        hero = await self.data.item.get_hero_log_by_id(card['user_hero_id'])
        if not hero: # Shouldn't happen
            self.logger.warning(f"User {req.user_id} scanned QR code {req.profile_card_code} but does not have hero entry {card['user_hero_id']}")
            return resp.make()
        
        hero_static_data = await self.data.static.get_hero_by_id(hero['hero_log_id'])
        if not hero_static_data: # Shouldn't happen
            self.logger.warning(f"No entry for hero {hero['hero_log_id']}, please run read.py")
            return resp.make()
        
        profile = await self.data.profile.get_profile(card['user'])
        if not profile: # Shouldn't happen
            self.logger.warning(f"No profile for user {card['user']}, something broke")
            return resp.make()

        self.logger.info(f"User {req.user_id} scanned QR code {req.profile_card_code}")
        card_resp = ReadProfileCard.from_args(req.profile_card_code, profile['nick_name'])
        card_resp.rank_num = profile['rank_num']
        card_resp.setting_title_id = profile['setting_title_id']
        card_resp.skill_id = hero['skill_slot1_skill_id']
        card_resp.hero_log_hero_log_id = hero['hero_log_id']
        card_resp.hero_log_log_level = hero['log_level']
        #TODO: Awakening
        #card_resp.hero_log_awakening_stage = hero['log_level'] 

        resp.profile_card_data.append(card_resp)
        return resp.make()

    async def handle_c308(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # card/scan_qr_shop_resource_card
        req = SaoScanQrShopResourceCardRequest(header, request)
        self.logger.info(f"User {req.user_id} scanned shop resource card {req.resource_card_code}")
        resp = SaoNoopResponse(GameconnectCmd.SCAN_QR_SHOP_RESOURCE_CARD_RESPONSE)
        # On official, resource cards have limited uses, but we don't track that currently (tho we should)
        
        card = await self.data.profile.get_resource_card(req.resource_card_code) # TODO: use count
        if not card:
            self.logger.warning(f"No resource card with serial {req.resource_card_code} exists!")
            resp.header.err_status = 4832 # Theres a few error codes but none seem to do anything?
            # Also not sure if it should be this or result

        return resp.make()

    async def handle_c30a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # card/scan_qr_quest_resource_card
        req = SaoScanQrQuestResourceCardRequest(header, request)
        self.logger.info(f"User {req.user_id} scanned quest resource card {req.resource_card_code}")
        
        card = await self.data.profile.get_resource_card(req.resource_card_code)
        if not card:
            resp = SaoScanQrQuestResourceCardResponse(card['common_reward_type'], card['common_reward_id'], card['holographic_flag'])
        
        else:            
            self.logger.warning(f"No resource card with serial {req.resource_card_code} exists!")
            resp = SaoScanQrQuestResourceCardResponse()
            resp.header.err_status = 4832 # Theres a few error codes but none seem to do anything?
            # Also not sure if it should be this or result

        return resp.make()

    async def handle_c400(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #home/check_yui_medal_get_condition
        req = SaoCheckYuiMedalGetConditionRequest(header, request)
        profile = await self.data.profile.get_profile(req.user_id)
        if profile['last_yui_medal_date']:
            last_check_ts = int(profile['last_yui_medal_date'].timestamp())
            day_ts = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            diff_ts = day_ts - last_check_ts
            if diff_ts > 0:
                num_days = diff_ts / 86400
            else:
                num_days = 0
        else:
            num_days = 1
        
        if num_days > 1:
            await self.data.profile.add_yui_medals(req.user_id)
        
        await self.data.profile.update_yui_medal_date(req.user_id)
        return SaoCheckYuiMedalGetConditionResponse(num_days, 1 if num_days > 1 else 0).make()

    async def handle_c402(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #home/get_yui_medal_bonus_user_data
        req = SaoGetYuiMedalBonusUserDataRequest(header, request)
        resp = SaoGetYuiMedalBonusUserDataResponse() # TODO: Track yui login bonus
        return resp.make()

    async def handle_c404(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # home/check_comeback_event
        req = SaoGenericUserTicketRequest(header, request)
        resp = SaoCheckComebackEventResponse()
        #resp.get_comeback_event_id_list += [1,2,3,4] # TODO: track comeback date
        return resp.make()

    async def handle_c406(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # home/change_my_store
        req = SaoChangeMyStoreRequest(header, request)
        self.logger.info(f"User {req.user_id} changed My Store to {req.store_id}")
        shop_id = int(req.store_id[3:], 16)
        await self.data.profile.set_my_shop(req.user_id, shop_id)
        return SaoNoopResponse(GameconnectCmd.CHANGE_MY_STORE_RESPONSE).make()

    async def handle_c408(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # home/check_title_get_decision
        req = SaoCheckTitleGetDecisionRequest(header, request)
        resp = SaoCheckTitleGetDecisionResponse() # TODO: titles
        return resp.make()

    async def handle_c40a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # home/check_profile_card_used_reward
        req = SaoCheckProfileCardUsedRewardRequest(header, request)
        resp = SaoCheckProfileCardUsedRewardResponse() # TODO: check_profile_card_used_reward
        return resp.make()

    async def handle_c40c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # home/check_ac_login_bonus
        req = SaoGenericUserTicketRequest(header, request)
        resp = SaoCheckAcLoginBonusResponse()
        #resp.get_ac_login_bonus_id_list.append(1) # TODO: track login bonus date
        #resp.get_ac_login_bonus_id_list.append(2)
        return resp.make()

    async def handle_c500(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # user_info/get_user_basic_data
        req = SaoGetUserBasicDataRequest(header, request)

        profile_data = await self.data.profile.get_profile(req.user_id)
        player_rank_data = self.load_data_csv("PlayerRank")

        resp = SaoGetUserBasicDataResponse(profile_data)
        for e in player_rank_data:
            if resp.user_basic_data[0].rank_num == int(e['PlayerRankId']):
                resp.user_basic_data[0].rank_exp = resp.user_basic_data[0].rank_exp - int(e["TotalExp"])
                break
        
        if profile_data['my_shop']:
            ac = await self.data.arcade.get_arcade(profile_data['my_shop'])
            if ac:
                # TODO: account for machine override
                resp.user_basic_data[0].my_store_id = f"{ac['country']}0{ac['id']:04d}"
                resp.user_basic_data[0].my_store_name = ac['name']
        
        return resp.make()

    async def handle_c502(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # user_info/get_vp_gasha_ticket_data_list
        req = SaoGetVpGashaTicketDataListRequest(header, request)
        # TODO: gasha tickets
        resp = SaoGetVpGashaTicketDataListResponse()
        return resp.make()

    async def handle_c504(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # user_info/get_present_box_num
        req = SaoGenericUserRequest(header, request)
        # TODO: presents
        return SaoGetPresentBoxNumResponse().make()

    async def handle_c600(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_hero_log_user_data_list
        req = SaoGenericUserRequest(header, request)
        hero_level_data = self.load_data_csv("HeroLogLevel")

        hero_data = await self.data.item.get_hero_logs(req.user_id)
        
        resp = SaoGetHeroLogUserDataListResponse()
        for hero in hero_data:
            append = HeroLogUserData.from_args(hero)
            hero_static = await self.data.static.get_hero_by_id(hero['hero_log_id'])
            if not hero_static:
                self.logger.warning(f"No hero for id {hero['hero_log_id']}, please run reader")
                resp.hero_log_user_data_list.append(append)
                continue

            append.property1_property_id = hero_static['Property1PropertyId'] if hero_static['Property1PropertyId'] else 0
            append.property1_value1 = hero_static['Property1Value1'] if hero_static['Property1Value1'] else 0
            append.property1_value2 = hero_static['Property1Value2'] if hero_static['Property1Value2'] else 0
            append.property2_property_id = hero_static['Property2PropertyId'] if hero_static['Property2PropertyId'] else 0
            append.property2_value1 = hero_static['Property2Value1'] if hero_static['Property2Value1'] else 0
            append.property2_value2 = hero_static['Property2Value2'] if hero_static['Property2Value2'] else 0
            append.property3_property_id = hero_static['Property3PropertyId'] if hero_static['Property3PropertyId'] else 0
            append.property3_value1 = hero_static['Property3Value1'] if hero_static['Property3Value1'] else 0
            append.property3_value2 = hero_static['Property3Value2'] if hero_static['Property3Value2'] else 0
            append.property4_property_id = hero_static['Property4PropertyId'] if hero_static['Property4PropertyId'] else 0
            append.property4_value1 = hero_static['Property4Value1'] if hero_static['Property4Value1'] else 0
            append.property4_value2 = hero_static['Property4Value2'] if hero_static['Property4Value2'] else 0

            for e in hero_level_data:
                if hero['log_level'] == int(e['HeroLogLevelId']):
                    append.log_exp = hero['log_exp'] - int(e["TotalExp"])
                    break
            resp.hero_log_user_data_list.append(append)

        return resp.make()

    async def handle_c602(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_equipment_user_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetEquipmentUserDataListResponse()
        equip_level_data = self.load_data_csv("EquipmentLevel")
    
        equipment_data = await self.data.item.get_user_equipments(req.user_id)
            
        if equipment_data:
            for equipment in equipment_data:
                e = EquipmentUserData.from_args(equipment)
                weapon_static = await self.data.static.get_equipment_by_id(equipment['equipment_id'])
                if not weapon_static:
                    self.logger.warning(f"No equipment for id {equipment['equipment_id']}, please run reader")
                    resp.equipment_user_data_list.append(e)
                    continue
                
                if not e.property1_property_id:
                    e.property1_property_id = weapon_static['Property1PropertyId'] if weapon_static['Property1PropertyId'] else 0
                    e.property1_value1 = weapon_static['Property1Value1'] if weapon_static['Property1Value1'] else 0
                    e.property1_value2 = weapon_static['Property1Value2'] if weapon_static['Property1Value2'] else 0
                
                if not e.property2_property_id:
                    e.property2_property_id = weapon_static['Property2PropertyId'] if weapon_static['Property2PropertyId'] else 0
                    e.property2_value1 = weapon_static['Property2Value1'] if weapon_static['Property2Value1'] else 0
                    e.property2_value2 = weapon_static['Property2Value2'] if weapon_static['Property2Value2'] else 0
                
                if e.property3_property_id:
                    e.property3_property_id = weapon_static['Property3PropertyId'] if weapon_static['Property3PropertyId'] else 0
                    e.property3_value1 = weapon_static['Property3Value1'] if weapon_static['Property3Value1'] else 0
                    e.property3_value2 = weapon_static['Property3Value2'] if weapon_static['Property3Value2'] else 0
                
                if e.property4_property_id:
                    e.property4_property_id = weapon_static['Property4PropertyId'] if weapon_static['Property4PropertyId'] else 0
                    e.property4_value1 = weapon_static['Property4Value1'] if weapon_static['Property4Value1'] else 0
                    e.property4_value2 = weapon_static['Property4Value2'] if weapon_static['Property4Value2'] else 0
                
                for f in equip_level_data:                
                    if equipment['enhancement_value'] == int(f['EquipmentLevelId']):
                        e.enhancement_exp = equipment['enhancement_exp'] - int(f["TotalExp"])
                        break
                resp.equipment_user_data_list.append(e)

        return resp.make()

    async def handle_c604(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_item_user_data_list
        req = SaoGenericUserRequest(header, request)

        item_data = await self.data.item.get_user_items(req.user_id)

        resp = SaoGetItemUserDataListResponse(item_data)
        return resp.make()

    async def handle_c606(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_support_log_user_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetSupportLogUserDataListResponse()
        supports = self.load_data_csv("SupportLog")
        # TODO: Save supports
        
        for x in range(len(supports)):
            tmp = SupportLogUserData.from_args(f"{req.user_id}{x}", supports[x]['SupportLogId'])
            resp.support_log_user_data_list.append(tmp)
        return resp.make()

    async def handle_c608(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #have_object/get_episode_append_data_list
        req = SaoGenericUserRequest(header, request)
        # TODO: Appends
        resp = SaoGetEpisodeAppendDataListResponse()
        return resp.make()
    
    async def handle_c60a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_event_item_data_list
        req = SaoGenericUserRequest(header, request)
        res = SaoGetEventItemDataListResponse()
        # TODO: Event items maybe
        return res.make()
    
    async def handle_c60c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # have_object/get_gasha_medal_user_data_list
        req = SaoGenericUserRequest(header, request)
        res = SaoGetGashaMedalUserDataListResponse()
        # TODO: Gasha Medal data
        return res.make()

    async def handle_c700(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # shop/get_shop_resource_sales_data_list
        # TODO: Get user shop data
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetShopResourceSalesDataListResponse()
        return resp.make()

    async def handle_c702(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # shop/purchase_shop_resource
        req = SaoPurchaseShopResourceRequest(header, request)
        self.logger.infof(f"User {req.user_id} (ticket {req.ticket_id}) purchased shop resourse {req.user_shop_resource_id}")
        # TODO: Shop purchases
        return SaoNoopResponse(GameconnectCmd.PURCHASE_SHOP_RESOURCE_RESPONSE).make()

    async def handle_c704(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # shop/discard_shop_resource
        req = SaoPurchaseShopResourceRequest(header, request)
        self.logger.infof(f"User {req.user_id} (ticket {req.ticket_id}) discarded shop resourse {req.user_shop_resource_id}")
        return SaoNoopResponse(GameconnectCmd.DISCARD_SHOP_RESOURCE_RESPONSE).make()
    
    async def handle_c800(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # custom/get_title_user_data_list
        req = SaoGenericUserRequest(header, request)
        titleIdsData = await self.data.static.get_title_ids(0, True)
        # TODO: Save titles
        
        resp = SaoGetTitleUserDataListResponse(req.user_id, titleIdsData)
        return resp.make()
    
    async def handle_c802(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # custom/change_title
        req = SaoChangeTitleRequest(header, request)
        self.logger.info(f"User {req.user_id} (ticket {req.ticket_id}) changed their title to {req.user_title_id}")
        await self.data.profile.set_title(req.user_id, req.user_title_id)
        
        return SaoNoopResponse(GameconnectCmd.CHANGE_TITLE_RESPONSE).make()

    async def handle_c804(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # custom/get_party_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetPartyDataListResponse()

        hero_parties = await self.data.item.get_hero_party(req.user_id)
        for party in hero_parties:
            hero1_data = await self.data.item.get_user_hero_by_id(party['user_hero_log_id_1'])
            hero2_data = await self.data.item.get_user_hero_by_id(party['user_hero_log_id_2'])
            hero3_data = await self.data.item.get_user_hero_by_id(party['user_hero_log_id_3'])
            
            resp.party_data_list.append(PartyData.from_args(party['id'], party['user_party_team_id'], hero1_data._asdict(), hero2_data._asdict(), hero3_data._asdict()))

        return resp.make()

    async def handle_c808(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # custom/get_support_log_party_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetSupportLogPartyDataListResponse()
        # TODO: Support logs
        return resp.make()

    async def handle_c812(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # custom/disposal_resource
        req = SaoDisposalResourceRequest(header, request)
        get_col = 0
        for disposal in req.disposal_common_reward_user_data_list:
            if disposal.common_reward_type == RewardType.HeroLog:
                removed_hero = await self.data.item.remove_hero_log(disposal.user_common_reward_id)
                if removed_hero:
                    static_hero = await self.data.static.get_hero_by_id(removed_hero)
                    get_col += static_hero['SalePrice']
            
            elif disposal.common_reward_type == RewardType.Equipment:
                removed_equip = await self.data.item.remove_equipment(disposal.user_common_reward_id)
                if removed_equip:
                    static_equip = await self.data.static.get_equipment_by_id(removed_equip)
                    get_col += static_equip['SalePrice']

            elif disposal.common_reward_type == RewardType.Item:
                removed_equip = await self.data.item.remove_item(disposal.user_common_reward_id)
                if removed_equip:
                    static_equip = await self.data.static.get_equipment_by_id(removed_equip)
                    get_col += static_equip['SalePrice']

            elif disposal.common_reward_type == RewardType.SupportLog:
                continue

            else:
                self.logger.warning(f"Unhandled disposal type {disposal.common_reward_type}")

        await self.data.profile.add_col(req.user_id, get_col)
        return SaoDisposalResourceResponse(get_col).make()

    async def handle_c814(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #custom/synthesize_enhancement_hero_log
        req = SaoSynthesizeEnhancementHeroLogRequest(header, request)
        resp = SaoSynthesizeEnhancementHeroLogResponse()
        hero_level_data = self.load_data_csv("HeroLogLevel")
        equip_level_data = self.load_data_csv("EquipmentLevel")
        hero_exp = 0
        col_cost = 0

        for x in req.material_common_reward_user_data_list:
            if x.common_reward_type == RewardType.Item:
                user_item = await self.data.item.get_user_item_by_id(x.user_common_reward_id)
                static_item = await self.data.static.get_item_id(user_item['item_id'])
                
                if int(static_item['ItemTypeId']) == 7:
                    hero_exp += int(static_item['Value'])
                    self.logger.info(f"Remove item {x.user_common_reward_id} and add {int(static_item['Value'])} XP (running {hero_exp})")
                    await self.data.item.remove_item(x.user_common_reward_id)

            elif x.common_reward_type == RewardType.Equipment:
                equipment_data = await self.data.item.get_user_equipment_by_id(x.user_common_reward_id)
                if equipment_data is None:
                    self.logger.error(f"Failed to find equipment {x.user_common_reward_id} for user {req.user_id}!")
                    continue
                
                req_exp = 0
                for e in range(len(equip_level_data)):
                    if equipment_data['enhancement_value'] == int(equip_level_data[e]['EquipmentLevelId']):
                        req_exp = equip_level_data[e + 1]['RequireExp']
                        break
                
                static_equip_data = await self.data.static.get_equipment_by_id(equipment_data['equipment_id'])
                
                hero_exp += int(static_equip_data['CompositionExp']) + req_exp
                self.logger.info(f"Remove equipment {x.user_common_reward_id} and add {int(static_equip_data['CompositionExp']) + req_exp} XP (running {hero_exp})")
                await self.data.item.remove_equipment(x.user_common_reward_id)

            elif x.common_reward_type == RewardType.HeroLog:
                hero_data = await self.data.item.get_hero_log_by_id(x.user_common_reward_id)
                if hero_data is None:
                    self.logger.error(f"Failed to find hero {x.user_common_reward_id} for user {req.user_id}!")
                    continue

                req_exp = 0
                for e in range(len(hero_level_data)):
                    if hero_data['log_level'] == int(hero_level_data[e]['HeroLogLevelId']):
                        req_exp = hero_level_data[e + 1]['RequireExp']
                        break
                
                static_hero_data = await self.data.static.get_hero_by_id(hero_data['hero_log_id'])
                
                hero_exp += int(static_hero_data['CompositionExp']) + req_exp
                self.logger.info(f"Remove hero {x.user_common_reward_id} and add {int(static_hero_data['CompositionExp']) + req_exp} XP (running {hero_exp})")
                await self.data.item.remove_hero_log(x.user_common_reward_id)
            
            else:
                self.logger.warning(f"Unhandled ype {x.common_reward_type}! (running {hero_exp})")
        
        hero_exp = int(hero_exp * 1.5)
        await self.data.item.add_hero_xp(req.origin_user_hero_log_id, hero_exp)
        log_exp = await self.data.item.get_hero_xp(req.origin_user_hero_log_id)
        pre_synth_xp = log_exp - hero_exp
        pre_synth_level = 1
        
        for e in range(len(hero_level_data)):
            if log_exp>=int(hero_level_data[e]["TotalExp"]) and log_exp<int(hero_level_data[e+1]["TotalExp"]):
                self.logger.info(f"Set hero {req.origin_user_hero_log_id} level {hero_level_data[e]['HeroLogLevelId']}")
                remain_exp = log_exp - int(hero_level_data[e]["TotalExp"])
                await self.data.item.set_hero_level(req.origin_user_hero_log_id, hero_level_data[e]["HeroLogLevelId"])
                break

        for e in range(len(hero_level_data)):
            if pre_synth_xp>=int(hero_level_data[e]["TotalExp"]) and pre_synth_xp<int(hero_level_data[e+1]["TotalExp"]):
                pre_synth_level = int(hero_level_data[e]["HeroLogLevelId"])
                break

        # Load the item again to push to the response handler
        synthesize_hero_log_data = await self.data.item.get_hero_log_by_id(req.origin_user_hero_log_id)
        
        col_cost = pre_synth_level * (100 * len(req.material_common_reward_user_data_list)) * (1 - synthesize_hero_log_data['awakening_stage'] * 0.1)
        if pre_synth_level >= 100:
            col_cost = col_cost * 10
        
        col_cost = col_cost * 1000
        col_cost = max(100, int(col_cost / 1000))
        
        self.logger.info(f"Synthesize {hero_exp} exp for hero {req.origin_user_hero_log_id}, costing {col_cost} col")
        
        await self.data.profile.add_col(req.user_id, -col_cost)
        if synthesize_hero_log_data is not None:
            resp.after_hero_log_user_data.append(HeroLogUserData.from_args(synthesize_hero_log_data))
            resp.after_hero_log_user_data[0].log_exp = remain_exp
        return resp.make()

    async def handle_c816(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #custom/synthesize_enhancement_equipment
        req_data = SaoSynthesizeEnhancementEquipmentRequest(header, request)
        resp = SaoSynthesizeEnhancementEquipmentResponse()
        hero_level_data = self.load_data_csv("HeroLogLevel")
        equip_level_data = self.load_data_csv("EquipmentLevel")
        equipment_exp = 0
        col_cost = 0

        for x in req_data.material_common_reward_user_data_list:
            if x.common_reward_type == RewardType.Item:
                user_item = await self.data.item.get_user_item_by_id(x.user_common_reward_id)
                static_item = await self.data.static.get_item_id(user_item['item_id'])
                
                if int(static_item['ItemTypeId']) == 7:
                    equipment_exp += int(static_item['Value'])
                    self.logger.info(f"Remove item {x.user_common_reward_id} and add {int(static_item['Value'])} XP (running {equipment_exp})")
                    await self.data.item.remove_item(x.user_common_reward_id)

            elif x.common_reward_type == RewardType.Equipment:
                equipment_data = await self.data.item.get_user_equipment_by_id(x.user_common_reward_id)
                if equipment_data is None:
                    self.logger.error(f"Failed to find equipment {x.user_common_reward_id} for user {req_data.user_id}!")
                    continue
                
                req_exp = 0
                for e in range(len(equip_level_data)):
                    if equipment_data['enhancement_value'] == int(equip_level_data[e]['EquipmentLevelId']):
                        req_exp = equip_level_data[e + 1]['RequireExp']
                        break
                
                static_equip_data = await self.data.static.get_equipment_by_id(equipment_data['equipment_id'])
                
                equipment_exp += int(static_equip_data['CompositionExp']) + req_exp
                self.logger.info(f"Remove equipment {x.user_common_reward_id} and add {int(static_equip_data['CompositionExp']) + req_exp} XP (running {equipment_exp})")
                await self.data.item.remove_equipment(x.user_common_reward_id)

            elif x.common_reward_type == RewardType.HeroLog:
                hero_data = await self.data.item.get_hero_log_by_id(x.user_common_reward_id)
                if hero_data is None:
                    self.logger.error(f"Failed to find hero {x.user_common_reward_id} for user {req_data.user_id}!")
                    continue

                req_exp = 0
                for e in range(len(hero_level_data)):
                    if hero_data['log_level'] == int(hero_level_data[e]['HeroLogLevelId']):
                        req_exp = hero_level_data[e + 1]['RequireExp']
                        break
                
                static_hero_data = await self.data.static.get_hero_by_id(hero_data['hero_log_id'])
                
                equipment_exp += int(static_hero_data['CompositionExp']) + req_exp
                self.logger.info(f"Remove hero {x.user_common_reward_id} and add {int(static_hero_data['CompositionExp']) + req_exp} XP (running {equipment_exp})")
                await self.data.item.remove_hero_log(x.user_common_reward_id)
            
            else:
                self.logger.warning(f"Unhandled ype {x.common_reward_type}! (running {equipment_exp})")
        
        equipment_exp = int(equipment_exp * 1.5)
        await self.data.item.add_equipment_enhancement_exp(req_data.origin_user_equipment_id, equipment_exp)
        synthesize_equipment_data = await self.data.item.get_user_equipment(req_data.user_id, req_data.origin_user_equipment_id)
        equip_exp_new = synthesize_equipment_data['enhancement_exp']
        pre_synth_level = synthesize_equipment_data['enhancement_value']
        new_synth_level = 1
        
        for e in range(len(equip_level_data)):
            if equip_exp_new>=int(equip_level_data[e]["TotalExp"]) and equip_exp_new<int(equip_level_data[e+1]["TotalExp"]):
                self.logger.info(f"Set equipment {req_data.origin_user_equipment_id} level {equip_level_data[e]['EquipmentLevelId']}")
                new_synth_level = equip_level_data[e]['EquipmentLevelId']
                remain_exp = equip_exp_new - int(equip_level_data[e]["TotalExp"])
                await self.data.item.set_equipment_enhancement_value(req_data.origin_user_equipment_id, equip_level_data[e]["EquipmentLevelId"])
                break

        # Load the item again to push to the response handler  
        
        col_cost = pre_synth_level * (100 * len(req_data.material_common_reward_user_data_list)) * (1 - synthesize_equipment_data['awakening_stage'] * 0.1)
        if pre_synth_level >= 100:
            col_cost = col_cost * 10
        
        col_cost = col_cost * 1000
        col_cost = max(100, int(col_cost / 1000))
        
        self.logger.info(f"Synthesize {equipment_exp} exp for equipment {req_data.origin_user_equipment_id}, costing {col_cost} col")
        
        await self.data.profile.add_col(req_data.user_id, -col_cost)
        if synthesize_equipment_data is not None:
            resp.after_equipment_user_data.append(EquipmentUserData.from_args(synthesize_equipment_data))
            resp.after_equipment_user_data[0].enhancement_exp = remain_exp
            resp.after_equipment_user_data[0].enhancement_value = new_synth_level
        return resp.make()

    async def handle_c806(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #custom/change_party
        req_data = SaoChangePartyRequest(header, request)

        for party_team in req_data.party_data_list:
            for hero in party_team.party_team_data_list:
                await self.data.item.set_user_hero_weapons(
                    int(hero.user_hero_log_id), 
                    int(hero.main_weapon_user_equipment_id) if hero.main_weapon_user_equipment_id and int(hero.main_weapon_user_equipment_id) > 0 else None, 
                    int(hero.sub_equipment_user_equipment_id) if hero.sub_equipment_user_equipment_id and int(hero.sub_equipment_user_equipment_id) > 0 else None
                )
                await self.data.item.set_user_hero_skills(
                    int(hero.user_hero_log_id), 
                    hero.skill_slot1_skill_id if hero.skill_slot1_skill_id > 0 else None, 
                    hero.skill_slot2_skill_id if hero.skill_slot2_skill_id > 0 else None, 
                    hero.skill_slot3_skill_id if hero.skill_slot3_skill_id > 0 else None, 
                    hero.skill_slot4_skill_id if hero.skill_slot4_skill_id > 0 else None, 
                    hero.skill_slot5_skill_id if hero.skill_slot5_skill_id > 0 else None
                )


            await self.data.item.put_hero_party(
                req_data.user_id,
                party_team.team_no,
                party_team.party_team_data_list[0].user_hero_log_id,
                party_team.party_team_data_list[1].user_hero_log_id,
                party_team.party_team_data_list[2].user_hero_log_id,
            )

        resp = SaoNoopResponse(GameconnectCmd.CHANGE_PARTY_RESPONSE)
        return resp.make()

    async def handle_c900(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest/get_quest_scene_user_data_list
        req = SaoGenericUserRequest(header, request)

        quest_data = await self.data.item.get_quest_logs(req.user_id)

        resp = SaoGetQuestSceneUserDataListResponse()
        for quest in quest_data:
            ex_bonus_data = await self.data.item.get_player_ex_bonus_by_quest(req.user_id, quest["quest_scene_id"])
            tmp = QuestSceneUserData.from_args(quest)
            
            for ex_bonus in ex_bonus_data:
                tmp.quest_scene_ex_bonus_user_data_list.append(QuestSceneExBonusUserData.from_args(ex_bonus['ex_bonus_table_id'], ex_bonus['quest_clear_flag']))
            
            resp.quest_scene_user_data_list.append(tmp)
        return resp.make()

    async def handle_c902(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes: # for whatever reason, having all entries empty or filled changes nothing
        #quest/get_quest_scene_prev_scan_profile_card
        resp = SaoGetQuestScenePrevScanProfileCardResponse()
        resp.profile_card_data.append(ReadProfileCardData.from_args({}, {}))
        return resp.make()

    async def handle_c904(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest/episode_play_start
        req_data = SaoEpisodePlayStartRequest(header, request)

        user_id = req_data.user_id
        profile_data = await self.data.profile.get_profile(user_id)

        sesh_id = await self.data.item.create_session(
            user_id, 
            int(req_data.play_start_request_data[0].user_party_id), 
            req_data.episode_id, 
            req_data.play_mode, 
            req_data.play_start_request_data[0].quest_drop_boost_apply_flag
            )

        resp = SaoEpisodePlayStartResponse()
        resp.play_start_response_data.append(QuestScenePlayStartResponseData.from_args(sesh_id, profile_data['nick_name']))
        resp.multi_play_start_response_data.append(QuestSceneMultiPlayStartResponseData.from_args())
        return resp.make()

    async def handle_c908(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes: # Level calculation missing for the profile and heroes
        #quest/episode_play_end
        req_data = SaoEpisodePlayEndRequest(header, request)
        resp = SaoEpisodePlayEndResponse()

        user_id = req_data.user_id
        episode_id = req_data.episode_id
        play_end = req_data.play_end_request_data[0]
        base_get_data = play_end.base_get_data[0]
        score_data = play_end.score_data[0]
        exp = 0
        cleared_mission_ct = 0
        highest_mission_diff_cleared = 0
        num_monsters_defeated = 0
        monsters_defeated_data = {}
        json_data = {"data": []}
        
        ep_data = await self.data.static.get_episode_by_id(req_data.episode_id)
        quest_scene = await self.data.static.get_quest_by_id(int(ep_data['QuestSceneId']))
        reward_table = await self.data.static.get_rewards_by_subtable(int(quest_scene['RewardTableSubId']))
        ex_bonus_table = await self.data.static.get_ex_bonuses_by_subtable(int(ep_data['ExBonusTableSubId']))

        await self.data.profile.add_col(user_id, base_get_data.get_col)

        quest_clear_flag = score_data.clear_time > 0
        clear_time = score_data.clear_time
        combo_num = score_data.combo_num
        total_damage = score_data.total_damage
        concurrent_destroying_num = score_data.concurrent_destroying_num
        
        if quest_clear_flag is True:
            await self.data.profile.add_vp(user_id, quest_scene['SingleRewardVp'])
            await self.data.profile.add_exp(user_id, quest_scene['SuccessPlayerExp'])
            exp = await self.data.profile.get_exp(user_id)
        
        else:
            await self.data.profile.add_exp(user_id, quest_scene['FailedPlayerExp'])
            exp = await self.data.profile.get_exp(user_id)
        
        # Calculate level based off experience and the CSV list
        player_level_data = self.load_data_csv("PlayerRank")
            
        for i in range(0,len(player_level_data)):
            if exp>=int(player_level_data[i]["TotalExp"]) and exp<int(player_level_data[i+1]["TotalExp"]):
                await self.data.profile.set_level(user_id, int(player_level_data[i]["PlayerRankId"]))
                break
        current_data = await self.data.item.get_quest_log(user_id, ep_data['QuestSceneId'])
        if current_data:
            await self.data.item.put_player_quest(
                user_id, 
                int(QuestType.EPISODE),
                ep_data['QuestSceneId'], 
                False if not quest_clear_flag and not current_data['quest_clear_flag'] else True, 
                min(clear_time, current_data['clear_time']) if quest_clear_flag else current_data['clear_time'], 
                max(combo_num, current_data['combo_num']), 
                max(int(total_damage), current_data['total_damage']), 
                max(concurrent_destroying_num, current_data['concurrent_destroying_num'])
            )
        else:
            await self.data.item.put_player_quest(
                user_id, 
                int(QuestType.EPISODE),
                ep_data['QuestSceneId'], 
                quest_clear_flag, 
                clear_time, 
                combo_num, 
                total_damage, 
                concurrent_destroying_num
            )

        for mission in play_end.mission_data_list:
            if mission.clear_flag == 1:
                cleared_mission_ct += 1
                if mission.mission_difficulty_id > highest_mission_diff_cleared:
                    highest_mission_diff_cleared = mission.mission_difficulty_id

        for monster_data in play_end.discovery_enemy_data_list:
            num_monsters_defeated += monster_data.destroy_num
            monsters_defeated_data[monster_data.enemy_kind_id] = monster_data.destroy_num

        for bonus in ex_bonus_table:
            table_id = int(bonus['ExBonusTableId'])
            ach_thing = 0
            condition = int(bonus['ExBonusConditionId'])
            val1 = int(bonus['ConditionValue1'])
            val2 = int(bonus['ConditionValue2'])
            if condition == ExBonusCondition.CLEAR_UNDER_X_SECS:
                if quest_clear_flag and int(score_data.clear_time / 1000) < val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.DEFEAT_X_MONSTER_Y_TIMES:
                if monsters_defeated_data.get(val1, 0) >= val2:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.DEFEAT_X_MONSTERS:
                if num_monsters_defeated >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_X_MISSIONS:
                if cleared_mission_ct >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_MISSION_DIFFICULTY_X:
                if highest_mission_diff_cleared >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.COLLECT_X_LOGS:
                if len(play_end.get_unanalyzed_log_tmp_reward_data_list) >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_SKILL_LEVEL_X:
                if score_data.reaching_skill_level >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.NO_LOSSES:
                if score_data.total_loss_num == 0:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.ACCEL_X_TIMES:
                if score_data.acceleration_invocation_num >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.MAX_COMBO_X:
                if score_data.combo_num >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.MULTIPLAYER_CLEAR_X:
                # TODO
                pass
            else:
                self.logger.warning(f"Unhandled EX Bonus condition {condition}")
            
            resp.play_end_response_data[0].ex_bonus_data_list.append(QuestScenePlayEndExBonusData.from_args(table_id, ach_thing))

        self.logger.info(f"User {user_id} {'cleared' if quest_clear_flag else 'ended'} episode {episode_id}")

        for rare_drop in play_end.get_rare_drop_data_list:
            rewardList = self.load_data_csv("QuestRareDrop")
            for drop in rewardList:
                if int(drop['QuestRareDropId']) == rare_drop.quest_rare_drop_id:
                    await self.add_reward(drop, user_id)
                    break

        for unanalyzed_log in play_end.get_unanalyzed_log_tmp_reward_data_list:
            able_rewards: List[Row] = []
            for reward in reward_table:
                if int(reward['UnanalyzedLogGradeId']) == unanalyzed_log.unanalyzed_log_grade_id:
                    able_rewards.append(reward)
            randomized_unanalyzed_id = choice(able_rewards)
            
            await self.add_reward(randomized_unanalyzed_id._asdict(), user_id)
            json_data["data"].append(randomized_unanalyzed_id._asdict())
        
        
        trace_table = await self.data.static.get_player_trace_by_subid(quest_scene['PlayerTraceTableSubId'])
        
        for trace in play_end.get_player_trace_data_list:
            self.logger.info(f"User {user_id} obtained trace {trace.user_quest_scene_player_trace_id}")
            resp.play_end_response_data[0].play_end_player_trace_reward_data_list.append(QuestScenePlayEndPlayerTraceRewardData.from_args(choice(trace_table)._asdict()))

        await self.data.item.create_end_session(user_id, ep_data['QuestSceneId'], play_end.play_result_flag, json_data["data"])

        # Update heroes from the used party
        play_session = await self.data.item.get_session(user_id)
        session_party = await self.data.item.get_hero_party_by_id(play_session["user_party_team_id"])
        if session_party:
            hero_level_data = self.load_data_csv("HeroLogLevel")
            hero_list = []
            hero_list.append(session_party["user_hero_log_id_1"])
            hero_list.append(session_party["user_hero_log_id_2"])
            hero_list.append(session_party["user_hero_log_id_3"])

            for i in range(0,3):
                await self.data.item.add_hero_xp(hero_list[i], base_get_data.get_hero_log_exp)
                log_exp = await self.data.item.get_hero_xp(hero_list[i])

                # Calculate hero level based off experience and the CSV list
                if log_exp:
                    for e in range(0,len(hero_level_data)):
                        if log_exp>=int(hero_level_data[e]["TotalExp"]) and log_exp<int(hero_level_data[e+1]["TotalExp"]):
                            self.logger.info(f"Set hero {hero_list[i]} level {hero_level_data[e]['HeroLogLevelId']} ({log_exp} total XP)")
                            await self.data.item.set_hero_level(hero_list[i], hero_level_data[e]['HeroLogLevelId'])
                            break
        else:
            self.logger.error(f"Failed to get session party {play_session['user_party_team_id']} data for user {user_id}!")

        return resp.make()

    async def handle_c90a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest/episode_play_end_unanalyzed_log_fixed
        req = SaoEpisodePlayEndUnanalyzedLogFixedRequest(header, request)
        resp = SaoEpisodePlayEndUnanalyzedLogFixedResponse()

        end_session_data = await self.data.item.get_end_session(req.user_id)
        for data in end_session_data['reward_data']:
            resp.play_end_unanalyzed_log_reward_data_list.append(QuestScenePlayEndUnanalyzedLogRewardData.from_args(data['UnanalyzedLogGradeId'], data))

        return resp.make()

    async def handle_c914(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest/trial_tower_play_start
        req_data = SaoTrialTowerPlayStartRequest(header, request)

        user_id = req_data.user_id
        profile_data = await self.data.profile.get_profile(user_id)

        sesh_id = await self.data.item.create_session(
            user_id, 
            int(req_data.play_start_request_data[0].user_party_id), 
            req_data.trial_tower_id, 
            req_data.play_mode, 
            req_data.play_start_request_data[0].quest_drop_boost_apply_flag
            )

        self.logger.info(f"User {req_data.user_id} started trial tower on floor {req_data.trial_tower_id}")
        resp = SaoTrialTowerPlayStartResponse(sesh_id, profile_data['nick_name'])
        return resp.make()

    async def handle_c918(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest/trial_tower_play_end
        req_data = SaoTrialTowerPlayEndRequest(header, request)
        resp = SaoTrialTowerPlayEndResponse()

        user_id = req_data.user_id
        trial_tower_id = req_data.trial_tower_id
        play_end = req_data.play_end_request_data[0]
        base_get_data = play_end.base_get_data[0]
        score_data = play_end.score_data[0]
        exp = 0
        cleared_mission_ct = 0
        highest_mission_diff_cleared = 0
        num_monsters_defeated = 0
        monsters_defeated_data = {}
        json_data = {"data": []}
        
        ep_data = await self.data.static.get_tower_by_id(trial_tower_id)
        quest_scene = await self.data.static.get_quest_by_id(int(ep_data['QuestSceneId']))
        reward_table = await self.data.static.get_rewards_by_subtable(int(quest_scene['RewardTableSubId']))
        ex_bonus_table = await self.data.static.get_ex_bonuses_by_subtable(int(ep_data['ExBonusTableSubId']))

        await self.data.profile.add_col(user_id, base_get_data.get_col)

        quest_clear_flag = score_data.clear_time > 0
        clear_time = score_data.clear_time
        combo_num = score_data.combo_num
        total_damage = score_data.total_damage
        concurrent_destroying_num = score_data.concurrent_destroying_num
        
        if quest_clear_flag is True:
            await self.data.profile.add_vp(user_id, quest_scene['SingleRewardVp'])
            await self.data.profile.add_exp(user_id, quest_scene['SuccessPlayerExp'])
            exp = await self.data.profile.get_exp(user_id)
        
        else:
            await self.data.profile.add_exp(user_id, quest_scene['FailedPlayerExp'])
            exp = await self.data.profile.get_exp(user_id)
        
        # Calculate level based off experience and the CSV list
        player_level_data = self.load_data_csv("PlayerRank")
            
        for i in range(0,len(player_level_data)):
            if exp>=int(player_level_data[i]["TotalExp"]) and exp<int(player_level_data[i+1]["TotalExp"]):
                await self.data.profile.set_level(user_id, int(player_level_data[i]["PlayerRankId"]))
                break
        current_data = await self.data.item.get_quest_log(user_id, ep_data['QuestSceneId'])
        if current_data:
            await self.data.item.put_player_quest(
                user_id, 
                int(QuestType.TRIAL_TOWER),
                ep_data['QuestSceneId'], 
                False if not quest_clear_flag and not current_data['quest_clear_flag'] else True, 
                min(clear_time, current_data['clear_time']) if quest_clear_flag else current_data['clear_time'], 
                max(combo_num, current_data['combo_num']), 
                max(int(total_damage), current_data['total_damage']), 
                max(concurrent_destroying_num, current_data['concurrent_destroying_num'])
            )
        else:
            await self.data.item.put_player_quest(
                user_id, 
                int(QuestType.TRIAL_TOWER),
                ep_data['QuestSceneId'], 
                quest_clear_flag, 
                clear_time, 
                combo_num, 
                total_damage, 
                concurrent_destroying_num
            )

        for mission in play_end.mission_data_list:
            if mission.clear_flag == 1:
                cleared_mission_ct += 1
                if mission.mission_difficulty_id > highest_mission_diff_cleared:
                    highest_mission_diff_cleared = mission.mission_difficulty_id

        for monster_data in play_end.discovery_enemy_data_list:
            num_monsters_defeated += monster_data.destroy_num
            monsters_defeated_data[monster_data.enemy_kind_id] = monster_data.destroy_num

        for bonus in ex_bonus_table:
            table_id = int(bonus['ExBonusTableId'])
            ach_thing = 0
            condition = int(bonus['ExBonusConditionId'])
            val1 = int(bonus['ConditionValue1'])
            val2 = int(bonus['ConditionValue2'])
            if condition == ExBonusCondition.CLEAR_UNDER_X_SECS:
                if quest_clear_flag and int(score_data.clear_time / 1000) < val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.DEFEAT_X_MONSTER_Y_TIMES:
                if monsters_defeated_data.get(val1, 0) >= val2:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.DEFEAT_X_MONSTERS:
                if num_monsters_defeated >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_X_MISSIONS:
                if cleared_mission_ct >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_MISSION_DIFFICULTY_X:
                if highest_mission_diff_cleared >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.COLLECT_X_LOGS:
                if len(play_end.get_unanalyzed_log_tmp_reward_data_list) >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.CLEAR_SKILL_LEVEL_X:
                if score_data.reaching_skill_level >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.NO_LOSSES:
                if score_data.total_loss_num == 0:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.ACCEL_X_TIMES:
                if score_data.acceleration_invocation_num >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.MAX_COMBO_X:
                if score_data.combo_num >= val1:
                    await self.add_reward(bonus._asdict(), user_id)
                    await self.data.item.put_ex_bonus(user_id, int(ep_data['QuestSceneId']), table_id, True)
                    ach_thing = 2
            elif condition == ExBonusCondition.MULTIPLAYER_CLEAR_X:
                # TODO
                pass
            else:
                self.logger.warning(f"Unhandled EX Bonus condition {condition}")
            
            resp.play_end_response_data[0].ex_bonus_data_list.append(QuestScenePlayEndExBonusData.from_args(table_id, ach_thing))

        self.logger.info(f"User {user_id} {'cleared' if quest_clear_flag else 'ended'} trial tower {trial_tower_id}")

        for rare_drop in play_end.get_rare_drop_data_list:
            rewardList = self.load_data_csv("QuestRareDrop")
            for drop in rewardList:
                if int(drop['QuestRareDropId']) == rare_drop.quest_rare_drop_id:
                    await self.add_reward(drop, user_id)
                    break

        for unanalyzed_log in play_end.get_unanalyzed_log_tmp_reward_data_list:
            able_rewards: List[Row] = []
            for reward in reward_table:
                if int(reward['UnanalyzedLogGradeId']) == unanalyzed_log.unanalyzed_log_grade_id:
                    able_rewards.append(reward)
            randomized_unanalyzed_id = choice(able_rewards)
            
            await self.add_reward(randomized_unanalyzed_id._asdict(), user_id)
            json_data["data"].append(randomized_unanalyzed_id._asdict())
        
        
        trace_table = await self.data.static.get_player_trace_by_subid(quest_scene['PlayerTraceTableSubId'])
        
        for trace in play_end.get_player_trace_data_list:
            self.logger.info(f"User {user_id} obtained trace {trace.user_quest_scene_player_trace_id}")
            resp.play_end_response_data[0].play_end_player_trace_reward_data_list.append(QuestScenePlayEndPlayerTraceRewardData.from_args(choice(trace_table)._asdict()))

        await self.data.item.create_end_session(user_id, ep_data['QuestSceneId'], play_end.play_result_flag, json_data["data"])

        # Update heroes from the used party
        play_session = await self.data.item.get_session(user_id)
        session_party = await self.data.item.get_hero_party_by_id(play_session["user_party_team_id"])
        if session_party:
            hero_level_data = self.load_data_csv("HeroLogLevel")
            hero_list = []
            hero_list.append(session_party["user_hero_log_id_1"])
            hero_list.append(session_party["user_hero_log_id_2"])
            hero_list.append(session_party["user_hero_log_id_3"])

            for i in range(0,3):
                self.logger.info(f"Give hero {hero_list[i]} {base_get_data.get_hero_log_exp}")
                await self.data.item.add_hero_xp(hero_list[i], base_get_data.get_hero_log_exp)
                log_exp = await self.data.item.get_hero_xp(hero_list[i])

                # Calculate hero level based off experience and the CSV list
                if log_exp:
                    for e in range(0,len(hero_level_data)):
                        if log_exp>=int(hero_level_data[e]["TotalExp"]) and log_exp<int(hero_level_data[e+1]["TotalExp"]):
                            self.logger.info(f"Set hero {hero_list[i]} level {hero_level_data[e]['HeroLogLevelId']} ({log_exp} total XP)")
                            await self.data.item.set_hero_level(hero_list[i], hero_level_data[e]['HeroLogLevelId'])
                            break
        else:
            self.logger.error(f"Failed to get session party {play_session['user_party_team_id']} data for user {user_id}!")

        return resp.make()

    async def handle_c91a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes: # handler is identical to the episode
        #quest/trial_tower_play_end_unanalyzed_log_fixed
        req = SaoTrialTowerPlayEndUnanalyzedLogFixedRequest(header, request)
        resp = SaoTrialTowerPlayEndUnanalyzedLogFixedResponse()
        
        end_session_data = await self.data.item.get_end_session(req.user_id)
        for data in end_session_data['reward_data']:
            resp.play_end_unanalyzed_log_reward_data_list.append(QuestScenePlayEndUnanalyzedLogRewardData.from_args(data['UnanalyzedLogGradeId'], data))

        return resp.make()

    async def handle_c930(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # quest/get_chat_side_story_user_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetChatSideStoryUserDataListResponse()

        return resp.make()

    async def handle_ca02(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #quest_multi_play_room/get_quest_scene_multi_play_photon_server
        resp = SaoGetQuestSceneMultiPlayPhotonServerResponse(self.game_cfg.server.photon_app_id)
        return resp.make()

    async def handle_cb02(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # quest_ranking/get_quest_hierarchy_progress_degrees_ranking_list
        req = SaoGetQuestHierarchyProgressDegreesRankingListRequest(header, request)
        return SaoGetQuestHierarchyProgressDegreesRankingListResponse(GameconnectCmd.GET_QUEST_HIERARCHY_PROGRESS_DEGREES_RANKING_LIST_RESPONSE).make()

    async def handle_cb04(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # quest_ranking/get_quest_popular_hero_log_ranking_list
        req = SaoGetQuestPopularHeroLogRankingListRequest(header, request)
        return SaoGetQuestPopularHeroLogRankingListResponse(GameconnectCmd.GET_QUEST_POPULAR_HERO_LOG_RANKING_LIST_RESPONSE).make()

    async def handle_cd00(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #defrag_match/get_defrag_match_basic_data
        resp = SaoGetDefragMatchBasicDataResponse()
        data = DefragMatchBasicUserData.from_args()
        return resp.make()

    async def handle_cd02(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #defrag_match/get_defrag_match_ranking_user_data
        # TODO: League points
        req = SaoGetDefragMatchRankingUserDataRequest(header, request)
        profile = await self.data.profile.get_profile(req.user_id)
        resp = SaoGetDefragMatchRankingUserDataResponse(profile._asdict())
        return resp.make()

    async def handle_cd04(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #defrag_match/get_defrag_match_league_point_ranking_list
        resp = SaoGetDefragMatchLeaguePointRankingListResponse()
        return resp.make()

    async def handle_cd06(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        #defrag_match/get_defrag_match_league_score_ranking_list
        resp = SaoGetDefragMatchLeagueScoreRankingListResponse()
        return resp.make()

    async def handle_cf0e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # gasha/get_gasha_medal_shop_user_data_list
        # TODO: Get user shop data
        req = GetGashaMedalShopUserDataListRequest(header, request)
        resp = GetGashaMedalShopUserDataListResponse(GameconnectCmd.GET_GASHA_MEDAL_SHOP_USER_DATA_LIST_RESPONSE)
        return resp.make()

    async def handle_d000(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetAdventureExecUserDataResponse()
        return resp.make()

    async def handle_d100(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # shop/get_yui_medal_shop_user_data_list
        # TODO: Get user shop data
        req = GetYuiMedalShopUserDataListRequest(header, request)
        resp = GetYuiMedalShopUserDataListResponse(GameconnectCmd.GET_YUI_MEDAL_SHOP_USER_DATA_LIST_RESPONSE)
        return resp.make()

    async def handle_d200(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # mission/get_beginner_mission_user_data
        req = SaoGetBeginnerMissionUserDataRequest(header, request)
        resp = SaoGetBeginnerMissionUserDataResponse()
        profile = await self.data.profile.get_profile(req.user_id)
        if profile:
            if profile['ad_confirm_date']:
                resp.data[0].ad_confirm_date = profile['ad_confirm_date']
                resp.data[0].ad_confirm_flag = 1

        return resp.make()

    async def handle_d202(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # mission/get_beginner_mission_progresses_user_data_list
        req = SaoGetBeginnerMissionProgressesUserDataListRequest(header, request)
        resp = SaoGetBeginnerMissionProgressesUserDataListResponse()

        return resp.make()

    async def handle_d204(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # mission/get_beginner_mission_seat_progresses_user_data_list
        req = SaoGetBeginnerMissionSeatProgressesUserDataListRequest(header, request)
        resp = SaoGetBeginnerMissionSeatProgressesUserDataListResponse()

        return resp.make()

    async def handle_d206(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # mission/beginner_mission_ad_confirm_notification
        req = SaoBeginnerMissionAdConfirmNotificationRequest(header, request)
        self.logger.info(f"User {req.user_id} confirmed ad for beginner mission {req.beginner_mission_id}")
        await self.data.profile.update_beginner_mission_date(req.user_id)

        return SaoNoopResponse(GameconnectCmd.BEGINNER_MISSION_AD_CONFIRM_NOTIFICATION_RESPONSE).make()

    async def handle_d312(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # campaign/get_linked_site_reg_campaign_user_data
        req = SaoGetLinkedSiteRegCampaignUserDataRequest(header, request)
        resp = SaoGetLinkedSiteRegCampaignUserDataResponse()

        return resp.make()

    async def handle_d400(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # other/get_hero_log_unit_user_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetHeroLogUnitUserDataListResponse()

        return resp.make()

    async def handle_d402(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # other/get_chara_unit_user_data_list
        req = SaoGenericUserRequest(header, request)
        resp = SaoGetCharaUnitUserDataListResponse()

        return resp.make()

    async def handle_d404(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # other/bnid_serial_code_check
        req = SaoBnidSerialCodeCheckRequest()
        resp = SaoBnidSerialCodeCheckResponse()
        return resp.make()

    async def handle_d404(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # other/bnid_serial_code_entry_by_appendix_card
        req = SaoBnidSerialCodeEntryByAppendixCardRequest()
        resp = SaoBnidSerialCodeEntryByAppendixCardResponse()
        return resp.make()

    async def handle_d500(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_player_ranks
        tbl = self.load_data_csv('PlayerRank')
        resp = SaoGetMPlayerRanksResponse(tbl)
        return resp.make()

    async def handle_d502(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_titles
        tbl = self.load_data_csv('Title')
        resp = SaoGetMTitlesResponse(tbl)
        return resp.make()

    async def handle_d504(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_fragments
        tbl = self.load_data_csv('Fragment')
        resp = SaoGetMFragmentsResponse(tbl)
        return resp.make()

    async def handle_d506(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_reward_tables
        tbl = self.load_data_csv('RewardTable')
        resp = SaoGetMRewardTablesResponse(tbl)
        return resp.make()

    async def handle_d508(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_reward_sets
        tbl = self.load_data_csv('RewardSet')
        resp = SaoGetMRewardSetsResponse(tbl)
        return resp.make()

    async def handle_d50a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_unanalyzed_log_grades
        tbl = self.load_data_csv('UnanalyzedLogGrade')
        resp = SaoGetMUnanalyzedLogGradesResponse(tbl)
        return resp.make()

    async def handle_d50c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_appoint_leader_params
        tbl = self.load_data_csv('AppointLeaderParam')
        resp = SaoGetMAppointLeaderParamsResponse(tbl)
        return resp.make()

    async def handle_d50e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_appoint_leader_effects
        tbl = self.load_data_csv('AppointLeaderEffect')
        resp = SaoGetMAppointLeaderEffectsResponse(tbl)
        return resp.make()

    async def handle_d510(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_appoint_leader_effect_types
        tbl = self.load_data_csv('AppointLeaderEffectType')
        resp = SaoGetMAppointLeaderEffectTypesResponse(tbl)
        return resp.make()

    async def handle_d512(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_rarities
        tbl = self.load_data_csv('Rarity')
        resp = SaoGetMRaritiesResponse(tbl)
        return resp.make()

    async def handle_d514(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_composition_events
        tbl = self.load_data_csv('CompositionEvent')
        resp = SaoGetMCompositionEventsResponse(tbl)
        return resp.make()

    async def handle_d516(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_composition_params
        tbl = self.load_data_csv('CompositionParam')
        resp = SaoGetMCompositionParamsResponse(tbl)
        return resp.make()

    async def handle_d518(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_game_play_prices
        tbl = self.load_data_csv('GamePlayPrice')
        resp = SaoGetMGamePlayPricesResponse(tbl)
        return resp.make()

    async def handle_d51a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_buy_tickets
        tbl = self.load_data_csv('BuyTicket')
        resp = SaoGetMBuyTicketsResponse(tbl)
        return resp.make()

    async def handle_d51c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_tips
        tbl = self.load_data_csv('Tips')
        resp = SaoGetMTipsResponse(tbl)
        return resp.make()

    async def handle_d51e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_caps
        tbl = self.load_data_csv('Cap')
        resp = SaoGetMCapsResponse(tbl)
        return resp.make()

    async def handle_d520(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_hero_log
        tbl = self.load_data_csv('HeroLog')
        resp = SaoGetMHeroLogResponse(tbl)
        return resp.make()

    async def handle_d522(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_hero_log_levels
        tbl = self.load_data_csv('HeroLogLevel')
        resp = SaoGetMHeroLogLevelsResponse(tbl)
        return resp.make()

    async def handle_d524(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_hero_log_roles
        tbl = self.load_data_csv('HeroLogRole')
        resp = SaoGetMHeroLogRolesResponse(tbl)
        return resp.make()

    async def handle_d526(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_hero_log_trust_ranks
        tbl = self.load_data_csv('HeroLogTrustRank')
        resp = SaoGetMHeroLogTrustRanksResponse(tbl)
        return resp.make()

    async def handle_d528(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_charas
        tbl = self.load_data_csv('Chara')
        resp = SaoGetMCharasResponse(tbl)
        return resp.make()

    async def handle_d52a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_chara_friendly_ranks
        tbl = self.load_data_csv('CharaFriendlyRank')
        resp = SaoGetMCharaFriendlyRanksResponse(tbl)
        return resp.make()

    async def handle_d52c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_equipments
        tbl = self.load_data_csv('Equipment')
        resp = SaoGetMEquipmentsResponse(tbl)
        return resp.make()

    async def handle_d52e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_equipment_levels
        tbl = self.load_data_csv('EquipmentLevel')
        resp = SaoGetMEquipmentLevelsResponse(tbl)
        return resp.make()

    async def handle_d530(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_weapon_types
        tbl = self.load_data_csv('WeaponType')
        resp = SaoGetMWeaponTypesResponse(tbl)
        return resp.make()

    async def handle_d532(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_items
        tbl = self.load_data_csv('Item')
        resp = SaoGetMItemsResponse(tbl)
        return resp.make()

    async def handle_d534(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_item_types
        tbl = self.load_data_csv('ItemType')
        resp = SaoGetMItemTypesResponse(tbl)
        return resp.make()

    async def handle_d536(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_buff_items
        tbl = self.load_data_csv('BuffItem')
        resp = SaoGetMBuffItemsResponse(tbl)
        return resp.make()

    async def handle_d538(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_enemies
        tbl = self.load_data_csv('Enemy')
        resp = SaoGetMEnemiesResponse(tbl)
        return resp.make()

    async def handle_d53a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_enemy_sets
        tbl = self.load_data_csv('EnemySet')
        resp = SaoGetMEnemySetsResponse(tbl)
        return resp.make()

    async def handle_d53c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_enemy_kinds
        tbl = self.load_data_csv('EnemyKind')
        resp = SaoGetMEnemyKindsResponse(tbl)
        return resp.make()

    async def handle_d53e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_enemy_categories
        tbl = self.load_data_csv('EnemyCategory')
        resp = SaoGetMEnemyCategoriesResponse(tbl)
        return resp.make()

    async def handle_d540(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_units
        tbl = self.load_data_csv('Unit')
        resp = SaoGetMUnitsResponse(tbl)
        return resp.make()

    async def handle_d542(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_unit_gimmicks
        tbl = self.load_data_csv('UnitGimmick')
        resp = SaoGetMUnitGimmicksResponse(tbl)
        return resp.make()

    async def handle_d544(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_unit_collisions
        tbl = self.load_data_csv('UnitCollision')
        resp = SaoGetMUnitCollisionsResponse(tbl)
        return resp.make()

    async def handle_d546(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_unit_powers
        tbl = self.load_data_csv('UnitPower')
        resp = SaoGetMUnitPowersResponse(tbl)
        return resp.make()

    async def handle_d548(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gimmick_attacks
        tbl = self.load_data_csv('GimmickAttack')
        resp = SaoGetMGimmickAttacksResponse(tbl)
        return resp.make()

    async def handle_d54a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_chara_attacks
        tbl = self.load_data_csv('CharaAttack')
        resp = SaoGetMCharaAttacksResponse(tbl)
        return resp.make()

    async def handle_d54c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_boss_attacks
        tbl = self.load_data_csv('BossAttack')
        resp = SaoGetMBossAttacksResponse(tbl)
        return resp.make()

    async def handle_d54e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_monster_attacks
        tbl = self.load_data_csv('MonsterAttack')
        resp = SaoGetMMonsterAttacksResponse(tbl)
        return resp.make()

    async def handle_d550(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_monster_actions
        tbl = self.load_data_csv('MonsterAction')
        resp = SaoGetMMonsterActionsResponse(tbl)
        return resp.make()

    async def handle_d552(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_properties
        tbl = self.load_data_csv('Property')
        resp = SaoGetMPropertiesResponse(tbl)
        return resp.make()

    async def handle_d554(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_property_tables
        tbl = self.load_data_csv('PropertyTable')
        resp = SaoGetMPropertyTablesResponse(tbl)
        return resp.make()

    async def handle_d556(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_property_types
        tbl = self.load_data_csv('PropertyType')
        resp = SaoGetMPropertyTypesResponse(tbl)
        return resp.make()

    async def handle_d558(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_skills
        tbl = self.load_data_csv('Skill')
        resp = SaoGetMSkillsResponse(tbl)
        return resp.make()

    async def handle_d55a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_skill_tables
        tbl = self.load_data_csv('SkillTable')
        resp = SaoGetMSkillTablesResponse(tbl)
        return resp.make()

    async def handle_d55c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_skill_levels
        tbl = self.load_data_csv('SkillLevel')
        resp = SaoGetMSkillLevelsResponse(tbl)
        return resp.make()

    async def handle_d55e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_awakenings
        tbl = self.load_data_csv('Awakening')
        resp = SaoGetMAwakeningsResponse(tbl)
        return resp.make()

    async def handle_d560(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_synchro_skills
        tbl = self.load_data_csv('SynchroSkill')
        resp = SaoGetMSynchroSkillsResponse(tbl)
        return resp.make()

    async def handle_d562(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_sound_skill_cut_in_voices
        tbl = self.load_data_csv('Sound_SkillCutInVoice')
        resp = SaoGetMSoundSkillCutInVoicesResponse(tbl)
        return resp.make()

    async def handle_d564(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_scenes
        tbl = self.load_data_csv('QuestScene')
        resp = SaoGetMQuestScenesResponse(tbl)
        return resp.make()

    async def handle_d566(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_exist_units
        tbl = self.load_data_csv('QuestExistUnit')
        resp = SaoGetMQuestExistUnitsResponse(tbl)
        return resp.make()

    async def handle_d568(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_episode_append_rewards
        tbl = self.load_data_csv('QuestEpisodeAppendRewards')
        resp = SaoGetMQuestEpisodeAppendRewardsResponse(tbl)
        return resp.make()

    async def handle_d56a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_side_quests
        tbl = self.load_data_csv('SideQuest')
        resp = SaoGetMSideQuestsResponse(tbl)
        return resp.make()

    async def handle_d56c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_episodes
        tbl = self.load_data_csv('Episode')
        resp = SaoGetMEpisodesResponse(tbl)
        return resp.make()

    async def handle_d56e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_episode_chapters
        tbl = self.load_data_csv('EpisodeChapter')
        resp = SaoGetMEpisodeChaptersResponse(tbl)
        return resp.make()

    async def handle_d570(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_episode_parts
        tbl = self.load_data_csv('EpisodePart')
        resp = SaoGetMEpisodePartsResponse(tbl)
        return resp.make()

    async def handle_d572(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_trial_towers
        tbl = self.load_data_csv('TrialTower')
        resp = SaoGetMTrialTowersResponse(tbl)
        return resp.make()

    async def handle_d574(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_ex_towers
        req = SaoGetMExTowersRequest(header, request)
        tbl = self.load_data_csv('ExTowers')
        resp = SaoGetMExTowersResponse(tbl)
        return resp.make()

    async def handle_d576(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_ex_tower_quests
        req = SaoGetMExTowerQuestsRequest(header, request)
        tbl = self.load_data_csv('ExTowerQuests')
        resp = SaoGetMExTowerQuestsResponse(tbl)
        return resp.make()

    async def handle_d578(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_menu_display_enemies
        tbl = self.load_data_csv('MenuDisplayEnemy')
        resp = SaoGetMMenuDisplayEnemiesResponse(tbl)
        return resp.make()

    async def handle_d57a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_missions
        tbl = self.load_data_csv('Mission')
        resp = SaoGetMMissionsResponse(tbl)
        return resp.make()

    async def handle_d57c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_mission_tables
        tbl = self.load_data_csv('MissionTable')
        resp = SaoGetMMissionTablesResponse(tbl)
        return resp.make()

    async def handle_d57e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_mission_difficulties
        tbl = self.load_data_csv('MissionDifficulty')
        resp = SaoGetMMissionDifficultiesResponse(tbl)
        return resp.make()

    async def handle_d580(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_battle_cameras
        tbl = self.load_data_csv('BattleCamera')
        resp = SaoGetMBattleCamerasResponse(tbl)
        return resp.make()

    async def handle_d582(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_chat_main_stories
        tbl = self.load_data_csv('ChatMainStory')
        resp = SaoGetMChatMainStoriesResponse(tbl)
        return resp.make()

    async def handle_d584(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_chat_side_stories
        tbl = self.load_data_csv('ChatSideStory')
        resp = SaoGetMChatSideStoriesResponse(tbl)
        return resp.make()

    async def handle_d586(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_chat_event_stories
        req = SaoGetMChatEventStoriesRequest(header, request)
        tbl = self.load_data_csv('ChatEventStory')
        resp = SaoGetMChatEventStoriesResponse(tbl)
        return resp.make()

    async def handle_d588(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_navigator_charas
        tbl = self.load_data_csv('NavigatorChara')
        resp = SaoGetMNavigatorCharasResponse(tbl)
        return resp.make()

    async def handle_d58a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_navigator_comments
        tbl = self.load_data_csv('NavigatorComment')
        resp = SaoGetMNavigatorCommentsResponse(tbl)
        return resp.make()

    async def handle_d58c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_ex_bonus_tables
        tbl = self.load_data_csv('ExBonusTable')
        resp = SaoGetMExBonusTablesResponse(tbl)
        return resp.make()

    async def handle_d58e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_ex_bonus_conditions
        tbl = self.load_data_csv('ExBonusCondition')
        resp = SaoGetMExBonusConditionsResponse(tbl)
        return resp.make()

    async def handle_d590(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_rare_drops
        tbl = self.load_data_csv('QuestRareDrop')
        resp = SaoGetMQuestRareDropsResponse(tbl)
        return resp.make()

    async def handle_d592(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_special_rare_drop_settings
        tbl = self.load_data_csv('QuestSpecialRareDropSettings')
        resp = SaoGetMQuestSpecialRareDropSettingsResponse(tbl)
        return resp.make()

    async def handle_d594(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_special_rare_drops
        tbl = self.load_data_csv('QuestSpecialRareDrops')
        resp = SaoGetMQuestSpecialRareDropsResponse(tbl)
        return resp.make()

    async def handle_d596(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_tutorials
        tbl = self.load_data_csv('QuestTutorial')
        resp = SaoGetMQuestTutorialsResponse(tbl)
        return resp.make()

    async def handle_d598(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_player_trace_tables
        tbl = self.load_data_csv('PlayerTraceTable')
        resp = SaoGetMQuestPlayerTraceTablesResponse(tbl)
        return resp.make()

    async def handle_d59a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_stills
        tbl = self.load_data_csv('QuestStill')
        resp = SaoGetMQuestStillsResponse(tbl)
        return resp.make()

    async def handle_d59c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gashas
        tbl = self.load_data_csv('Gasha')
        resp = SaoGetMGashasResponse(tbl)
        return resp.make()

    async def handle_d59e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_headers
        tbl = self.load_data_csv('GashaHeader')
        resp = SaoGetMGashaHeadersResponse(tbl)
        return resp.make()

    async def handle_d5a0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_lottery_rarities
        tbl = self.load_data_csv('GashaLotteryRarity')
        resp = SaoGetMGashaLotteryRaritiesResponse(tbl)
        return resp.make()

    async def handle_d5a2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_prizes
        tbl = self.load_data_csv('GashaPrize')
        resp = SaoGetMGashaPrizesResponse(tbl)
        return resp.make()

    async def handle_d5a4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_comeback_events
        tbl = self.load_data_csv('ComebackEvent')
        resp = SaoGetMComebackEventsResponse(tbl)
        return resp.make()

    async def handle_d5a6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_ad_banners
        tbl = self.load_data_csv('AdBanners')
        resp = SaoGetMAdBannersResponse(tbl)
        return resp.make()

    async def handle_d5a8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_events
        tbl = self.load_data_csv('Event')
        resp = SaoGetMEventsResponse(tbl)
        return resp.make()

    async def handle_d5aa(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunts
        req = SaoGetMTreasureHuntsRequest(header, request)
        tbl = self.load_data_csv('TreasureHunt')
        resp = SaoGetMTreasureHuntsResponse(tbl)
        return resp.make()

    async def handle_d5ac(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_whole_tasks
        req = SaoGetMTreasureHuntWholeTasksRequest(header, request)
        tbl = self.load_data_csv('TreasureHuntWholeTask')
        resp = SaoGetMTreasureHuntWholeTasksResponse(tbl)
        return resp.make()

    async def handle_d5ae(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_individual_tasks
        req = SaoGetMTreasureHuntIndividualTasksRequest(header, request)
        tbl = self.load_data_csv('TreasureHuntIndividualTask')
        resp = SaoGetMTreasureHuntIndividualTasksResponse(tbl)
        return resp.make()

    async def handle_d5b0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_special_effects
        req = SaoGetMTreasureHuntSpecialEffectsRequest(header, request)
        tbl = self.load_data_csv('TreasureHuntSpecialEffect')
        resp = SaoGetMTreasureHuntSpecialEffectsResponse(tbl)
        return resp.make()

    async def handle_d5b2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_event_point_reward_common_rewards
        req = SaoGetMTreasureHuntEventPointRewardCommonRewardsRequest(header, request)
        tbl = self.load_data_csv('TreasureHuntEventPointRewardCommonReward')
        resp = SaoGetMTreasureHuntEventPointRewardCommonRewardsResponse(tbl)
        return resp.make()

    async def handle_d5b4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_event_point_reward_titles
        req = SaoGetMTreasureHuntEventPointRewardTitlesRequest(header, request)
        tbl = self.load_data_csv('TreasureHuntEventPointRewardTitle')
        resp = SaoGetMTreasureHuntEventPointRewardTitlesResponse(tbl)
        return resp.make()

    async def handle_d5b6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_treasure_hunt_task_texts
        tbl = self.load_data_csv('TreasureHuntTaskText')
        resp = SaoGetMTreasureHuntTaskTextsResponse(tbl)
        return resp.make()

    async def handle_d5b8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_bnid_serial_codes
        tbl = self.load_data_csv('BnidSerialCodes')
        resp = SaoGetMBnidSerialCodesResponse(tbl)
        return resp.make()

    async def handle_d5ba(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_bnid_serial_code_rewards
        tbl = self.load_data_csv('BnidSerialCodeRewards')
        resp = SaoGetMBnidSerialCodeRewardsResponse(tbl)
        return resp.make()

    async def handle_d5bc(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_support_log
        tbl = self.load_data_csv('SupportLog')
        resp = SaoGetMSupportLogResponse(tbl)
        return resp.make()

    async def handle_d5be(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_support_log_types
        tbl = self.load_data_csv('SupportLogType')
        resp = SaoGetMSupportLogTypesResponse(tbl)
        return resp.make()

    async def handle_d5c0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_episode_appends
        tbl = self.load_data_csv('EpisodeAppends')
        resp = SaoGetMEpisodeAppendsResponse(tbl)
        return resp.make()

    async def handle_d5c2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_defrag_match_quests
        tbl = self.load_data_csv('DefragMatchQuest')
        resp = SaoGetMQuestDefragMatchQuestsResponse(tbl)
        return resp.make()

    async def handle_d5c4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_quest_defrag_match_quest_boss_tables
        tbl = self.load_data_csv('DefragMatchBossTable')
        resp = SaoGetMQuestDefragMatchQuestBossTablesResponse(tbl)
        return resp.make()

    async def handle_d5c6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_matches
        req = SaoGetMDefragMatchesRequest(header, request)
        tbl = self.load_data_csv('DefragMatchs')
        resp = SaoGetMDefragMatchesResponse(tbl)
        return resp.make()

    async def handle_d5c8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_seed
        req = SaoGetMDefragMatchSeedRequest(header, request)
        tbl = self.load_data_csv('DefragMatchSeed')
        resp = SaoGetMDefragMatchSeedResponse(tbl)
        return resp.make()

    async def handle_d5ca(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_special_effects
        req = SaoGetMDefragMatchSpecialEffectsRequest(header, request)
        tbl = self.load_data_csv('DefragMatchSpecialEffects')
        resp = SaoGetMDefragMatchSpecialEffectsResponse(tbl)
        return resp.make()

    async def handle_d5cc(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_grades
        req = SaoGetMDefragMatchGradesRequest(header, request)
        tbl = self.load_data_csv('DefragMatchGrade')
        resp = SaoGetMDefragMatchGradesResponse(tbl)
        return resp.make()

    async def handle_d5ce(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_cpu_units
        tbl = self.load_data_csv('DefragMatchCpuUnits')
        resp = SaoGetMDefragMatchCpuUnitsResponse(tbl)
        return resp.make()

    async def handle_d5d0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_cpu_support_logs
        tbl = self.load_data_csv('DefragMatchCpuSupportLogs')
        resp = SaoGetMDefragMatchCpuSupportLogsResponse(tbl)
        return resp.make()

    async def handle_d5d2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_period_bonuses
        req = SaoGetMDefragMatchPeriodBonusesRequest(header, request)
        tbl = self.load_data_csv('DefragMatchPeriodBonuses')
        resp = SaoGetMDefragMatchPeriodBonusesResponse(tbl)
        return resp.make()

    async def handle_d5d4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_random_bonus_tables
        req = SaoGetMDefragMatchRandomBonusTablesRequest(header, request)
        tbl = self.load_data_csv('DefragMatchRandomBonusTables')
        resp = SaoGetMDefragMatchRandomBonusTablesResponse(tbl)
        return resp.make()

    async def handle_d5d6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_random_bonus_conditions
        tbl = self.load_data_csv('DefragMatchRandomBonusConditions')
        resp = SaoGetMDefragMatchRandomBonusConditionsResponse(tbl)
        return resp.make()

    async def handle_d5d8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_defrag_match_rare_drops
        req = SaoGetMDefragMatchRareDropsRequest(header, request)
        tbl = self.load_data_csv('DefragMatchRareDrops')
        resp = SaoGetMDefragMatchRareDropsResponse(tbl)
        return resp.make()

    async def handle_d5da(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_yui_medal_shops
        tbl = self.load_data_csv('YuiMedalShops')
        resp = SaoGetMYuiMedalShopsResponse(tbl)
        return resp.make()

    async def handle_d5dc(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_yui_medal_shop_items
        tbl = self.load_data_csv('YuiMedalShopItems')
        resp = SaoGetMYuiMedalShopItemsResponse(tbl)
        return resp.make()

    async def handle_d5de(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_event_scenes
        req = SaoGetMEventScenesRequest(header, request)
        tbl = self.load_data_csv('EventScenes')
        resp = SaoGetMEventScenesResponse(tbl)
        return resp.make()

    async def handle_d5e0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_generic_campaign_periods
        tbl = self.load_data_csv('GenericCampaignPeriods')
        resp = SaoGetMGenericCampaignPeriodsResponse(tbl)
        return resp.make()

    async def handle_d5e2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_beginner_missions
        tbl = self.load_data_csv('BeginnerMissions')
        resp = SaoGetMBeginnerMissionsResponse(tbl)
        return resp.make()

    async def handle_d5e4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_beginner_mission_conditions
        req = SaoGetMBeginnerMissionConditionsRequest(header, request)
        tbl = self.load_data_csv('BeginnerMissionConditions')
        resp = SaoGetMBeginnerMissionConditionsResponse(tbl)
        return resp.make()

    async def handle_d5e6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_beginner_mission_rewards
        req = SaoGetMBeginnerMissionRewardsRequest(header, request)
        tbl = self.load_data_csv('BeginnerMissionRewards')
        resp = SaoGetMBeginnerMissionRewardsResponse(tbl)
        return resp.make()

    async def handle_d5e8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_beginner_mission_seat_conditions
        req = SaoGetMBeginnerMissionSeatConditionsRequest(header, request)
        tbl = self.load_data_csv('BeginnerMissionSeatConditions')
        resp = SaoGetMBeginnerMissionSeatConditionsResponse(tbl)
        return resp.make()

    async def handle_d5ea(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_beginner_mission_seat_rewards
        req = SaoGetMBeginnerMissionSeatRewardsRequest(header, request)
        tbl = self.load_data_csv('BeginnerMissionSeatRewards')
        resp = SaoGetMBeginnerMissionSeatRewardsResponse(tbl)
        return resp.make()

    async def handle_d5ec(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_event_items
        tbl = self.load_data_csv('EventItems')
        resp = SaoGetMEventItemsResponse(tbl)
        return resp.make()

    async def handle_d5ee(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_event_monsters
        req = SaoGetMEventMonstersRequest(header, request)
        tbl = self.load_data_csv('EventMonsters')
        resp = SaoGetMEventMonstersResponse(tbl)
        return resp.make()

    async def handle_d5f0(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_yui_medal_bonuses
        tbl = self.load_data_csv('YuiMedalBonus')
        resp = SaoGetMYuiMedalBonusesResponse(tbl)
        return resp.make()

    async def handle_d5f2(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_yui_medal_bonus_conditions
        tbl = self.load_data_csv('YuiMedalBonusCondition')
        resp = SaoGetMYuiMedalBonusConditionsResponse(tbl)
        return resp.make()

    async def handle_d5f4(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medals
        tbl = self.load_data_csv('GashaMedals')
        resp = SaoGetMGashaMedalsResponse(tbl)
        return resp.make()

    async def handle_d5f6(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medal_types
        tbl = self.load_data_csv('GashaMedalTypes')
        resp = SaoGetMGashaMedalTypesResponse(tbl)
        return resp.make()

    async def handle_d5f8(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medal_settings
        req = SaoGetMGashaMedalSettingsRequest(header, request)
        tbl = self.load_data_csv('GashaMedalSettings')
        resp = SaoGetMGashaMedalSettingsResponse(tbl)
        return resp.make()

    async def handle_d5fa(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medal_bonuses
        tbl = self.load_data_csv('GashaMedalBonuses')
        resp = SaoGetMGashaMedalBonusesResponse(tbl)
        return resp.make()

    async def handle_d5fc(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medal_shops
        tbl = self.load_data_csv('GashaMedalShops')
        resp = SaoGetMGashaMedalShopsResponse(tbl)
        return resp.make()

    async def handle_d5fe(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data/get_m_gasha_medal_shop_items
        req = SaoGetMGashaMedalShopItemsRequest(header, request)
        tbl = self.load_data_csv('GashaMedalShopItems')
        resp = SaoGetMGashaMedalShopItemsResponse(tbl)
        return resp.make()

    async def handle_d600(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mres_earn_campaign_applications
        tbl = self.load_data_csv('ResEarnCampaignApplications')
        resp = SaoGetMResEarnCampaignApplicationsResponse(tbl)
        return resp.make()

    async def handle_d602(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mres_earn_campaign_application_products
        req = SaoGetMResEarnCampaignApplicationProductsRequest(header, request)
        tbl = self.load_data_csv('ResEarnCampaignApplicationProducts')
        resp = SaoGetMResEarnCampaignApplicationProductsResponse(tbl)
        return resp.make()

    async def handle_d604(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mres_earn_campaign_shops
        tbl = self.load_data_csv('ResEarnCampaignShops')
        resp = SaoGetMResEarnCampaignShopsResponse(tbl)
        return resp.make()

    async def handle_d606(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mres_earn_campaign_shop_items
        req = SaoGetMResEarnCampaignShopItemsRequest(header, request)
        tbl = self.load_data_csv('ResEarnCampaignShopItems')
        resp = SaoGetMResEarnCampaignShopItemsResponse(tbl)
        return resp.make()

    async def handle_d608(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mpaying_yui_medal_bonuses
        tbl = self.load_data_csv('PayingYuiMedalBonuses')
        resp = SaoGetMPayingYuiMedalBonusesResponse(tbl)
        return resp.make()

    async def handle_d60a(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mac_login_bonuses
        tbl = self.load_data_csv('AcLoginBonuses')
        resp = SaoGetMAcLoginBonusesResponse(tbl)
        return resp.make()

    async def handle_d60c(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mplay_campaigns
        tbl = self.load_data_csv('PlayCampaigns')
        resp = SaoGetMPlayCampaignsResponse(tbl)
        return resp.make()

    async def handle_d60e(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mplay_campaign_rewards
        req = SaoGetMPlayCampaignRewardsRequest(header, request)
        tbl = self.load_data_csv('PlayCampaignRewards')
        resp = SaoGetMPlayCampaignRewardsResponse(tbl)
        return resp.make()

    async def handle_d610(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mgasha_free_campaigns
        tbl = self.load_data_csv('GashaFreeCampaigns')
        resp = SaoGetMGashaFreeCampaignsResponse(tbl)
        return resp.make()

    async def handle_d612(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mquest_drop_boost_campaigns
        tbl = self.load_data_csv('QuestDropBoostCampaigns')
        resp = SaoGetMQuestDropBoostCampaignsResponse(tbl)
        return resp.make()

    async def handle_d614(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mfirst_ticket_purchase_campaigns
        tbl = self.load_data_csv('FirstTicketPurchaseCampaigns')
        resp = SaoGetMFirstTicketPurchaseCampaignsResponse(tbl)
        return resp.make()

    async def handle_d616(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mlinked_site_reg_campaigns
        tbl = self.load_data_csv('LinkedSiteRegCampaigns')
        resp = SaoGetMLinkedSiteRegCampaignsResponse(tbl)
        return resp.make()

    async def handle_d618(self, header: SaoRequestHeader, request: bytes, src_ip: str) -> bytes:
        # master_data2/get_mlinked_site_reg_campaign_rewards
        req = SaoGetMLinkedSiteRegCampaignRewardsRequest(header, request)
        tbl = self.load_data_csv('LinkedSiteRegCampaignRewards')
        resp = SaoGetMLinkedSiteRegCampaignRewardsResponse(tbl)
        return resp.make()
