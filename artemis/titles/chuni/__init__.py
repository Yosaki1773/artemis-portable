from .const import ChuniConstants
from .database import ChuniData
from .frontend import ChuniFrontend
from .index import ChuniServlet
from .read import ChuniReader

index = ChuniServlet
database = ChuniData
reader = ChuniReader
frontend = ChuniFrontend
game_codes = [
    ChuniConstants.GAME_CODE,
    ChuniConstants.GAME_CODE_NEW,
    ChuniConstants.GAME_CODE_INT,
]
