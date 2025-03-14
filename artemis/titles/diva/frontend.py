from typing import List
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from os import path
import yaml
import jinja2

from core.frontend import FE_Base, UserSession
from core.config import CoreConfig
from .database import DivaData
from .config import DivaConfig
from .const import DivaConstants

class DivaFrontend(FE_Base):
    def __init__(
        self, cfg: CoreConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.data = DivaData(cfg)
        self.game_cfg = DivaConfig()
        if path.exists(f"{cfg_dir}/{DivaConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{DivaConstants.CONFIG_NAME}"))
            )
        self.nav_name = "Project Diva"
    
    def get_routes(self) -> List[Route]:
        return [
            Route("/", self.render_GET, methods=['GET']),
            Mount("/playlog", routes=[
                Route("/", self.render_GET_playlog, methods=['GET']),
                Route("/{index}", self.render_GET_playlog, methods=['GET']),
            ]),
            Route("/update.name", self.update_name, methods=['POST']),
            Route("/update.lv", self.update_lv, methods=['POST']),
        ]
    
    async def render_GET(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/diva/templates/diva_index.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()
        
        if usr_sesh.user_id > 0:
            profile = await self.data.profile.get_profile(usr_sesh.user_id, 1)
            
            resp = Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=usr_sesh.user_id,
                profile=profile
            ), media_type="text/html; charset=utf-8")
            return resp
        else:
            return RedirectResponse("/gate")
    
    async def render_GET_playlog(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/diva/templates/diva_playlog.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()
        
        if usr_sesh.user_id > 0:
            path_index = request.path_params.get("index")
            if not path_index or int(path_index) < 1:
                index = 0
            else:
                index = int(path_index) - 1 # 0 and 1 are 1st page
            user_id = usr_sesh.user_id
            playlog_count = await self.data.score.get_user_playlogs_count(user_id)
            if playlog_count < index * 20 :
                return Response(template.render(
                    title=f"{self.core_config.server.name} | {self.nav_name}",
                    game_list=self.environment.globals["game_list"],
                    sesh=vars(usr_sesh),
                    score_count=0
                ), media_type="text/html; charset=utf-8")
            playlog = await self.data.score.get_playlogs(user_id, index, 20) #Maybe change to the playlog instead of direct scores
            playlog_with_title = []
            for record in playlog:
                song = await self.data.static.get_music_chart(record[2], record[3], record[4])
                if song:
                    title = song.title
                    vocaloid_arranger = song.vocaloid_arranger
                else:
                    title = "Unknown"
                    vocaloid_arranger = "Unknown"
                playlog_with_title.append({
                    "raw": record,
                    "title": title,
                    "vocaloid_arranger": vocaloid_arranger
                })
            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=usr_sesh.user_id,
                playlog=playlog_with_title,
                playlog_count=playlog_count
            ), media_type="text/html; charset=utf-8")
        else:
            return RedirectResponse("/gate/", 300)
        
    async def update_name(self, request: Request) -> Response:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate")
        
        form_data = await request.form()
        new_name: str = form_data.get("new_name")
        new_name_full = ""

        if not new_name:
            return RedirectResponse("/gate/?e=4", 303)
        
        if len(new_name) > 8:
            return RedirectResponse("/gate/?e=8", 303)
        
        for x in new_name: # FIXME: This will let some invalid characters through atm
            o = ord(x)
            try:
                if o == 0x20:
                    new_name_full += chr(0x3000)
                elif o < 0x7F and o > 0x20:
                    new_name_full += chr(o + 0xFEE0)
                elif o <= 0x7F:
                    self.logger.warning(f"Invalid ascii character {o:02X}")
                    return RedirectResponse("/gate/?e=4", 303)
                else:
                    new_name_full += x
            
            except Exception as e:
                self.logger.error(f"Something went wrong parsing character {o:04X} - {e}")
                return RedirectResponse("/gate/?e=4", 303)
            
        if not await self.data.profile.update_profile(usr_sesh.user_id, player_name=new_name_full):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/diva", 303)
        
    async def update_lv(self, request: Request) -> Response:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate")
        
        form_data = await request.form()
        new_lv: str = form_data.get("new_lv")
        new_lv_full = ""

        if not new_lv:
            return RedirectResponse("/gate/?e=4", 303)
        
        if len(new_lv) > 8:
            return RedirectResponse("/gate/?e=8", 303)
        
        for x in new_lv: # FIXME: This will let some invalid characters through atm
            o = ord(x)
            try:
                if o == 0x20:
                    new_lv_full += chr(0x3000)
                elif o < 0x7F and o > 0x20:
                    new_lv_full += chr(o + 0xFEE0)
                elif o <= 0x7F:
                    self.logger.warning(f"Invalid ascii character {o:02X}")
                    return RedirectResponse("/gate/?e=4", 303)
                else:
                    new_lv_full += x
            
            except Exception as e:
                self.logger.error(f"Something went wrong parsing character {o:04X} - {e}")
                return RedirectResponse("/gate/?e=4", 303)
            
        if not await self.data.profile.update_profile(usr_sesh.user_id, lv_str=new_lv_full):
            return RedirectResponse("/gate/?e=999", 303)
            
        return RedirectResponse("/game/diva", 303)
