from .const import SaoConstants
from .database import SaoData
from .index import SaoServlet
from .read import SaoReader

index = SaoServlet
database = SaoData
reader = SaoReader
game_codes = [SaoConstants.GAME_CODE]
