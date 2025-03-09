from titles.ongeki.const import OngekiConstants
from titles.ongeki.database import OngekiData
from titles.ongeki.frontend import OngekiFrontend
from titles.ongeki.index import OngekiServlet
from titles.ongeki.read import OngekiReader

index = OngekiServlet
database = OngekiData
reader = OngekiReader
frontend = OngekiFrontend
game_codes = [OngekiConstants.GAME_CODE]
