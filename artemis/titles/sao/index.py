from typing import Tuple, Dict, List
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse, FileResponse
from starlette.routing import Route
import yaml
import logging, coloredlogs
from logging.handlers import TimedRotatingFileHandler
from os import path
from Crypto.Cipher import Blowfish
from Crypto.Hash import MD5
import secrets
import traceback
import sys

from core import CoreConfig
from core.title import BaseServlet
from core.utils import Utils
from titles.sao.config import SaoConfig
from titles.sao.const import SaoConstants
from titles.sao.base import SaoBase
from titles.sao.handlers.base import *


class SaoServlet(BaseServlet):
    def __init__(self, core_cfg: CoreConfig, cfg_dir: str) -> None:
        super().__init__(core_cfg, cfg_dir)
        self.config_dir = cfg_dir
        self.game_cfg = SaoConfig()
        if path.exists(f"{cfg_dir}/sao.yaml"):
            self.game_cfg.update(yaml.safe_load(open(f"{cfg_dir}/sao.yaml")))

        self.logger = logging.getLogger("sao")
        if not hasattr(self.logger, "inited"):
            log_fmt_str = "[%(asctime)s] SAO | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)
            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.core_cfg.server.log_dir, "sao"),
                encoding="utf8",
                when="d",
                backupCount=10,
            )

            fileHandler.setFormatter(log_fmt)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(log_fmt)

            self.logger.addHandler(fileHandler)
            self.logger.addHandler(consoleHandler)

            self.logger.setLevel(self.game_cfg.server.loglevel)
            coloredlogs.install(
                level=self.game_cfg.server.loglevel, logger=self.logger, fmt=log_fmt_str
            )
            self.logger.inited = True

        self.base = SaoBase(core_cfg, self.game_cfg)
        self.static_hash = None
        
        if self.game_cfg.hash.verify_hash:
            self.static_hash = MD5.new(self.game_cfg.hash.hash_base.encode()).digest() # Greate hashing guys, really validates the data

    def get_routes(self) -> List[Route]:
        return [
            Route("/{datecode:int}/proto/if/{category:str}/{endpoint:str}", self.render_POST, methods=['POST']),
            Route("/saoresource/{resource_type:str}/{resource_id:int}/{endpoint:str}", self.handle_resource),
            Route("/system_status.php", self.render_system_status),
        ]

    @classmethod
    def is_game_enabled(cls, game_code: str, core_cfg: CoreConfig, cfg_dir: str) -> bool:
        game_cfg = SaoConfig()

        if path.exists(f"{cfg_dir}/{SaoConstants.CONFIG_NAME}"):
            game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{SaoConstants.CONFIG_NAME}"))
            )
    
        if not game_cfg.server.enable:
            return False
        
        return True

    def get_allnet_info(self, game_id: str, int_ver: int, serial: str) -> Tuple[str, str]:
        if self.core_cfg.server.is_using_proxy:
            return (f"https://{self.core_cfg.server.hostname}/", "")
        
        return (f"http://{self.core_cfg.server.hostname}:{Utils.get_title_port(self.core_cfg)}/", "")

    def get_mucha_info(self, core_cfg: CoreConfig, cfg_dir: str) -> Tuple[bool, List[str], List[str]]:
        if not self.game_cfg.server.enable:
            return (False, [], [])

        return (True, SaoConstants.GAME_CDS, SaoConstants.NETID_PREFIX)

    async def render_system_status(self, request: Request) -> bytes:
        return PlainTextResponse("open")

    async def render_POST(self, request: Request) -> bytes:
        endpoint = request.path_params['endpoint']
        ip = Utils.get_ip_addr(request)
        iv = b""

        req_raw = await request.body()
        if len(req_raw) < 40:
            self.logger.warning(f"Malformed request to {endpoint} - {req_raw.hex()}")
            return Response()
        req_header = SaoRequestHeader(req_raw)
        
        cmd_str = f"{req_header.cmd:04x}"
        
        if self.game_cfg.hash.verify_hash and self.static_hash != req_header.hash:
            self.logger.error(f"Hash mismatch! Expecting {self.static_hash} but recieved {req_header.hash}")
            return Response()
        
        if self.game_cfg.crypt.enable:
            iv = req_raw[40:48]
            cipher = Blowfish.new(self.game_cfg.crypt.key.encode(), Blowfish.MODE_CBC, iv)
            crypt_data = req_raw[48:]
            req_data = cipher.decrypt(crypt_data)
            self.logger.debug(f"Decrypted {req_data.hex()} with IV {iv.hex()}")
            
        else:
            req_data = req_raw[40:]

        self.logger.debug(f"{endpoint} ({cmd_str}) Request from {ip}: {req_raw.hex()}")
        handler = getattr(self.base, f"handle_{cmd_str}", None)
        if handler is None:
            self.logger.info(f"Using Generic handler for {endpoint}")
            handler = self.base.handle_noop

        try:
            resp = await handler(req_header, req_data, ip)
        
        except Exception as e:
            self.logger.error(f"Error handling {endpoint} - {e}")
            tp, val, tb  = sys.exc_info()
            traceback.print_exception(tp, val, tb, limit=5)
            with open("{0}/{1}.log".format(self.core_cfg.server.log_dir, "sao"), "a") as f:
                traceback.print_exception(tp, val, tb, limit=5, file=f)
            
            resp = SaoNoopResponse(req_header.cmd + 1).make()

        if resp is None:
            resp = SaoNoopResponse(req_header.cmd + 1).make()
        
        if type(resp) == bytes:
            pass
        
        elif issubclass(resp, SaoBaseResponse):
            resp = resp.make()
        
        else:
            self.logger.error(f"Unknown response type {type(resp)}")
            return SaoNoopResponse(req_header.cmd + 1).make()
        
        self.logger.debug(f"Response: {resp.hex()}")

        if self.game_cfg.crypt.enable:
            iv = secrets.token_bytes(8)
            data_to_crypt = resp[24:]
            while len(data_to_crypt) % 8 != 0:
                data_to_crypt += b"\x00"
            
            cipher = Blowfish.new(self.game_cfg.crypt.key.encode(), Blowfish.MODE_CBC, iv)
            data_crypt = cipher.encrypt(data_to_crypt)
            crypt_data_len = len(data_crypt) + len(iv)
            tmp = struct.pack("!I", crypt_data_len) # does it want the length of the encrypted response??
            resp = resp[:20] + tmp + iv + data_crypt
            self.logger.debug(f"Encrypted Response: {resp.hex()}")

        return Response(resp)

    async def handle_resource(self, request: Request) -> bytes:
        # TODO: better guard against path traversal attacks
        resource_type = request.path_params['resource_type'].replace(".\\", "").replace("..\\", "")
        resource_id = request.path_params['resource_id']
        endpoint = request.path_params['endpoint'].replace(".\\", "").replace("..\\", "")
        req_ip = Utils.get_ip_addr(request)

        self.logger.debug(f"{req_ip} requested {resource_type} id {resource_id} {endpoint}")
        if path.exists(f"./titles/sao/data/{resource_type}/{resource_id}/{endpoint}"):
            return FileResponse(f"./titles/sao/data/{resource_type}/{resource_id}/{endpoint}")
        return Response(status_code=404)
