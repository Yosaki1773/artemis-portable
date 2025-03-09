from .const import PokkenConstants
from .database import PokkenData
from .frontend import PokkenFrontend
from .index import PokkenServlet

index = PokkenServlet
database = PokkenData
game_codes = [PokkenConstants.GAME_CODE]
frontend = PokkenFrontend
