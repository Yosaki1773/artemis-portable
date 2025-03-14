from typing import Optional
from os import walk, path
import xml.etree.ElementTree as ET
from read import BaseReader
from PIL import Image

from core.config import CoreConfig
from titles.chuni.database import ChuniData
from titles.chuni.const import ChuniConstants
from titles.chuni.schema.static import music as MusicTable


class ChuniReader(BaseReader):
    def __init__(
        self,
        config: CoreConfig,
        version: int,
        bin_dir: Optional[str],
        opt_dir: Optional[str],
        extra: Optional[str],
    ) -> None:
        super().__init__(config, version, bin_dir, opt_dir, extra)
        self.data = ChuniData(config)

        try:
            self.logger.info(
                f"Start importer for {ChuniConstants.game_ver_to_string(version)}"
            )
        except IndexError:
            self.logger.error(f"Invalid chunithm version {version}")
            exit(1)

    async def read(self) -> None:
        data_dirs = []
        if self.bin_dir is not None:
            data_dirs += self.get_data_directories(self.bin_dir)

        if self.opt_dir is not None:
            data_dirs += self.get_data_directories(self.opt_dir)
        
        we_diff = "4"
        if self.version >= ChuniConstants.VER_CHUNITHM_NEW:
            we_diff = "5"

        # character images could be stored anywhere across all the data dirs. Map them first
        self.logger.info(f"Mapping DDS image files...")
        dds_images = dict()
        for dir in data_dirs:
            self.map_dds_images(dds_images, f"{dir}/ddsImage")

        for dir in data_dirs:
            self.logger.info(f"Read from {dir}")
            await self.read_events(f"{dir}/event")
            await self.read_music(f"{dir}/music", we_diff)
            await self.read_charges(f"{dir}/chargeItem")
            await self.read_avatar(f"{dir}/avatarAccessory")
            await self.read_login_bonus(f"{dir}/")
            await self.read_nameplate(f"{dir}/namePlate")
            await self.read_trophy(f"{dir}/trophy")
            await self.read_character(f"{dir}/chara", dds_images)
            await self.read_map_icon(f"{dir}/mapIcon")
            await self.read_system_voice(f"{dir}/systemVoice")

    async def read_login_bonus(self, root_dir: str) -> None:
        for root, dirs, files in walk(f"{root_dir}loginBonusPreset"):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/LoginBonusPreset.xml"):
                    with open(f"{root}/{dir}/LoginBonusPreset.xml", "r", encoding="utf-8") as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False

                    result = await self.data.static.put_login_bonus_preset(
                        self.version, id, name, is_enabled
                    )

                    if result is not None:
                        self.logger.info(f"Inserted login bonus preset {id}")
                    else:
                        self.logger.warning(f"Failed to insert login bonus preset {id}")

                    for bonus in xml_root.find("infos").findall("LoginBonusDataInfo"):
                        for name in bonus.findall("loginBonusName"):
                            bonus_id = name.find("id").text
                            bonus_name = name.find("str").text

                        if path.exists(
                            f"{root_dir}/loginBonus/loginBonus{bonus_id}/LoginBonus.xml"
                        ):
                            with open(
                                f"{root_dir}/loginBonus/loginBonus{bonus_id}/LoginBonus.xml",
                                "rb",
                            ) as fp:
                                bytedata = fp.read()
                                strdata = bytedata.decode("UTF-8")

                                bonus_root = ET.fromstring(strdata)

                                for present in bonus_root.findall("present"):
                                    present_id = present.find("id").text
                                    present_name = present.find("str").text

                                item_num = int(bonus_root.find("itemNum").text)
                                need_login_day_count = int(
                                    bonus_root.find("needLoginDayCount").text
                                )
                                login_bonus_category_type = int(
                                    bonus_root.find("loginBonusCategoryType").text
                                )

                                result = await self.data.static.put_login_bonus(
                                    self.version,
                                    id,
                                    bonus_id,
                                    bonus_name,
                                    present_id,
                                    present_name,
                                    item_num,
                                    need_login_day_count,
                                    login_bonus_category_type,
                                )

                                if result is not None:
                                    self.logger.info(f"Inserted login bonus {bonus_id}")
                                else:
                                    self.logger.warning(
                                        f"Failed to insert login bonus {bonus_id}"
                                    )

    async def read_events(self, evt_dir: str) -> None:
        for root, dirs, files in walk(evt_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/Event.xml"):
                    with open(f"{root}/{dir}/Event.xml", "r", encoding="utf-8") as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    for substances in xml_root.findall("substances"):
                        event_type = substances.find("type").text

                    result = await self.data.static.put_event(
                        self.version, id, event_type, name
                    )
                    if result is not None:
                        self.logger.info(f"Inserted event {id}")
                    else:
                        self.logger.warning(f"Failed to insert event {id}")

    async def read_music(self, music_dir: str, we_diff: str = "4") -> None:
        max_title_len = MusicTable.columns["title"].type.length
        max_artist_len = MusicTable.columns["artist"].type.length

        for root, dirs, files in walk(music_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/Music.xml"):
                    with open(f"{root}/{dir}/Music.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        song_id = name.find("id").text
                        title = name.find("str").text
                        if len(title) > max_title_len:
                            self.logger.warning(f"Truncating music {song_id} song title")
                            title = title[:max_title_len]

                    for artistName in xml_root.findall("artistName"):
                        artist = artistName.find("str").text
                        if len(artist) > max_artist_len:
                            self.logger.warning(f"Truncating music {song_id} artist name")
                            artist = artist[:max_artist_len]

                    for genreNames in xml_root.findall("genreNames"):
                        for list_ in genreNames.findall("list"):
                            for StringID in list_.findall("StringID"):
                                genre = StringID.find("str").text

                    for jaketFile in xml_root.findall("jaketFile"):  # nice typo, SEGA
                        jacket_path = jaketFile.find("path").text
                        # Save off image for use in frontend
                        self.copy_image(jacket_path, f"{root}/{dir}", "titles/chuni/img/jacket/")

                    for fumens in xml_root.findall("fumens"):
                        for MusicFumenData in fumens.findall("MusicFumenData"):
                            fumen_path = MusicFumenData.find("file").find("path")

                            if fumen_path is not None:
                                chart_type = MusicFumenData.find("type")
                                chart_id = chart_type.find("id").text
                                chart_diff = chart_type.find("str").text
                                if chart_diff == "WorldsEnd" and chart_id == we_diff: # 4 in SDBT, 5 in SDHD
                                    level = float(xml_root.find("starDifType").text)
                                    we_chara = (
                                        xml_root.find("worldsEndTagName")
                                        .find("str")
                                        .text
                                    )
                                else:
                                    level = float(
                                        f"{MusicFumenData.find('level').text}.{MusicFumenData.find('levelDecimal').text}"
                                    )
                                    we_chara = None

                                result = await self.data.static.put_music(
                                    self.version,
                                    song_id,
                                    chart_id,
                                    title,
                                    artist,
                                    level,
                                    genre,
                                    jacket_path,
                                    we_chara,
                                )

                                if result is not None:
                                    self.logger.info(
                                        f"Inserted music {song_id} chart {chart_id}"
                                    )
                                else:
                                    self.logger.warning(
                                        f"Failed to insert music {song_id} chart {chart_id}"
                                    )

    async def read_charges(self, charge_dir: str) -> None:
        for root, dirs, files in walk(charge_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/ChargeItem.xml"):
                    with open(f"{root}/{dir}/ChargeItem.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    expirationDays = xml_root.find("expirationDays").text
                    consumeType = xml_root.find("consumeType").text
                    sellingAppeal = bool(xml_root.find("sellingAppeal").text)

                    result = await self.data.static.put_charge(
                        self.version,
                        id,
                        name,
                        expirationDays,
                        consumeType,
                        sellingAppeal,
                    )

                    if result is not None:
                        self.logger.info(f"Inserted charge {id}")
                    else:
                        self.logger.warning(f"Failed to insert charge {id}")

    async def read_avatar(self, avatar_dir: str) -> None:
        for root, dirs, files in walk(avatar_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/AvatarAccessory.xml"):
                    with open(f"{root}/{dir}/AvatarAccessory.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    sortName = xml_root.find("sortName").text
                    category = xml_root.find("category").text
                    defaultHave = xml_root.find("defaultHave").text == 'true'
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False
                    
                    for image in xml_root.findall("image"):
                        iconPath = image.find("path").text
                        self.copy_image(iconPath, f"{root}/{dir}", "titles/chuni/img/avatar/")
                    for texture in xml_root.findall("texture"):
                        texturePath = texture.find("path").text
                        self.copy_image(texturePath, f"{root}/{dir}", "titles/chuni/img/avatar/")

                    result = await self.data.static.put_avatar(
                        self.version, id, name, category, iconPath, texturePath, is_enabled, defaultHave, sortName
                    )

                    if result is not None:
                        self.logger.info(f"Inserted avatarAccessory {id}")
                    else:
                        self.logger.warning(f"Failed to insert avatarAccessory {id}")

    async def read_nameplate(self, nameplate_dir: str) -> None:
        for root, dirs, files in walk(nameplate_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/NamePlate.xml"):
                    with open(f"{root}/{dir}/NamePlate.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    sortName = xml_root.find("sortName").text
                    defaultHave = xml_root.find("defaultHave").text == 'true'
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False
                    
                    for image in xml_root.findall("image"):
                        texturePath = image.find("path").text
                        self.copy_image(texturePath, f"{root}/{dir}", "titles/chuni/img/nameplate/")

                    result = await self.data.static.put_nameplate(
                        self.version, id, name, texturePath, is_enabled, defaultHave, sortName
                    )

                    if result is not None:
                        self.logger.info(f"Inserted nameplate {id}")
                    else:
                        self.logger.warning(f"Failed to insert nameplate {id}")

    async def read_trophy(self, trophy_dir: str) -> None:
        for root, dirs, files in walk(trophy_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/Trophy.xml"):
                    with open(f"{root}/{dir}/Trophy.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    rareType = xml_root.find("rareType").text
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False
                    defaultHave = xml_root.find("defaultHave").text == 'true'

                    result = await self.data.static.put_trophy(
                        self.version, id, name, rareType, is_enabled, defaultHave
                    )

                    if result is not None:
                        self.logger.info(f"Inserted trophy {id}")
                    else:
                        self.logger.warning(f"Failed to insert trophy {id}")

    async def read_character(self, chara_dir: str, dds_images: dict) -> None:
        for root, dirs, files in walk(chara_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/Chara.xml"):
                    with open(f"{root}/{dir}/Chara.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    sortName = xml_root.find("sortName").text
                    for work in xml_root.findall("works"):
                        worksName = work.find("str").text
                    rareType = xml_root.find("rareType").text
                    defaultHave = xml_root.find("defaultHave").text == 'true'
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False
                    
                    # character images are not stored alongside
                    for image in xml_root.findall("defaultImages"):
                        imageKey = image.find("str").text
                    if imageKey in dds_images.keys():
                        (imageDir, imagePaths) = dds_images[imageKey]
                        imagePath1 = imagePaths[0] if len(imagePaths) > 0 else ""
                        imagePath2 = imagePaths[1] if len(imagePaths) > 1 else ""
                        imagePath3 = imagePaths[2] if len(imagePaths) > 2 else ""
                        # @note the third image is the image needed for the user box ui
                        if imagePath3:
                            self.copy_image(imagePath3, imageDir, "titles/chuni/img/character/")
                        else:
                            self.logger.warning(f"Character {id} only has {len(imagePaths)} images. Expected 3")                        
                    else:
                        self.logger.warning(f"Unable to location character {id} images")

                    result = await self.data.static.put_character(
                        self.version, id, name, sortName, worksName, rareType, imagePath1, imagePath2, imagePath3, is_enabled, defaultHave
                    )

                    if result is not None:
                        self.logger.info(f"Inserted character {id}")
                    else:
                        self.logger.warning(f"Failed to insert character {id}")
    
    async def read_map_icon(self, mapicon_dir: str) -> None:
        for root, dirs, files in walk(mapicon_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/MapIcon.xml"):
                    with open(f"{root}/{dir}/MapIcon.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    sortName = xml_root.find("sortName").text
                    for image in xml_root.findall("image"):
                        iconPath = image.find("path").text
                        self.copy_image(iconPath, f"{root}/{dir}", "titles/chuni/img/mapIcon/")
                    defaultHave = xml_root.find("defaultHave").text == 'true'
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False

                    result = await self.data.static.put_map_icon(
                        self.version, id, name, sortName, iconPath, is_enabled, defaultHave
                    )

                    if result is not None:
                        self.logger.info(f"Inserted map icon {id}")
                    else:
                        self.logger.warning(f"Failed to map icon {id}")

    async def read_system_voice(self, voice_dir: str) -> None:
        for root, dirs, files in walk(voice_dir):
            for dir in dirs:
                if path.exists(f"{root}/{dir}/SystemVoice.xml"):
                    with open(f"{root}/{dir}/SystemVoice.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        id = name.find("id").text
                        name = name.find("str").text
                    sortName = xml_root.find("sortName").text
                    for image in xml_root.findall("image"):
                        imagePath = image.find("path").text
                        self.copy_image(imagePath, f"{root}/{dir}", "titles/chuni/img/systemVoice/")
                    defaultHave = xml_root.find("defaultHave").text == 'true'
                    disableFlag = xml_root.find("disableFlag") # may not exist in older data
                    is_enabled = True if (disableFlag is None or disableFlag.text == "false") else False
                    
                    result = await self.data.static.put_system_voice(
                        self.version, id, name, sortName, imagePath, is_enabled, defaultHave
                    )

                    if result is not None:
                        self.logger.info(f"Inserted system voice {id}")
                    else:
                        self.logger.warning(f"Failed to system voice {id}")

    def copy_image(self, filename: str, src_dir: str, dst_dir: str) -> None:
        # Convert the image to png so we can easily display it in the frontend
        file_src = path.join(src_dir, filename)
        (basename, ext) = path.splitext(filename)
        file_dst = path.join(dst_dir, basename) + ".png"

        if path.exists(file_src) and not path.exists(file_dst):
            try:
                im = Image.open(file_src)
                im.save(file_dst)
            except Exception:
                self.logger.warning(f"Failed to convert {filename} to png")

    def map_dds_images(self, image_dict: dict, dds_dir: str) -> None:
        for root, dirs, files in walk(dds_dir):
            for dir in dirs:
                directory = f"{root}/{dir}"
                if path.exists(f"{directory}/DDSImage.xml"):
                    with open(f"{directory}/DDSImage.xml", "r", encoding='utf-8') as fp:
                        strdata = fp.read()

                    xml_root = ET.fromstring(strdata)
                    for name in xml_root.findall("name"):
                        name = name.find("str").text

                    images = []
                    i = 0
                    while xml_root.findall(f"ddsFile{i}"):
                        for ddsFile in xml_root.findall(f"ddsFile{i}"):
                            images += [ddsFile.find("path").text]
                        i += 1

                    image_dict[name] = (directory, images)