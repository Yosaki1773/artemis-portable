from core.config import CoreConfig
from titles.mai2.base import Mai2Base
from titles.mai2.config import Mai2Config
from titles.mai2.const import Mai2Constants


class Mai2Finale(Mai2Base):
    def __init__(self, cfg: CoreConfig, game_cfg: Mai2Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = Mai2Constants.VER_MAIMAI_FINALE
        self.can_deliver = True
        self.can_usbdl = True
