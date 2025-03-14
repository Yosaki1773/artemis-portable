from core.config import CoreConfig


class SaoServerConfig:
    def __init__(self, parent_config: "SaoConfig"):
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "sao", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return CoreConfig.str_to_loglevel(
            CoreConfig.get_config_field(
                self.__config, "sao", "server", "loglevel", default="info"
            )
        )

    @property
    def auto_register(self) -> bool:
        """
        Automatically register users in `aime_user` on first carding in with sao
        if they don't exist already. Set to false to display an error instead.
        """
        return CoreConfig.get_config_field(
            self.__config, "sao", "server", "auto_register", default=True
        )

    @property
    def photon_app_id(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "sao", "server", "photon_app_id", default="7df3a2f6-d69d-4073-aafe-810ee61e1cea"
        )

    @property
    def data_version(self) -> int:
        return CoreConfig.get_config_field(
            self.__config, "sao", "server", "data_version", default=1
        )

    @property
    def game_version(self) -> int:
        return CoreConfig.get_config_field(
            self.__config, "sao", "server", "game_version", default=33
        )

class SaoCryptConfig:
    def __init__(self, parent_config: "SaoConfig"):
        self.__config = parent_config
    
    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "sao", "crypt", "enable", default=False
        )
    
    @property
    def key(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "sao", "crypt", "key", default=""
        )

class SaoHashConfig:
    def __init__(self, parent_config: "SaoConfig"):
        self.__config = parent_config
        
    @property
    def verify_hash(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "sao", "hash", "verify_hash", default=False
        )
    
    @property
    def hash_base(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "sao", "hash", "hash_base", default=""
        )

class SaoCardConfig:
    def __init__(self, parent_config: "SaoConfig"):
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "sao", "card", "enable", default=True
        )
    
    @property
    def crypt_password(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "sao", "card", "crypt_password", default=""
        )
    
    @property
    def crypt_salt(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "sao", "card", "crypt_salt", default=""
        )

class SaoConfig(dict):
    def __init__(self) -> None:
        self.server = SaoServerConfig(self)
        self.crypt = SaoCryptConfig(self)
        self.hash = SaoHashConfig(self)
        self.card = SaoCardConfig(self)
