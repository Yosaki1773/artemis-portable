from os import path
from typing import List

import jinja2
import yaml
from core.config import CoreConfig
from core.frontend import FE_Base, UserSession
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from titles.wacca.config import WaccaConfig
from titles.wacca.const import WaccaConstants
from titles.wacca.database import WaccaData


class WaccaFrontend(FE_Base):
    def __init__(
        self, cfg: CoreConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.data = WaccaData(cfg)
        self.game_cfg = WaccaConfig()
        if path.exists(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{WaccaConstants.CONFIG_NAME}"))
            )
        self.nav_name = "Wacca"

    def get_routes(self) -> List[Route]:
        return [Route("/", self.render_GET, methods=["GET"])]

    async def render_GET(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/wacca/templates/wacca_index.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        return Response(
            template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
            ),
            media_type="text/html; charset=utf-8",
        )
