from core.config import CoreConfig


class DivaServerConfig:
    def __init__(self, parent_config: "DivaConfig") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "diva", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return CoreConfig.str_to_loglevel(
            CoreConfig.get_config_field(
                self.__config, "diva", "server", "loglevel", default="info"
            )
        )

    @property
    def festa_enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "diva", "server", "festa_enable", default=True
        )
    
    @property
    def festa_add_VP(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "diva", "server", "festa_add_VP", default="20,5"
        )
    
    @property
    def festa_multiply_VP(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "diva", "server", "festa_multiply_VP", default="1,2"
        )
    
    @property
    def festa_end_time(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "diva", "server", "festa_end_time", default="2029-01-01 00:00:00.0"
        )

class DivaModsConfig:
    def __init__(self, parent_config: "DivaConfig") -> None:
        self.__config = parent_config

    @property
    def unlock_all_modules(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "diva", "mods", "unlock_all_modules", default=True
        )

    @property
    def unlock_all_items(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "diva", "mods", "unlock_all_items", default=True
        )


class DivaConfig(dict):
    def __init__(self) -> None:
        self.server = DivaServerConfig(self)
        self.mods = DivaModsConfig(self)
