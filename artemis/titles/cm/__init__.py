from titles.cm.const import CardMakerConstants
from titles.cm.database import CardMakerData
from titles.cm.index import CardMakerServlet
from titles.cm.read import CardMakerReader

index = CardMakerServlet
reader = CardMakerReader
database = CardMakerData
game_codes = [CardMakerConstants.GAME_CODE]
