from titles.idac.const import IDACConstants
from titles.idac.database import IDACData
from titles.idac.frontend import IDACFrontend
from titles.idac.index import IDACServlet
from titles.idac.read import IDACReader

index = IDACServlet
database = IDACData
reader = IDACReader
frontend = IDACFrontend
game_codes = [IDACConstants.GAME_CODE]
