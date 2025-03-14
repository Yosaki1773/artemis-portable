from typing import List
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.staticfiles import StaticFiles
from sqlalchemy.engine import Row
from os import path
import yaml
import jinja2

from core.frontend import FE_Base, UserSession
from core.config import CoreConfig
from .database import ChuniData
from .config import ChuniConfig
from .const import ChuniConstants, AvatarCategory, ItemKind


def pairwise(iterable):
    # https://docs.python.org/3/library/itertools.html#itertools.pairwise
    # but for Python < 3.10. pairwise('ABCDEFG') → AB BC CD DE EF FG
    iterator = iter(iterable)
    a = next(iterator, None)
    for b in iterator:
        yield a, b
        a = b


def calculate_song_rank(score: int, game_version: int) -> str:
    if game_version >= ChuniConstants.VER_CHUNITHM_NEW:
        intervals = ChuniConstants.SCORE_RANK_INTERVALS_NEW
    else:
        intervals = ChuniConstants.SCORE_RANK_INTERVALS_OLD

    for (min_score, rank) in intervals:
        if score >= min_score:
            return rank

    return "D"


def calculate_song_rating(score: int, chart_constant: float, game_version: int) -> float:
    is_new = game_version >= ChuniConstants.VER_CHUNITHM_NEW

    if is_new:  # New and later
        max_score = 1009000
        max_rating_modifier = 2.15
    else:  # Up to Paradise Lost
        max_score = 1007500
        max_rating_modifier = 2.0

    if (score < 500000):
        return 0.0  # D
    elif (score >= max_score):
        return chart_constant + max_rating_modifier  # SSS/SSS+

    # Okay, we're doing this the hard way.
    # Rating goes up linearly between breakpoints listed below.
    # Pick the score interval in which we are in, then calculate
    # the position between possible ratings.
    score_intervals = [
        ( 500000, 0.0),  # C
        ( 800000, max(0.0, (chart_constant - 5.0) / 2)),  # BBB
        ( 900000, max(0.0, (chart_constant - 5.0))),  # A
        ( 925000, max(0.0, (chart_constant - 3.0))),  # AA
        ( 975000, chart_constant),  # S
        (1000000, chart_constant + 1.0),  # SS
        (1005000, chart_constant + 1.5),  # SS+
        (1007500, chart_constant + 2.0),  # SSS
        (1009000, chart_constant + max_rating_modifier),  # SSS+!
    ]

    for ((lo_score, lo_rating), (hi_score, hi_rating)) in pairwise(score_intervals):
        if not (lo_score <= score < hi_score):
            continue

        interval_pos = (score - lo_score) / (hi_score - lo_score)
        return lo_rating + ((hi_rating - lo_rating) * interval_pos)



