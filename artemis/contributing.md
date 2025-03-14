# Contributing to ARTEMiS
If you would like to contribute to artemis, either by adding features, games, or fixing bugs, you can do so by forking the repo and submitting a pull request [here](https://gitea.tendokyu.moe/Hay1tsme/artemis/pulls). This guide assume you're familiar with both git, python, and the libraries that artemis uses.

This document is a work in progress. If you have any questions or notice any errors, please report it to the discord.

## Adding games
### Step 0
+ Follow the "n-1" rule of thumb. PRs for game versions that are currently active in arcades will be deleted. If you're unsure, ask!
+ Always PR against the `develop` branch.
+ Check to see if somebody else is already PRing the features/games you want to add. If they are, consider contributing to them rather then making an entirely new PR.
+ We don't technically have a written code style guide (TODO) but try to keep your code consistant with code that's already there where possible.

### Step 1 (Setup)
1) Fork the gitea repo, clone your fork, and checkout the develop branch.
2) Make a new folder in the `titles` folder, name it some recogniseable shorthand for your game (Chunithm becomes chuni, maimai dx is mai2, etc)
3) In this new folder, create a file named `__init__.py`. This is the first thing that will load when your title module is loaded by the core system, and it acts as sort of a directory for where everything lives in your module. This file will contain the following required items:
    + `index`: must point to a subclass of `BaseServlet` that will handle setup and dispatching of your game.
    + `game_codes`: must be a list of 4 letter SEGA game codes as strings.

    It can also contain the following optional fields:
    + `database`: points to a subclass of `Data` that contains one or more subclasses of `BaseData` that act as database transaction handlers. Required for the class to store and retrieve data from the database.
    + `reader`: points to a subclass of `BaseReader` that handles importing static data from game files into the database.
    + `frontend`: points to a subclass of `FE_Base` that handles frontend routes for your game.

    The next step will focus on `index`

### Step 2 (Index)
1) Create another file in your game's folder. By convention, it should be called `index.py`.

2) Inside `index.py`, add the following code, replacing {Game name here} with the name of your game, without spaces or special characters. Look at other titles for examples.
```py
from core.title import BaseServlet
from core import CoreConfig

class {Game name here}Servlet(BaseServlet):
    def __init__(self, core_cfg: CoreConfig, cfg_dir: str) -> None:
        pass
```
3) The `__init__` function should acomplish the following:
    + Reading your game's config
    + Setting up your games logger
    + Instancing your games versions
    
    It's usually safe to copy and paste the `__init__` functions from other games, just make sure you change everything that needs to be changed!

4) Go back to the `__init__.py` that you created and add the following:
```py
from .index import {Game name here}Servlet

index = {Game name here}Servlet
```

5) Going back to `index.py`, within the Servlet class, define the following functions from `BaseServlet` as needed (see function documentation):
    + `is_game_enabled`: Returns true if the game is enabled and should be served, false otherwise. Returns false by default, so override this to allow your game to be served.
    + `get_routes`: Returns a list of Starlette routes that your game will serve.
    + `get_allnet_info`: Returns a tuple of strings where the first is the allnet uri and the second is the allnet host. The function takes the game ID, version and keychip ID as parameters, so you can send different responses if need be.
    + `get_mucha_info`: Only used by games that use Mucha as authentication. Returns a tuple where the first is a bool that is weather or not the game is enabled, the 2nd is a list of game CDs as strings that this servlet should handle, and the 3rd is a list of netID prefixes that each game CD should use. If your game does not use mucha, do not define this function.
    + `setup`: Preforms any setup your servlet requires, such as spinning up matching servers. It is run once when the server starts. If you don't need any setup, do not define.

6) Make sure any functions you specify to handle routes in `get_routes` are defined as async, as follows: `async def handle_thing(self, request: Request) -> Response:` where Response is whatever kind of Response class you'll be returning. Make sure all paths in this function return some subclass of Response, otherwise you'll get an error when serving.

### Step 3 (Constants)
1) In your game's folder, create a file to store static values for your game. By convention, we call this `const.py`

2) Inside, create a class called `{Game name here}Constants`. Do not define an `__init__` function.

