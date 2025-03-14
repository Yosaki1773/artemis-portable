from core.data import Data
from core.config import CoreConfig
from titles.chuni.schema import *
from .config import ChuniConfig

class ChuniData(Data):
    def __init__(self, cfg: CoreConfig, chuni_cfg: ChuniConfig = None) -> None:
        super().__init__(cfg)

        self.item = ChuniItemData(cfg, self.session)
        self.profile = ChuniProfileData(cfg, self.session)
        self.score = ChuniScoreData(cfg, self.session)
        self.static = ChuniStaticData(cfg, self.session)

        # init rom versioning for use with score playlog data
        if chuni_cfg:
            ChuniRomVersion.init_versions(chuni_cfg)
