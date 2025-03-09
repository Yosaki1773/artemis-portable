from core.config import CoreConfig
from core.data import Data


class CardMakerData(Data):
    def __init__(self, cfg: CoreConfig) -> None:
        super().__init__(cfg)
        # empty Card Maker database