class ChuniFrontend(FE_Base):
    def __init__(
        self, cfg: CoreConfig, environment: jinja2.Environment, cfg_dir: str
    ) -> None:
        super().__init__(cfg, environment)
        self.game_cfg = ChuniConfig()
        if path.exists(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"):
            self.game_cfg.update(
                yaml.safe_load(open(f"{cfg_dir}/{ChuniConstants.CONFIG_NAME}"))
            )
        self.data = ChuniData(cfg, self.game_cfg)
        self.nav_name = "Chunithm"

    def get_routes(self) -> List[Route]:
        return [
            Route("/", self.render_GET, methods=['GET']),
            Route("/rating", self.render_GET_rating, methods=['GET']),
            Mount("/playlog", routes=[
                Route("/", self.render_GET_playlog, methods=['GET']),
                Route("/{index}", self.render_GET_playlog, methods=['GET']),
            ]),
            Route("/favorites", self.render_GET_favorites, methods=['GET']),
            Route("/userbox", self.render_GET_userbox, methods=['GET']),
            Route("/avatar", self.render_GET_avatar, methods=['GET']),
            Route("/update.map-icon", self.update_map_icon, methods=['POST']),
            Route("/update.system-voice", self.update_system_voice, methods=['POST']),            
            Route("/update.userbox", self.update_userbox, methods=['POST']),
            Route("/update.avatar", self.update_avatar, methods=['POST']),
            Route("/update.name", self.update_name, methods=['POST']),
            Route("/update.favorite_music_playlog", self.update_favorite_music_playlog, methods=['POST']),
            Route("/update.favorite_music_favorites", self.update_favorite_music_favorites, methods=['POST']),
            Route("/version.change", self.version_change, methods=['POST']),
            Mount('/img', app=StaticFiles(directory='titles/chuni/img'), name="img")
        ]

    async def render_GET(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_index.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            versions = await self.data.profile.get_all_profile_versions(usr_sesh.user_id)
            profile = []
            if versions:
                # chunithm_version is -1 means it is not initialized yet, select a default version from existing.
                if usr_sesh.chunithm_version < 0:
                    usr_sesh.chunithm_version = versions[0]
                profile = await self.data.profile.get_profile_data(usr_sesh.user_id, usr_sesh.chunithm_version)

            user_id = usr_sesh.user_id
            version = usr_sesh.chunithm_version

            # While map icons and system voices weren't present prior to AMAZON, we don't need to bother checking 
            # version here - it'll just end up being empty sets and the jinja will ignore the variables anyway.
            map_icons, total_map_icons = await self.get_available_map_icons(version, profile)
            system_voices, total_system_voices = await self.get_available_system_voices(version, profile)

            resp = Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=user_id,
                profile=profile,
                version_list=ChuniConstants.VERSION_NAMES,
                versions=versions,
                cur_version=version,
                cur_version_name=ChuniConstants.game_ver_to_string(version),
                map_icons=map_icons,
                system_voices=system_voices,
                total_map_icons=total_map_icons,
                total_system_voices=total_system_voices
            ), media_type="text/html; charset=utf-8")

            if usr_sesh.chunithm_version >= 0:
                encoded_sesh = self.encode_session(usr_sesh)
                resp.set_cookie("ARTEMIS_SESH", encoded_sesh)
            return resp

        else:
            return RedirectResponse("/gate/", 303)

    async def render_GET_rating(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_rating.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.chunithm_version < 0:
                return RedirectResponse("/game/chuni/", 303)
            profile = await self.data.profile.get_profile_data(usr_sesh.user_id, usr_sesh.chunithm_version)
            rating = await self.data.profile.get_profile_rating(usr_sesh.user_id, usr_sesh.chunithm_version)
            hot_list=[]
            base_list=[]
            if profile and rating:
                song_records = []

                for song in rating:
                    music_chart = await self.data.static.get_music_chart(usr_sesh.chunithm_version, song.musicId, song.difficultId)
                    if not music_chart:
                        continue

                    rank = calculate_song_rank(song.score, profile.version)
                    rating = calculate_song_rating(song.score, music_chart.level, profile.version)

                    song_rating = int(rating * 10 ** 2) / 10 ** 2
                    song_records.append({
                        "difficultId": song.difficultId,
                        "musicId": song.musicId,
                        "title": music_chart.title,
                        "level": music_chart.level,
                        "score": song.score,
                        "type": song.type,
                        "rank": rank,
                        "song_rating": song_rating,
                    })

                hot_list = [obj for obj in song_records if obj["type"] == "userRatingBaseHotList"]
                base_list = [obj for obj in song_records if obj["type"] == "userRatingBaseList"]
            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                profile=profile,
                hot_list=hot_list,
                base_list=base_list,
                cur_version=usr_sesh.chunithm_version,
                cur_version_name=ChuniConstants.game_ver_to_string(usr_sesh.chunithm_version)
            ), media_type="text/html; charset=utf-8")
        else:
            return RedirectResponse("/gate/", 303)

    async def render_GET_playlog(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_playlog.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.chunithm_version < 0:
                return RedirectResponse("/game/chuni/", 303)
            path_index = request.path_params.get('index')
            if not path_index or int(path_index) < 1:
                index = 0
            else:
                index = int(path_index) - 1 # 0 and 1 are 1st page
            user_id = usr_sesh.user_id
            version = usr_sesh.chunithm_version
            playlog_count = await self.data.score.get_user_playlogs_count(user_id, version)
            if playlog_count < index * 20 :
                return Response(template.render(
                    title=f"{self.core_config.server.name} | {self.nav_name}",
                    game_list=self.environment.globals["game_list"],
                    sesh=vars(usr_sesh),
                    playlog_count=0,
                    cur_version=version,
                    cur_version_name=ChuniConstants.game_ver_to_string(version)
                ), media_type="text/html; charset=utf-8")
            playlog = await self.data.score.get_playlogs_limited(user_id, version, index, 20)
            playlog_with_title = []
            for idx,record in enumerate(playlog):
                music_chart = await self.data.static.get_music_chart(version, record.musicId, record.level)
                if music_chart:
                    difficultyNum=music_chart.level
                    artist=music_chart.artist
                    title=music_chart.title
                    (jacket, ext) = path.splitext(music_chart.jacketPath)
                    jacket += ".png"
                else:
                    difficultyNum=0
                    artist="unknown"
                    title="musicid: " + str(record.musicId)
                    jacket = "unknown.png"

                # Check if this song is a favorite so we can populate the add/remove button
                is_favorite = await self.data.item.is_favorite(user_id, version, record.musicId)

                playlog_with_title.append({
                    # Values for the actual readable results
                    "raw": record,
                    "title": title,
                    "difficultyNum": difficultyNum,
                    "artist": artist,
                    "jacket": jacket,
                    # Values used solely for favorite updates
                    "idx": idx,
                    "musicId": record.musicId,
                    "isFav": is_favorite
                })
            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=user_id,
                playlog=playlog_with_title,
                playlog_count=playlog_count,
                cur_version=version,
                cur_version_name=ChuniConstants.game_ver_to_string(version)
            ), media_type="text/html; charset=utf-8")
        else:
            return RedirectResponse("/gate/", 303)

    async def render_GET_favorites(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_favorites.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.chunithm_version < 0:
                return RedirectResponse("/game/chuni/", 303)

            user_id = usr_sesh.user_id
            version = usr_sesh.chunithm_version
            favorites = await self.data.item.get_all_favorites(user_id, version, 1)
            favorites_count = len(favorites)
            favorites_with_title = []
            favorites_by_genre = dict()
            for idx,favorite in enumerate(favorites):
                song = await self.data.static.get_song(favorite.favId)
                if song:
                    # we likely got multiple results - one for each chart. Just use the first
                    artist=song.artist
                    title=song.title
                    genre=song.genre
                    (jacket, ext) = path.splitext(song.jacketPath)
                    jacket += ".png"
                else:
                    artist="unknown"
                    title="musicid: " + str(favorite.favId)
                    genre="unknown"
                    jacket = "unknown.png"

                # add a new collection for the genre if this is our first time seeing it
                if genre not in favorites_by_genre:
                    favorites_by_genre[genre] = []

                # add the song to the appropriate genre collection
                favorites_by_genre[genre].append({
                    "idx": idx,
                    "title": title,
                    "artist": artist,
                    "jacket": jacket,
                    "favId": favorite.favId
                })

            # Sort favorites by title before rendering the page
            for g in favorites_by_genre:
                favorites_by_genre[g].sort(key=lambda x: x["title"].lower())

            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=user_id,
                favorites_by_genre=favorites_by_genre,
                favorites_count=favorites_count,
                cur_version=version,
                cur_version_name=ChuniConstants.game_ver_to_string(version)
            ), media_type="text/html; charset=utf-8")
        else:
            return RedirectResponse("/gate/", 303)

    async def get_available_map_icons(self, version: int, profile: Row) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_map_icons(version)
        if rows is None:
            return (items, 0) # can only happen with old db

        force_unlocked = self.game_cfg.mods.forced_item_unlocks("map_icons")

        user_map_icons = []
        if not force_unlocked:
            user_map_icons = await self.data.item.get_items(profile.user, ItemKind.MAP_ICON.value)
            user_map_icons = [icon["itemId"] for icon in user_map_icons] + [profile.mapIconId]

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["mapIconId"] in user_map_icons:
                item = dict()
                item["id"] = row["mapIconId"]
                item["name"] = row["name"]
                item["iconPath"] = path.splitext(row["iconPath"])[0] + ".png"
                items[row["mapIconId"]] = item
                 
        return (items, len(rows))

    async def get_available_system_voices(self, version: int, profile: Row) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_system_voices(version)
        if rows is None:
            return (items, 0) # can only happen with old db
        
        force_unlocked = self.game_cfg.mods.forced_item_unlocks("system_voices")

        user_system_voices = []
        if not force_unlocked:
            user_system_voices = await self.data.item.get_items(profile.user, ItemKind.SYSTEM_VOICE.value)
            user_system_voices = [icon["itemId"] for icon in user_system_voices] + [profile.voiceId]

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["voiceId"] in user_system_voices:
                item = dict()
                item["id"] = row["voiceId"]
                item["name"] = row["name"]
                item["imagePath"] = path.splitext(row["imagePath"])[0] + ".png"
                items[row["voiceId"]] = item
                 
        return (items, len(rows))

    async def get_available_nameplates(self, version: int, profile: Row) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_nameplates(version)
        if rows is None:
            return (items, 0) # can only happen with old db

        force_unlocked = self.game_cfg.mods.forced_item_unlocks("nameplates")

        user_nameplates = []
        if not force_unlocked:
            user_nameplates = await self.data.item.get_items(profile.user, ItemKind.NAMEPLATE.value)
            user_nameplates = [item["itemId"] for item in user_nameplates] + [profile.nameplateId]

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["nameplateId"] in user_nameplates:
                item = dict()
                item["id"] = row["nameplateId"]
                item["name"] = row["name"]
                item["texturePath"] = path.splitext(row["texturePath"])[0] + ".png"
                items[row["nameplateId"]] = item
                 
        return (items, len(rows))

    async def get_available_trophies(self, version: int, profile: Row) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_trophies(version)
        if rows is None:
            return (items, 0) # can only happen with old db
            
        force_unlocked = self.game_cfg.mods.forced_item_unlocks("trophies")

        user_trophies = []
        if not force_unlocked:
            user_trophies = await self.data.item.get_items(profile.user, ItemKind.TROPHY.value)
            user_trophies = [item["itemId"] for item in user_trophies] + [profile.trophyId]

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["trophyId"] in user_trophies:
                item = dict()
                item["id"] = row["trophyId"]
                item["name"] = row["name"]
                item["rarity"] = row["rareType"]
                items[row["trophyId"]] = item
                 
        return (items, len(rows))

    async def get_available_characters(self, version: int, profile: Row) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_characters(version)
        if rows is None:
            return (items, 0) # can only happen with old db
            
        force_unlocked = self.game_cfg.mods.forced_item_unlocks("character_icons")
            
        user_characters = []
        if not force_unlocked:
            user_characters = await self.data.item.get_characters(profile.user)
            user_characters = [chara["characterId"] for chara in user_characters] + [profile.characterId, profile.charaIllustId]

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["characterId"] in user_characters:
                item = dict()
                item["id"] = row["characterId"]
                item["name"] = row["name"]
                item["iconPath"] = path.splitext(row["imagePath3"])[0] + ".png"
                items[row["characterId"]] = item
                 
        return (items, len(rows))   

    async def get_available_avatar_items(self, version: int, category: AvatarCategory, user_unlocked_items: List[int]) -> (List[dict], int):
        items = dict()
        rows = await self.data.static.get_avatar_items(version, category.value)
        if rows is None:
            return (items, 0) # can only happen with old db

        force_unlocked = self.game_cfg.mods.forced_item_unlocks("avatar_accessories")

        for row in rows:
            if force_unlocked or row["defaultHave"] or row["avatarAccessoryId"] in user_unlocked_items:
                item = dict()
                item["id"] = row["avatarAccessoryId"]
                item["name"] = row["name"]
                item["iconPath"] = path.splitext(row["iconPath"])[0] + ".png"
                item["texturePath"] = path.splitext(row["texturePath"])[0] + ".png"
                items[row["avatarAccessoryId"]] = item
                 
        return (items, len(rows))

    async def render_GET_userbox(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_userbox.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.chunithm_version < 0:
                return RedirectResponse("/game/chuni/", 303)

            user_id = usr_sesh.user_id
            version = usr_sesh.chunithm_version

            # Get the user profile so we know how the userbox is currently configured
            profile = await self.data.profile.get_profile_data(user_id, version)

            # Build up lists of available userbox components
            nameplates, total_nameplates = await self.get_available_nameplates(version, profile)
            trophies, total_trophies = await self.get_available_trophies(version, profile)
            characters, total_characters = await self.get_available_characters(version, profile)

            # Get the user's team
            team_name = "ARTEMiS"
            if profile["teamId"]:
                team = await self.data.profile.get_team_by_id(profile["teamId"])
                team_name = team["teamName"]
            # Figure out the rating color we should use (rank maps to the stylesheet)
            rating = profile.playerRating / 100;
            rating_rank = 0
            if rating >= 16:
                rating_rank = 8
            elif rating >= 15.25:
                rating_rank = 7
            elif rating >= 14.5:
                rating_rank = 6
            elif rating >= 13.25:
                rating_rank = 5
            elif rating >= 12:
                rating_rank = 4
            elif rating >= 10:
                rating_rank = 3
            elif rating >= 7:
                rating_rank = 2
            elif rating >= 4:
                rating_rank = 1

            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=user_id,
                cur_version=version,
                cur_version_name=ChuniConstants.game_ver_to_string(version),
                profile=profile,
                team_name=team_name,
                rating_rank=rating_rank,
                nameplates=nameplates,
                trophies=trophies,
                characters=characters,
                total_nameplates=total_nameplates,
                total_trophies=total_trophies,
                total_characters=total_characters
            ), media_type="text/html; charset=utf-8")            
        else:
            return RedirectResponse("/gate/", 303)

    async def render_GET_avatar(self, request: Request) -> bytes:
        template = self.environment.get_template(
            "titles/chuni/templates/chuni_avatar.jinja"
        )
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            if usr_sesh.chunithm_version < 11:
                # Avatar configuration only for NEW!! and newer
                return RedirectResponse("/game/chuni/", 303)

            user_id = usr_sesh.user_id
            version = usr_sesh.chunithm_version

            # Get the user profile so we know what avatar items are currently in use
            profile = await self.data.profile.get_profile_data(user_id, version)
            # Get all the user avatar accessories so we know what to populate
            user_accessories = await self.data.item.get_items(user_id, ItemKind.AVATAR_ACCESSORY.value)
            user_accessories = [item["itemId"] for item in user_accessories] + \
                               [profile.avatarBack, profile.avatarItem, profile.avatarWear, \
                                profile.avatarFront, profile.avatarSkin, profile.avatarHead, profile.avatarFace]

            # Build up available list of items for each avatar category
            wears, total_wears = await self.get_available_avatar_items(version, AvatarCategory.WEAR, user_accessories)
            faces, total_faces = await self.get_available_avatar_items(version, AvatarCategory.FACE, user_accessories)
            heads, total_heads = await self.get_available_avatar_items(version, AvatarCategory.HEAD, user_accessories)
            skins, total_skins = await self.get_available_avatar_items(version, AvatarCategory.SKIN, user_accessories)
            items, total_items = await self.get_available_avatar_items(version, AvatarCategory.ITEM, user_accessories)
            fronts, total_fronts = await self.get_available_avatar_items(version, AvatarCategory.FRONT, user_accessories)
            backs, total_backs = await self.get_available_avatar_items(version, AvatarCategory.BACK, user_accessories)

            return Response(template.render(
                title=f"{self.core_config.server.name} | {self.nav_name}",
                game_list=self.environment.globals["game_list"],
                sesh=vars(usr_sesh),
                user_id=user_id,
                cur_version=version,
                cur_version_name=ChuniConstants.game_ver_to_string(version),
                profile=profile,
                wears=wears,
                faces=faces,
                heads=heads,
                skins=skins,
                items=items,
                fronts=fronts,
                backs=backs,
                total_wears=total_wears,
                total_faces=total_faces,
                total_heads=total_heads,
                total_skins=total_skins,
                total_items=total_items,
                total_fronts=total_fronts,
                total_backs=total_backs
            ), media_type="text/html; charset=utf-8")
        else:
            return RedirectResponse("/gate/", 303)

    async def update_map_icon(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_map_icon: str = form_data.get("id")
        
        if not new_map_icon:
            return RedirectResponse("/gate/?e=4", 303)

        if not await self.data.profile.update_map_icon(usr_sesh.user_id, usr_sesh.chunithm_version, new_map_icon):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/chuni/", 303)

    async def update_system_voice(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_system_voice: str = form_data.get("id")
        
        if not new_system_voice:
            return RedirectResponse("/gate/?e=4", 303)

        if not await self.data.profile.update_system_voice(usr_sesh.user_id, usr_sesh.chunithm_version, new_system_voice):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/chuni/", 303)

    async def update_userbox(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_nameplate: str = form_data.get("nameplate")
        new_trophy: str = form_data.get("trophy")
        new_character: str = form_data.get("character")
        
        if not new_nameplate or \
           not new_trophy or \
           not new_character:
            return RedirectResponse("/game/chuni/userbox?e=4", 303)

        if not await self.data.profile.update_userbox(usr_sesh.user_id, usr_sesh.chunithm_version, new_nameplate, new_trophy, new_character):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/chuni/userbox", 303)

    async def update_avatar(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_wear: str = form_data.get("wear")
        new_face: str = form_data.get("face")
        new_head: str = form_data.get("head")
        new_skin: str = form_data.get("skin")
        new_item: str = form_data.get("item")
        new_front: str = form_data.get("front")
        new_back: str = form_data.get("back")
        
        if not new_wear or \
           not new_face or \
           not new_head or \
           not new_skin or \
           not new_item or \
           not new_front or \
           not new_back:
            return RedirectResponse("/game/chuni/avatar?e=4", 303)

        if not await self.data.profile.update_avatar(usr_sesh.user_id, usr_sesh.chunithm_version, new_wear, new_face, new_head, new_skin, new_item, new_front, new_back):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/chuni/avatar", 303)


    async def update_name(self, request: Request) -> bytes:
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse("/gate/", 303)

        form_data = await request.form()
        new_name: str  = form_data.get("new_name")
        new_name_full = ""

        if not new_name:
            return RedirectResponse("/gate/?e=4", 303)

        if len(new_name) > 8:
            return RedirectResponse("/gate/?e=8", 303)

        for x in new_name: # FIXME: This will let some invalid characters through atm
            o = ord(x)
            try:
                if o == 0x20:
                    new_name_full += chr(0x3000)
                elif o < 0x7F and o > 0x20:
                    new_name_full += chr(o + 0xFEE0)
                elif o <= 0x7F:
                    self.logger.warning(f"Invalid ascii character {o:02X}")
                    return RedirectResponse("/gate/?e=4", 303)
                else:
                    new_name_full += x

            except Exception as e:
                self.logger.error(f"Something went wrong parsing character {o:04X} - {e}")
                return RedirectResponse("/gate/?e=4", 303)

        if not await self.data.profile.update_name(usr_sesh.user_id, new_name_full):
            return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse("/game/chuni/?s=1", 303)

    async def update_favorite_music(self, request: Request, retPage: str):
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            return RedirectResponse(retPage, 303)

        user_id = usr_sesh.user_id
        version = usr_sesh.chunithm_version
        form_data = await request.form()
        music_id: str = form_data.get("musicId")
        isAdd: int = int(form_data.get("isAdd"))

        if isAdd:
            if await self.data.item.put_favorite_music(user_id, version, music_id) == None:
                return RedirectResponse("/gate/?e=999", 303)
        else:
            if await self.data.item.delete_favorite_music(user_id, version, music_id) == None:
                return RedirectResponse("/gate/?e=999", 303)

        return RedirectResponse(retPage, 303)

    async def update_favorite_music_playlog(self, request: Request):
        return await self.update_favorite_music(request, "/game/chuni/playlog")
    
    async def update_favorite_music_favorites(self, request: Request):
        return await self.update_favorite_music(request, "/game/chuni/favorites")    

    async def version_change(self, request: Request):
        usr_sesh = self.validate_session(request)
        if not usr_sesh:
            usr_sesh = UserSession()

        if usr_sesh.user_id > 0:
            form_data = await request.form()
            chunithm_version = form_data.get("version")
            self.logger.debug(f"version change to: {chunithm_version}")
            if(chunithm_version.isdigit()):
                usr_sesh.chunithm_version=int(chunithm_version)
                encoded_sesh = self.encode_session(usr_sesh)
                self.logger.debug(f"Created session with JWT {encoded_sesh}")
                resp = RedirectResponse("/game/chuni/", 303)
                resp.set_cookie("ARTEMIS_SESH", encoded_sesh)
            return resp
        else:
            return RedirectResponse("/gate/", 303)
