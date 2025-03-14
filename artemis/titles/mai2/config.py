from core.config import CoreConfig


class Mai2ServerConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return CoreConfig.str_to_loglevel(
            CoreConfig.get_config_field(
                self.__config, "mai2", "server", "loglevel", default="info"
            )
        )


class Mai2DeliverConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "deliver", "enable", default=False
        )

    @property
    def udbdl_enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "deliver", "udbdl_enable", default=False
        )

    @property
    def content_folder(self) -> int:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "deliver", "content_folder", default=""
        )


class Mai2UploadsConfig:
    def __init__(self, parent: "Mai2Config") -> None:
        self.__config = parent

    @property
    def photos(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "uploads", "photos", default=False
        )

    @property
    def photos_dir(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "uploads", "photos_dir", default=""
        )

    @property
    def movies(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "uploads", "movies", default=False
        )

    @property
    def movies_dir(self) -> str:
        return CoreConfig.get_config_field(
            self.__config, "mai2", "uploads", "movies_dir", default=""
        )


class Mai2Config(dict):
    def __init__(self) -> None:
        self.server = Mai2ServerConfig(self)
        self.deliver = Mai2DeliverConfig(self)
        self.uploads = Mai2UploadsConfig(self)
