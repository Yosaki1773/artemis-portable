import json
import logging
import string
import zlib
from logging.handlers import TimedRotatingFileHandler
from os import path
from typing import Dict, List, Tuple

import coloredlogs
import inflection
import yaml
from core import CoreConfig, Utils
from core.title import BaseServlet
from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from .air import ChuniAir
from .airplus import ChuniAirPlus
from .amazon import ChuniAmazon
from .amazonplus import ChuniAmazonPlus
from .base import ChuniBase
from .config import ChuniConfig
from .const import ChuniConstants
from .crystal import ChuniCrystal
from .crystalplus import ChuniCrystalPlus
from .luminous import ChuniLuminous
from .luminousplus import ChuniLuminousPlus
from .verse import ChuniVerse
from .sunplus import ChuniSunPlus
from .new import ChuniNew
from .newplus import ChuniNewPlus
from .paradise import ChuniParadise
from .plus import ChuniPlus
from .star import ChuniStar
from .starplus import ChuniStarPlus
from .sun import ChuniSun
from .sunplus import ChuniSunPlus


class ChuniServlet(BaseServlet):
    def __init__(self, core_cfg: CoreConfig, cfg_dir: str) -> None:
        super().__init__(core_cfg, cfg_dir)
        self.game_cfg = ChuniConfig()
        self.hash_table: Dict[Dict[str, str]] = {}
        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}", encoding='utf-8'))
            )

        self.versions = [
            ChuniBase,
            ChuniPlus,
            ChuniAir,
            ChuniAirPlus,
            ChuniStar,
            ChuniStarPlus,
            ChuniAmazon,
            ChuniAmazonPlus,
            ChuniCrystal,
            ChuniCrystalPlus,
            ChuniParadise,
            ChuniNew,
            ChuniNewPlus,
            ChuniSun,
            ChuniSunPlus,
            ChuniLuminous,
            ChuniLuminousPlus,
            ChuniVerse,
        ]

        self.logger = logging.getLogger("chuni")

        if not hasattr(self.logger, "inited"):
            log_fmt_str = "[%(asctime)s] Chunithm | %(levelname)s | %(message)s"
            log_fmt = logging.Formatter(log_fmt_str)
            fileHandler = TimedRotatingFileHandler(
                "{0}/{1}.log".format(self.core_cfg.server.log_dir, "chuni"),
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

        for version, keys in self.game_cfg.crypto.keys.items():
            if len(keys) < 3:
                continue

            self.hash_table[version] = {}

            method_list = [
                method
                for method in dir(self.versions[version])
                if not method.startswith("__")
            ]
            for method in method_list:
                method_fixed = inflection.camelize(method)[6:-7]
                # number of iterations was changed to 70 in SUN and then to 36
                if version == ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS:
                    iter_count = 56
                elif version == ChuniConstants.VER_CHUNITHM_LUMINOUS:
                    iter_count = 8
                elif version == ChuniConstants.VER_CHUNITHM_SUN_PLUS:
                    iter_count = 36
                elif version == ChuniConstants.VER_CHUNITHM_SUN:
                    iter_count = 70
                else:
                    iter_count = 44

                hash = PBKDF2(
                    method_fixed,
                    bytes.fromhex(keys[2]),
                    128,
                    count=iter_count,
                    hmac_hash_module=SHA1,
                )

                hashed_name = hash.hex()[
                    :32
                ]  # truncate unused bytes like the game does
                self.hash_table[version][hashed_name] = method_fixed

                self.logger.debug(
                    f"Hashed v{version} method {method_fixed} with {bytes.fromhex(keys[2])} to get {hash.hex()}"
                )

    @classmethod
    def is_game_enabled(
        cls, game_code: str, core_cfg: CoreConfig, cfg_dir: str
    ) -> bool:
        game_cfg = ChuniConfig()
        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}", encoding='utf-8'))
            )

        if not game_cfg.server.enable:
            return False

        return True

    def get_allnet_info(
        self, game_code: str, game_ver: int, keychip: str
    ) -> Tuple[str, str]:
        if (
            not self.core_cfg.server.is_using_proxy
            and Utils.get_title_port(self.core_cfg) != 80
        ):
            return (
                f"http://{self.core_cfg.server.hostname}:{Utils.get_title_port(self.core_cfg)}/{game_code}/{game_ver}/",
                self.core_cfg.server.hostname,
            )

        return (
            f"http://{self.core_cfg.server.hostname}/{game_code}/{game_ver}/",
            self.core_cfg.server.hostname,
        )

    def get_routes(self) -> List[Route]:
        return [
            Route(
                "/{game:str}/{version:int}/ChuniServlet/{endpoint:str}",
                self.render_POST,
                methods=["POST"],
            ),
            Route(
                "/{game:str}/{version:int}/ChuniServlet/MatchingServer/{endpoint:str}",
                self.render_POST,
                methods=["POST"],
            ),
        ]

    async def render_POST(self, request: Request) -> bytes:
        endpoint: str = request.path_params.get("endpoint")
        version: int = request.path_params.get("version")
        game_code: str = request.path_params.get("game")

        if endpoint.lower() == "ping":
            return Response(zlib.compress(b'{"returnCode": "1"}'))

        req_raw = await request.body()

        encrtped = False
        internal_ver = 0
        client_ip = Utils.get_ip_addr(request)

        if game_code == "SDHD" or game_code == "SDBT":  # JP
            if version < 105:  # 1.0
                internal_ver = ChuniConstants.VER_CHUNITHM
            elif version >= 105 and version < 110:  # PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_PLUS
            elif version >= 110 and version < 115:  # AIR
                internal_ver = ChuniConstants.VER_CHUNITHM_AIR
            elif version >= 115 and version < 120:  # AIR PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_AIR_PLUS
            elif version >= 120 and version < 125:  # STAR
                internal_ver = ChuniConstants.VER_CHUNITHM_STAR
            elif version >= 125 and version < 130:  # STAR PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_STAR_PLUS
            elif version >= 130 and version < 135:  # AMAZON
                internal_ver = ChuniConstants.VER_CHUNITHM_AMAZON
            elif version >= 135 and version < 140:  # AMAZON PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_AMAZON_PLUS
            elif version >= 140 and version < 145:  # CRYSTAL
                internal_ver = ChuniConstants.VER_CHUNITHM_CRYSTAL
            elif version >= 145 and version < 150:  # CRYSTAL PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS
            elif version >= 150 and version < 200:  # PARADISE
                internal_ver = ChuniConstants.VER_CHUNITHM_PARADISE
            elif version >= 200 and version < 205:  # NEW!!
                internal_ver = ChuniConstants.VER_CHUNITHM_NEW
            elif version >= 205 and version < 210:  # NEW PLUS!!
                internal_ver = ChuniConstants.VER_CHUNITHM_NEW_PLUS
            elif version >= 210 and version < 215:  # SUN
                internal_ver = ChuniConstants.VER_CHUNITHM_SUN
            elif 215 <= version < 220:  # SUN
                internal_ver = ChuniConstants.VER_CHUNITHM_SUN_PLUS
            elif 220 <= version < 225:
                internal_ver = ChuniConstants.VER_CHUNITHM_LUMINOUS
            elif 225 <= version < 230:
                internal_ver = ChuniConstants.VER_CHUNITHM_LUMINOUS_PLUS
            elif version >= 230:  
                internal_ver = ChuniConstants.VER_CHUNITHM_VERSE
        elif game_code == "SDGS":  # Int
            if version < 110:  # SUPERSTAR
                internal_ver = (
                    ChuniConstants.VER_CHUNITHM_PARADISE
                )  # FIXME: Not sure what was intended to go here? was just "PARADISE"
            elif version >= 110 and version < 115:  # NEW
                internal_ver = ChuniConstants.VER_CHUNITHM_NEW
            elif version >= 115 and version < 120:  # NEW PLUS!!
                internal_ver = ChuniConstants.VER_CHUNITHM_NEW_PLUS
            elif version >= 120 and version < 125:  # SUN
                internal_ver = ChuniConstants.VER_CHUNITHM_SUN
            elif 125 <= version < 130:  # SUN PLUS
                internal_ver = ChuniConstants.VER_CHUNITHM_SUN_PLUS
            elif version >= 130:  # LUMINOUS
                internal_ver = ChuniConstants.VER_CHUNITHM_LUMINOUS

        if all(c in string.hexdigits for c in endpoint) and len(endpoint) == 32:
            # If we get a 32 character long hex string, it's a hash and we're
            # doing encrypted. The likelyhood of false positives is low but
            # technically not 0
            if internal_ver < ChuniConstants.VER_CHUNITHM_NEW:
                endpoint = request.headers.get("User-Agent").split("#")[0]

            else:
                if internal_ver not in self.hash_table:
                    self.logger.error(
                        f"v{version} does not support encryption or no keys entered"
                    )
                    return Response(zlib.compress(b'{"stat": "0"}'))

                elif endpoint.lower() not in self.hash_table[internal_ver]:
                    self.logger.error(
                        f"No hash found for v{version} endpoint {endpoint}"
                    )
                    return Response(zlib.compress(b'{"stat": "0"}'))

                endpoint = self.hash_table[internal_ver][endpoint.lower()]

            try:
                crypt = AES.new(
                    bytes.fromhex(self.game_cfg.crypto.keys[internal_ver][0]),
                    AES.MODE_CBC,
                    bytes.fromhex(self.game_cfg.crypto.keys[internal_ver][1]),
                )

                req_raw = crypt.decrypt(req_raw)

            except Exception as e:
                self.logger.error(
                    f"Failed to decrypt v{version} request to {endpoint} -> {e}"
                )
                return Response(zlib.compress(b'{"stat": "0"}'))

            encrtped = True

        if (
            not encrtped
            and self.game_cfg.crypto.encrypted_only
            and internal_ver >= ChuniConstants.VER_CHUNITHM_CRYSTAL_PLUS
        ):
            self.logger.error(
                f"Unencrypted v{version} {endpoint} request, but config is set to encrypted only: {req_raw}"
            )
            return Response(zlib.compress(b'{"stat": "0"}'))

        try:
            unzip = zlib.decompress(req_raw)

        except zlib.error as e:
            self.logger.error(
                f"Failed to decompress v{version} {endpoint} request -> {e}"
            )
            return Response(zlib.compress(b'{"stat": "0"}'))

        req_data = json.loads(unzip)

        self.logger.info(f"v{version} {endpoint} request from {client_ip}")
        self.logger.debug(req_data)

        endpoint = endpoint.replace("C3Exp", "") if game_code == "SDGS" else endpoint
        func_to_find = "handle_" + inflection.underscore(endpoint) + "_request"
        handler_cls = self.versions[internal_ver](self.core_cfg, self.game_cfg)

        if not hasattr(handler_cls, func_to_find):
            self.logger.warning(f"Unhandled v{version} request {endpoint}")
            resp = {"returnCode": 1}

        else:
            try:
                handler = getattr(handler_cls, func_to_find)
                resp = await handler(req_data)

            except Exception as e:
                self.logger.error(f"Error handling v{version} method {endpoint} - {e}")
                return Response(zlib.compress(b'{"stat": "0"}'))

        if resp is None:
            resp = {"returnCode": 1}

        self.logger.debug(f"Response {resp}")

        zipped = zlib.compress(json.dumps(resp, ensure_ascii=False).encode("utf-8"))

        if not encrtped:
            return Response(zipped)

        padded = pad(zipped, 16)

        crypt = AES.new(
            bytes.fromhex(self.game_cfg.crypto.keys[internal_ver][0]),
            AES.MODE_CBC,
            bytes.fromhex(self.game_cfg.crypto.keys[internal_ver][1]),
        )

        return Response(crypt.encrypt(padded))