3) Put constants related to your game here. A good example of something to put here is game codes.
```py
class {Game name here}Constants:
    GAME_CODE = "SBXX"
    CONFIG_NAME = "{game name}.yaml"
```

4) If you choose to put game codes in here, add this to your `__init__.py` file:
```py
from .const import {Game name here}Constants
...
game_codes = [{Game name here}Constants.GAME_CODE]
```

### Step 4 (Config)
1) Make a file to store your game's config. By convention, it should be called `config.py`

2) Inside that file, add the following:
```py
from core.config import CoreConfig

class {game name}ServerConfig:
    def __init__(self, parent_config: "{game name}Config") -> None:
        self.__config = parent_config

    @property
    def enable(self) -> bool:
        return CoreConfig.get_config_field(
            self.__config, "{game name}", "server", "enable", default=True
        )

    @property
    def loglevel(self) -> int:
        return CoreConfig.str_to_loglevel(
            CoreConfig.get_config_field(
                self.__config, "{game name}", "server", "loglevel", default="info"
            )
        )

class {game name}Config(dict):
    def __init__(self) -> None:
        self.server = {game name}ServerConfig(self)
```

3) In the `example_config` folder, create a yaml file for your game. By convention, it should be called `{game folder name}.ymal`. Add the following:
```yaml
server:
    enable: True
    loglevel: "info"
```

4) Add any additional config options that you feel the game needs. Look to other games for config examples.

5) In `index.py` import your config and instance it in `__init__` with:
```py
self.game_cfg = {game folder name}Config()
if path.exists(f"{cfg_dir}/{game folder name}Constants.CONFIG_NAME}"):
    self.game_cfg.update(
        yaml.safe_load(open(f"{cfg_dir}/{game folder name}Constants.CONFIG_NAME}"))
    )
```
This will attempt to load the config file you specified in your constants, and if not, go with the defaults specified in `config.py`. This game_cfg object can then be passed down to your handlers when you create them.

At this stage your game should be loaded by allnet, and serve whatever routes you put in `get_routes`. See the next section about adding versions and handlers.

### Step 5 (Database)
TODO

### Step 6 (Frontend)
TODO

### Step 7 (Reader)
TODO

## Adding game versions
See the above section about code expectations and how to PR.
1) In the game's folder, create a python file to contain the version handlers. By convention, the first version is version 0, and is stored in `base.py`. Versions following that increment the version number, and are stored in `{short version name}.py`. See Wacca's folder for an example of how to name versions.

2) Internal version numbers should be defined in `const.py`. The version should change any time the game gets a major update (i.e. a new version or plus version.)
```py
# in const.py
VERSION_{game name} = 0
VERSION_{game name}_PLUS = 1
```

3) Inside `base.py` (or whatever your version is named) add the following:
```py
class {game name}Base:
    def __init__(self, cfg: CoreConfig, game_cfg: {game name}Config) -> None:
        self.game_config = game_cfg
        self.core_config = cfg
        self.version = {game name}Constants.VERSION_{game name}
        self.data = {game name}Data(cfg)
        # Any other initialization stuff
```

4) Define your handlers. This will vary wildly by game, but best practice is to keep the naming consistant, so that the main dispatch function in `index.py` can use `getattr` to get the handler, rather then having a static list of what endpoint or request type goes to which handler. See Wacca's `index.py` and `base.py` for examples of how to do this.

5) If your version is not the base version, make sure it inherits from the base version:
```py
class {game name}Plus({game name}Base):
    def __init__(self, cfg: CoreConfig, game_cfg: {game name}Config) -> None:
        super().__init__(cfg, game_cfg)
        self.version = {game name}Constants.VERSION_{game name}_PLUS
```

6) Back in `index.py` make sure to import your new class, and add it to `__init__`. Some games may opt to just a single list called `self.versions` that contains all the version classes at their internal version's index. Others may simply define them as seperate members. See Wacca for an example of `self.versions`

7) Add your version to your game's dispatching logic.

8) Test to make sure your game is being handled properly.

9) Submit a PR.

## Adding/improving core services
If you intend to submit improvements or additions to core services (allnet, mucha, billing, aimedb, database, etc) please get in touch with a maintainer.
