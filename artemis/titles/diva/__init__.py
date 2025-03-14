from titles.diva.index import DivaServlet
from titles.diva.const import DivaConstants
from titles.diva.database import DivaData
from titles.diva.read import DivaReader
from .frontend import DivaFrontend

index = DivaServlet
database = DivaData
reader = DivaReader
frontend = DivaFrontend
game_codes = [DivaConstants.GAME_CODE]
