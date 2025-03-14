from .index import SaoServlet
from .const import SaoConstants
from .database import SaoData
from .frontend import SaoFrontend
from .read import SaoReader

index = SaoServlet
database = SaoData
frontend = SaoFrontend
reader = SaoReader
game_codes = [SaoConstants.GAME_CODE]
