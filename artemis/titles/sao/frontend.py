import yaml
import jinja2
from typing import List
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route
from os import path
import random
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
from Crypto.Cipher import AES, _mode_cbc

from core.frontend import FE_Base, UserSession
from core.config import CoreConfig
from .database import SaoData
from .config import SaoConfig
from .const import SaoConstants


class SaoFrontend(FE_Base):
    SN_PREFIX = SaoConstants.SERIAL_IDENT
    NETID_PREFIX = SaoConstants.NETID_PREFIX
    ALL_HEROS = []
    def __init__(
        self, cfg: CoreConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.data = SaoData(cfg)
        self.game_cfg = SaoConfig()
        if path.exists(f"{cfg_dir}/{SaoConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{SaoConstants.CONFIG_NAME}"))
            )
        self.nav_name = "SAO"
        self.card_key= None
        self.card_iv = None
        
        if self.game_cfg.card.enable and self.game_cfg.card.crypt_password and self.game_cfg.card.crypt_salt:
            hash = PBKDF2(
                self.game_cfg.card.crypt_password,
                bytes.fromhex(self.game_cfg.card.crypt_salt),
                48,
                count=1000,
                hmac_hash_module=SHA1,
            )
            
            self.card_key = hash[:32]
            self.card_iv = hash[32:48]
    
    def get_routes(self) -> List[Route]:
        return [
            Route("/", self.render_GET, methods=['GET']),
            Route("/update.name", self.change_name, methods=['POST']),
            Route("/matching.auth", self.matching_auth, methods=['POST']),
            Route("/matching.auth/", self.matching_auth, methods=['POST']),
            Route("/qr.read", self.read_qr, methods=['POST']),
            Route("/qr.register", self.reg_qr, methods=['POST']),
            Route("/profile.register", self.reg_profile, methods=['POST'])
        ]

    async def render_GET(self, request: Request) -> Response:
        template = self.environment.get_template(
            "titles/sao/templates/sao_index.jinja"
        )
        pf = None
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        else:
            profile = await self.data.profile.get_profile(usr_sesh.user_id)
            if profile is not None:
                pf = profile._asdict()
            if not self.ALL_HEROS:
                self.ALL_HEROS = await self.data.static.get_heros()
 
        err = 0
        suc = 0
        if "e" in request.query_params:
            err = request.query_params.get("e", 0)
        if "s" in request.query_params:
            suc = request.query_params.get("s", 0)

        return Response(template.render(
            title=f"{self.core_config.server.name} | {self.nav_name}",
            game_list=self.environment.globals["game_list"],
            sesh=vars(usr_sesh),
            profile=pf,
            success=int(suc),
            error=int(err),
            all_heros=self.ALL_HEROS if self.ALL_HEROS else []
        ), media_type="text/html; charset=utf-8")
    
    async def change_name(self, request: Request) -> RedirectResponse:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/game/sao/", 303)
        
        frm = await request.form()
        new_name = frm.get("new_name")
        
        if len(new_name) > 16:
            return RedirectResponse("/game/sao/?e=8", 303)
        
        await self.data.profile.set_profile_name(usr_sesh.user_id, new_name)
        self.logger.info(f"User {usr_sesh.user_id} changed name to {new_name}")
        
        return RedirectResponse("/game/sao/?s=1", 303)

    async def matching_auth(self, request: Request) -> JSONResponse:
        self.logger.debug(f"Mathing auth params: {request.query_params}")
        self.logger.debug(f"Mathing auth headers: {request.headers}")
        uid = request.query_params.get('userId', '')
        
        if not uid:
            uid = f'Guest{str(random.randint(1,9999)).zfill(4)}'
            self.logger.info(f"Matching auth request with no userId, using {uid}")
        
        else:
            self.logger.info(f"Matching auth request for userId {uid}")
        
        return JSONResponse({ "ResultCode": 1, "UserId": uid }) # Just auth everything for now
    
    async def read_qr(self, request: Request) -> PlainTextResponse:
        if not self.card_key or not self.card_iv:
            return PlainTextResponse("e13-1", 400)
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return PlainTextResponse("e9", 403)
        
        frm = await request.form()
        qr_data = frm.get("qr_data", "")
        if not qr_data.isalnum() or not len(qr_data) == 0x40:
            return PlainTextResponse("e14-1", 400)
        
        try:
            cipher: _mode_cbc.CbcMode = AES.new(self.card_key, AES.MODE_CBC, iv=self.card_iv)
        except Exception as e:
            self.logger.error(f"Error creating card cipher - {e}")
            return PlainTextResponse("e13-2", 500)
        sn = b""
        try:
            sn = cipher.decrypt(bytes.fromhex(qr_data))[:19]
            sn = sn.decode()
        except Exception as e:
            self.logger.error(f"Error decrypting card data {qr_data} ({sn}) - {e}")
            return PlainTextResponse("e14-2", 400)
        
        if not sn.isnumeric():
            self.logger.error(f"Card serial {sn} decrypted incorrectly")
            return PlainTextResponse("e13-3", 400)
        
        return PlainTextResponse(sn)
    
    async def reg_qr(self, request: Request) -> RedirectResponse:
        if not self.card_key or not self.card_iv:
            return RedirectResponse("/game/sao/?e=14", 303)
        
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/game/sao/?e=9", 303)
        
        frm = await request.form()
        serial = frm.get("qr_register_serial")
        hero = frm.get("qr_register_hero")
        is_holo = bool(frm.get("qr_register_holo", False))

        user_hero = await self.data.item.get_hero_log(usr_sesh.user_id, hero)
        if not user_hero:
            hero_statc = await self.data.static.get_hero_by_id(hero)
            if not hero_statc:
                self.logger.error(f"Failed to find hero log {hero}! Please run the reader")
                return RedirectResponse(" /game/sao/?e=13", 303)
            
            skills = await self.data.static.get_skill_table_by_subid(hero_statc['SkillTableSubId'])
            if not skills:
                self.logger.error(f"Failed to find skill table {hero_statc['SkillTableSubId']}! Please run the reader")
                return RedirectResponse("/game/sao/?e=13", 303)

            default_skills = []
            now_have_skills = [None, None, None, None, None]
            x = 0
            for skill in skills:
                if skill['LevelObtained'] == 1 and skill['AwakeningId'] == 0:
                    default_skills[x] = skill['SkillId']
                    x += 1
                if x >= 5:
                    break
            
            for skill in default_skills:
                skill_info = await self.data.static.get_skill_by_id(skill)
                skill_slot = skill_info['Level'] - 1
                if now_have_skills[skill_slot] is not None:
                    now_have_skills[skill]


            user_hero_id = await self.data.item.put_hero_log(
                usr_sesh.user_id,
                hero,
                1,
                0,
                hero_statc['DefaultEquipmentId1'],
                hero_statc['DefaultEquipmentId2'], 
                now_have_skills[0],
                now_have_skills[1],
                now_have_skills[2],
                now_have_skills[3],
                now_have_skills[4]
            )
            if not user_hero_id:
                self.logger.error(f"Failed to give user {usr_sesh.user_id} hero {hero}!")
                return RedirectResponse("/game/sao/?e=99", 303)
        else:
            user_hero_id = user_hero['id']
        
        card_id = await self.data.profile.put_hero_card(usr_sesh.user_id, serial, user_hero_id, is_holo)
        if not card_id:
            self.logger.error(f"Failed to give user {usr_sesh.user_id} hero card {hero}!")
            return RedirectResponse("/game/sao/?e=99", 303)
        
        self.logger.info(f"User {usr_sesh.user_id} added hero {hero} as card with id {card_id}")

        return RedirectResponse("/game/sao/?s=1", 303)

    async def reg_profile(self, request: Request) -> RedirectResponse:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/game/sao/?e=9", 303)
        
        frm = await request.form()
        name = frm.get("sao_register_username")

        if len(name) > 16:
            return RedirectResponse("/game/sao/?e=8", 303)
        
        profile_id = await self.data.profile.create_profile(usr_sesh.user_id)
        if not profile_id:            
            self.logger.error(f"Failed to web register User {usr_sesh.user_id} with name {name}")
            return RedirectResponse("/game/sao/?e=99", 303)
        
        await self.data.profile.set_profile_name(usr_sesh.user_id, name)
        
        equip1 = await self.data.item.put_equipment(usr_sesh.user_id, 101000000)
        equip2 = await self.data.item.put_equipment(usr_sesh.user_id, 102000000)
        equip3 = await self.data.item.put_equipment(usr_sesh.user_id, 109000000)
        if not equip1 or not equip2 or not equip3:
            self.logger.error(f"Failed to create profile for user {usr_sesh.user_id} from (could not add equipment)")
            return RedirectResponse("/game/sao/?e=98", 303)
        
        hero1 = await self.data.item.put_hero_log(usr_sesh.user_id, 101000010, 1, 0, equip1, None, 1002, 1003, 1014, None, None)
        hero2 = await self.data.item.put_hero_log(usr_sesh.user_id, 102000010, 1, 0, equip2, None, 3001, 3002, 3004, None, None)
        hero3 = await self.data.item.put_hero_log(usr_sesh.user_id, 105000010, 1, 0, equip3, None, 10005, 10002, 10004, None, None)
        if not hero1 or not hero2 or not hero3:
            self.logger.error(f"Failed to create profile for user {usr_sesh.user_id} (could not add heros)")
            return RedirectResponse("/game/sao/?e=97", 303)
        
        await self.data.item.put_hero_party(usr_sesh.user_id, 0, hero1, hero2, hero3)
        self.logger.info(f"Web registered User {usr_sesh.user_id} profile {profile_id} with name {name}")
        
        return RedirectResponse("/game/sao/?s=1", 303)