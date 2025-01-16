import os
import base64
from io import BytesIO
from collections import Counter
from typing import List

import requests
from PIL import Image, ImageFont, ImageDraw, ImageEnhance, ImageFile

from EnkaNetwork.enkanetwork import (
    EnkaNetworkAPI,
    CharacterInfo,
    CharacterSkill,
    Equipments,
    EquipmentsStats,
)

import enka

from config import Config


class CynoGenerator(Config):
    def __init__(self, cwd="./ArtifacterImageGen"):
        self.cwd = cwd
        self.rounded = False

        Config.__init__(self)

        self.subop = self.set_subop()
        self.subop2 = self.set_subop2()

        ImageFile.LOAD_TRUNCATED_IMAGES = True

        self.status_prop = self.read_json(f"{cwd}/mapping/status_prop.json")

        os.makedirs(self.cwd + "/cache", exist_ok=True)
        self.client = enka.GenshinClient(enka.gi.Language.JAPANESE)

    async def initialize(self):
        await self.client.start()

    def set_subop(self):
        subop_path = f"{self.cwd}/mapping/subop.json"

        if os.path.exists(subop_path):
            return self.read_json(subop_path)

        # なにこれ
        resp = requests.get(
            "https://raw.githubusercontent.com/Sycamore0/GenshinData/main/ExcelBinOutput/ReliquaryAffixExcelConfigData.json",
            timeout=10,
        )

        sub_stats_data = resp.json()

        result = {}
        for entry in sub_stats_data:
            prop_type = entry["propType"]
            entry_id = entry["id"]

            del entry["id"]
            del entry["propType"]

            if prop_type not in result:
                result[prop_type] = {}

            result[prop_type][entry_id] = entry

        self.write_json(result, subop_path)

        return result

    def set_subop2(self):
        subop_path = f"{self.cwd}/mapping/subop2.json"

        if os.path.exists(subop_path):
            return self.read_json(subop_path)

        # なにこれ
        resp = requests.get(
            "https://gitlab.com/YuukiPS/GC-Resources/-/raw/5.0/Resources/ExcelBinOutput/ReliquaryAffixExcelConfigData.json",
            timeout=10,
        )

        sub_stats_data = resp.json()

        result = {}
        for entry in sub_stats_data:
            prop_type = entry["propType"]
            entry_id = entry["id"]

            del entry["id"]
            del entry["propType"]

            if prop_type not in result:
                result[prop_type] = {}

            result[prop_type][entry_id] = entry

        self.write_json(result, subop_path)

        return result

    def set_artifact(self, artifact: enka.gi.Artifact, score_type: str):
        score = 0.0

        result = {
            "type": artifact.set_name,
            "Level": artifact.level,
            "rarelity": artifact.rarity,
            "filename": self.get_image(os.path.basename(artifact.icon), artifact.icon),
            "main": {
                "option": self.status_prop[artifact.main_stat.type],
            },
            "sub": [],
        }

        # ?1
        main_stat = artifact.main_stat
        if main_stat.type in self.MAIN_STATS_PROPS:
            result["main"]["value"] = int(main_stat.value)
        else:
            result["main"]["value"] = main_stat.value

        # ?2
        for sub_stat in artifact.sub_stats:
            if self.rounded:
                stat = {
                    "option": self.status_prop[sub_stat.type],
                    "value": (
                        sub_stat.value
                        if sub_stat.type not in self.MAIN_STATS_PROPS
                        else round(sub_stat.value)
                    ),
                    "values": [],
                }
            else:
                stat = {
                    "option": self.status_prop[sub_stat.type],
                    "value": sub_stat.value,
                    "values": [],
                }

            # スコア計算?
            if sub_stat.type in self.SCORE_MODIFIERS:
                score += sub_stat.value * self.SCORE_MODIFIERS[sub_stat.type]

            # 追加スコア計算?
            if sub_stat.type in self.PERCENT_STATS.values():
                if (
                    score_type in self.PERCENT_STATS
                    and sub_stat.type == self.PERCENT_STATS[score_type]
                ):
                    score += sub_stat.value
            elif (
                sub_stat.type == "FIGHT_PROP_ELEMENT_MASTERY"
                and score_type == "ELEMENT"
            ):
                score += sub_stat.value * 0.25

            # サブオプションとは?
            for i in [artifact.main_stat_id] + artifact.sub_stat_ids:
                if str(i) in self.subop[sub_stat.type].keys():
                    value = self.subop[sub_stat.type][str(i)]["propValue"]
                    if self.rounded:
                        if sub_stat.type in self.MAIN_STATS_PROPS:
                            stat["values"].append(round(value))
                        else:
                            stat["values"].append(round(value * 100, 1))
                    else:
                        if sub_stat.type in self.MAIN_STATS_PROPS:
                            stat["values"].append(value)
                        else:
                            stat["values"].append(value * 100)

            stat["values"].sort()
            result["sub"].append(stat)

        if self.rounded:
            return result, round(score, 1)
        else:
            return result, score

    def set_buff(self, c: enka.gi.Character):
        result = {}

        element_buffs = {}
        for prop_type, stat in c.stats.items():
            if prop_type == enka.gi.FightPropType.FIGHT_PROP_PHYSICAL_ADD_HURT:
                element_buffs["物理ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_FIRE_ADD_HURT:
                element_buffs["炎元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_ELEC_ADD_HURT:
                element_buffs["雷元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_WATER_ADD_HURT:
                element_buffs["水元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_GRASS_ADD_HURT:
                element_buffs["草元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_WIND_ADD_HURT:
                element_buffs["風元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_ROCK_ADD_HURT:
                element_buffs["岩元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_ICE_ADD_HURT:
                element_buffs["氷元素ダメージ"] = stat.value
            elif prop_type == enka.gi.FightPropType.FIGHT_PROP_HEAL_ADD:
                element_buffs["与える治癒効果"] = stat.value

        # 0より大きい場合のみ
        for buff_name, value in element_buffs.items():
            if value > 0:
                result[buff_name] = round(value * 100, 1)

        # 最大値を探す ← 原神の計算方法がいまいちわからないのであとで解析
        if result:
            max_value = max(result.values())
            element = self.ELEMENT_MAP[c.element.name]
            for k, v in sorted(result.items()):
                if v == max_value:
                    if k == element:
                        return k, v

            return max(result.items(), key=lambda x: x[1])

        return None, None

    def get_image(self, filename: str, url: str) -> str:
        path = f"{self.cwd}/cache/{filename}.png"
        if not os.path.exists(path):
            resp = requests.get(url, timeout=10)
            with open(path, mode="wb") as f:
                f.write(resp.content)

        return path

    def resize_image(self, filename, target_h=1200):
        # なぜこのサイズにこだわっているかは後で考える
        image = Image.open(filename)

        w, h = image.size

        # 縦横比を保ったまま、縦の長さが1200ピクセルになるようにリサイズする
        target_w = int(w * target_h / h)
        resized_image = image.resize((target_w, target_h))

        # 透明な背景の新しい画像を作成する
        background = Image.new("RGBA", (2048, 1200), (0, 0, 0, 0))

        # リサイズした画像を中央に配置する
        x, y = int((2048 - target_w) / 2), int((1200 - target_h) / 2)
        background.paste(resized_image, (x, y))

        background.save(filename, "png")

    def generation(
        self,
        character: enka.gi.Character,
        score_type: str,
        background_path: str,
        rounded=False,
    ):
        # print("character", character)
        self.rounded = rounded

        element = character.element.name

        # CharacterData :dict = data.get("Character")
        CharacterName: str = character.name
        CharacterConstellations: int = character.constellations_unlocked
        CharacterLevel: int = character.level
        if (character.id == 10000005) or (character.id == 10000007):
            FriendShip = None
        else:
            FriendShip: int = character.friendship_level
        # CharacterStatus : CharacterStats = character.stats

        base_hp, hp, base_atk, atk, base_def, _def = 0, 0, 0, 0, 0, 0
        ms, cr, cd, er = 0, 0, 0, 0

        if True:#self.rounded:
            for prop_type, stat in character.stats.items():
                if prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_HP:
                    base_hp = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_MAX_HP:
                    hp = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_ATTACK:
                    base_atk = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CUR_ATTACK:
                    atk = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_DEFENSE:
                    base_def = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CUR_DEFENSE:
                    _def = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_ELEMENT_MASTERY:
                    ms = round(stat.value)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CRITICAL:
                    cr = round(stat.value * 100, 1)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CRITICAL_HURT:
                    cd = round(stat.value * 100, 1)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CHARGE_EFFICIENCY:
                    er = round(stat.value * 100, 1)
        else:
            for prop_type, stat in character.stats.items():
                if prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_HP:
                    base_hp = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_MAX_HP:
                    hp = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_ATTACK:
                    base_atk = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CUR_ATTACK:
                    atk = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_BASE_DEFENSE:
                    base_def = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CUR_DEFENSE:
                    _def = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_ELEMENT_MASTERY:
                    ms = stat.value
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CRITICAL:
                    cr = round(stat.value * 100, 1)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CRITICAL_HURT:
                    cd = round(stat.value * 100, 1)
                elif prop_type == enka.gi.FightPropType.FIGHT_PROP_CHARGE_EFFICIENCY:
                    er = round(stat.value * 100, 1)

        CharacterStatus: dict = {
            "HP": hp,
            "攻撃力": atk,
            "防御力": _def,
            "元素熟知": ms,
            "会心率": cr,
            "会心ダメージ": cd,
            "元素チャージ効率": er,
        }
        buff, value = self.set_buff(character)
        if buff:
            CharacterStatus[buff] = value
        CharacterBase: dict = {"HP": base_hp, "攻撃力": base_atk, "防御力": base_def}

        CharacterTalent: List[enka.gi.Talent] = character.talents

        Weapon: enka.gi.Weapon = character.weapon
        WeaponName: str = Weapon.name
        WeaponLevel: int = Weapon.level
        WeaponRank: int = Weapon.refinement
        WeaponRarity: int = Weapon.rarity
        print(Weapon.stats)
        WeaponBaseATK: int = next(
            (
                int(stat.value)
                for stat in Weapon.stats
                if stat.type == "FIGHT_PROP_BASE_ATTACK"
            ),
            None,
        )
        WeaponSubOP: list[enka.gi.Stat] = (
            Weapon.stats[1] if len(Weapon.stats) > 1 else None
        )
        WeaponSubOPKey: str = Weapon.stats[1].name if WeaponSubOP else None
        WeaponSubOPValue: int | float = Weapon.stats[1].value if WeaponSubOP else None

        ScoreData: dict = {}
        ScoreCVBasis: str = score_type
        ArtifactsData: dict = {}
        ScoreTotal = 0.0
        for e in character.artifacts:
            match e.equip_type:
                case "EQUIP_BRACER":
                    ArtifactsData["flower"], score = self.set_artifact(e, score_type)
                    ScoreData["flower"] = score
                    ScoreTotal += score
                case "EQUIP_NECKLACE":
                    ArtifactsData["wing"], score = self.set_artifact(e, score_type)
                    ScoreData["wing"] = score
                    ScoreTotal += score
                case "EQUIP_SHOES":
                    ArtifactsData["clock"], score = self.set_artifact(e, score_type)
                    ScoreData["clock"] = score
                    ScoreTotal += score
                case "EQUIP_RING":
                    ArtifactsData["cup"], score = self.set_artifact(e, score_type)
                    ScoreData["cup"] = score
                    ScoreTotal += score
                case "EQUIP_DRESS":
                    ArtifactsData["crown"], score = self.set_artifact(e, score_type)
                    ScoreData["crown"] = score
                    ScoreTotal += score
        ScoreTotal = round(ScoreTotal, 1)

        def config_font(size):
            return ImageFont.truetype(f"{self.cwd}/Assets/ja-jp.ttf", size)

        if background_path:
            if background_path.startswith("http") or background_path.startswith(
                "https"
            ):
                background = BytesIO(requests.get(background_path, timeout=10).content)
            else:
                background = background_path
            Base = Image.open(background).resize((1920, 1080)).convert("RGBA")
        else:
            Base = Image.open(f"{self.cwd}/Base/{element}.png")

        # なにこれ
        if (character.id == 10000005) or (character.id == 10000007):
            if not os.path.exists(
                self.cwd + "/cache/" + character.image.banner.filename + ".png"
            ):
                self.resize_image(
                    self.get_image(
                        character.image.banner.filename, character.image.banner.url
                    )
                )

        banner_url = character.icon.gacha
        CharacterImage = Image.open(
            self.get_image(os.path.basename(banner_url), banner_url)
        ).convert("RGBA")

        CharacterBack = Image.new("RGBA", (2048, 1024), (0, 0, 0, 0))
        x = int((2048 - CharacterImage.width) / 2)
        y = int((1024 - CharacterImage.height) / 2)
        CharacterBack.paste(CharacterImage, (x, y))
        CharacterImage = CharacterBack
        Shadow = Image.open(f"{self.cwd}/Assets/Shadow.png").resize(Base.size)
        CharacterImage = CharacterImage.crop((289, 0, 1728, 1024))
        CharacterImage = CharacterImage.resize(
            (int(CharacterImage.width * 0.75), int(CharacterImage.height * 0.75))
        )

        CharacterAvatarMask = CharacterImage.copy()

        if CharacterName in ["アルハイゼン", "ヌヴィレット"]:
            CharacterAvatarMask2 = (
                Image.open(f"{self.cwd}/Assets/Alhaitham.png")
                .convert("L")
                .resize(CharacterImage.size)
            )
        else:
            CharacterAvatarMask2 = (
                Image.open(f"{self.cwd}/Assets/CharacterMask.png")
                .convert("L")
                .resize(CharacterImage.size)
            )
        CharacterImage.putalpha(CharacterAvatarMask2)

        CharacterPaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))

        CharacterPaste.paste(CharacterImage, (-160, -45), mask=CharacterAvatarMask)
        Base = Image.alpha_composite(Base, CharacterPaste)
        Base = Image.alpha_composite(Base, Shadow)

        # 武器
        WeaponBase = (
            Image.open(self.get_image(os.path.basename(Weapon.icon), Weapon.icon))
            .convert("RGBA")
            .resize((128, 128))
        )
        WeaponPaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))

        WeaponMask = WeaponBase.copy()
        WeaponPaste.paste(WeaponBase, (1430, 50), mask=WeaponMask)

        Base = Image.alpha_composite(Base, WeaponPaste)

        WeaponRImage = Image.open(
            f"{self.cwd}/Assets/Rarelity/{WeaponRarity}.png"
        ).convert("RGBA")
        WeaponRImage = WeaponRImage.resize(
            (int(WeaponRImage.width * 0.97), int(WeaponRImage.height * 0.97))
        )
        WeaponRPaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))
        WeaponRMask = WeaponRImage.copy()

        WeaponRPaste.paste(WeaponRImage, (1422, 173), mask=WeaponRMask)
        Base = Image.alpha_composite(Base, WeaponRPaste)

        # 天賦
        TalentBase = Image.open(f"{self.cwd}/Assets/TalentBack.png")
        TalentBasePaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))
        TalentBase = TalentBase.resize(
            (int(TalentBase.width / 1.5), int(TalentBase.height / 1.5))
        )

        for i in range(3):
            TalentPaste = Image.new("RGBA", TalentBase.size, (255, 255, 255, 0))
            Talent = (
                Image.open(
                    self.get_image(
                        os.path.basename(character.talents[i].icon),
                        character.talents[i].icon,
                    )
                )
                .resize((50, 50))
                .convert("RGBA")
            )
            TalentMask = Talent.copy()
            TalentPaste.paste(
                Talent,
                (TalentPaste.width // 2 - 25, TalentPaste.height // 2 - 25),
                mask=TalentMask,
            )

            TalentObject = Image.alpha_composite(TalentBase, TalentPaste)
            TalentBasePaste.paste(TalentObject, (15, 330 + i * 105))

        Base = Image.alpha_composite(Base, TalentBasePaste)

        # 凸
        CBase = (
            Image.open(f"{self.cwd}/命の星座/{element}.png")
            .resize((90, 90))
            .convert("RGBA")
        )
        Clock = (
            Image.open(f"{self.cwd}/命の星座/{element}LOCK.png")
            .resize((90, 90))
            .convert("RGBA")
        )
        ClockMask = Clock.copy()

        CPaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))
        for c in range(1, 7):
            if c > CharacterConstellations:
                CPaste.paste(Clock, (666, -10 + c * 93), mask=ClockMask)
            else:
                CharaC = (
                    Image.open(
                        self.get_image(
                            os.path.basename(character.constellations[c - 1].icon),
                            character.constellations[c - 1].icon,
                        )
                    )
                    .convert("RGBA")
                    .resize((45, 45))
                )
                CharaCPaste = Image.new("RGBA", CBase.size, (255, 255, 255, 0))
                CharaCMask = CharaC.copy()
                CharaCPaste.paste(
                    CharaC,
                    (int(CharaCPaste.width / 2) - 25, int(CharaCPaste.height / 2) - 23),
                    mask=CharaCMask,
                )

                Cobject = Image.alpha_composite(CBase, CharaCPaste)
                CPaste.paste(Cobject, (666, -10 + c * 93))

        Base = Image.alpha_composite(Base, CPaste)
        D = ImageDraw.Draw(Base)

        D.text((30, 20), CharacterName, font=config_font(48))
        levellength = D.textlength("Lv." + str(CharacterLevel), font=config_font(25))
        D.text((35, 75), "Lv." + str(CharacterLevel), font=config_font(25))
        if FriendShip:
            friendshiplength = D.textlength(str(FriendShip), font=config_font(25))
            D.rounded_rectangle(
                (35 + levellength + 5, 74, 77 + levellength + friendshiplength, 102),
                radius=2,
                fill="black",
            )
            FriendShipIcon = Image.open(f"{self.cwd}/Assets/Love.png").convert("RGBA")
            FriendShipIcon = FriendShipIcon.resize(
                (int(FriendShipIcon.width * (24 / FriendShipIcon.height)), 24)
            )
            Fmask = FriendShipIcon.copy()
            Base.paste(FriendShipIcon, (42 + int(levellength), 76), mask=Fmask)
            D.text((73 + levellength, 74), str(FriendShip), font=config_font(25))

        D.text(
            (42, 397),
            f"Lv.{CharacterTalent[0].level}",
            font=config_font(17),
            fill="aqua" if CharacterTalent[0].level >= 10 else None,
        )
        D.text(
            (42, 502),
            f"Lv.{CharacterTalent[1].level}",
            font=config_font(17),
            fill="aqua" if CharacterTalent[1].level >= 10 else None,
        )
        D.text(
            (42, 607),
            f"Lv.{CharacterTalent[2].level}",
            font=config_font(17),
            fill="aqua" if CharacterTalent[2].level >= 10 else None,
        )

        def genbasetext(state):
            sumv = CharacterStatus[state]
            plusv = sumv - CharacterBase[state]
            basev = CharacterBase[state]
            return (
                f"+{format(plusv,',')}",
                f"{format(basev,',')}",
                D.textlength(f"+{format(plusv,',')}", font=config_font(12)),
                D.textlength(f"{format(basev,',')}", font=config_font(12)),
            )

        disper = [
            "会心率",
            "会心ダメージ",
            "攻撃パーセンテージ",
            "防御パーセンテージ",
            "HPパーセンテージ",
            "水元素ダメージ",
            "物理ダメージ",
            "風元素ダメージ",
            "岩元素ダメージ",
            "炎元素ダメージ",
            "与える治癒効果",
            "与える治療効果",
            "雷元素ダメージ",
            "氷元素ダメージ",
            "草元素ダメージ",
            "受ける治療効果",
            "元素チャージ効率",
        ]
        StateOP = (
            "HP",
            "攻撃力",
            "防御力",
            "元素熟知",
            "会心率",
            "会心ダメージ",
            "元素チャージ効率",
        )
        for k, v in CharacterStatus.items():
            if (
                k
                in [
                    "氷元素ダメージ",
                    "水元素ダメージ",
                    "岩元素ダメージ",
                    "草元素ダメージ",
                    "風元素ダメージ",
                    "炎元素ダメージ",
                    "物理ダメージ",
                    "与える治癒効果",
                    "雷元素ダメージ",
                ]
                and v == 0
            ):
                k = f"{element}元素ダメージ"
            try:
                i = StateOP.index(k)
            except:
                i = 7
                D.text((844, 67 + i * 70), k, font=config_font(26))
                opicon = Image.open(f"{self.cwd}/emotes/{k}.png").resize((40, 40))
                oppaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))
                # opmask = opicon.copy()
                oppaste.paste(opicon, (789, 65 + i * 70))
                Base = Image.alpha_composite(Base, oppaste)
                D = ImageDraw.Draw(Base)

            if k not in disper:
                statelen = D.textlength(format(v, ","), config_font(26))
                D.text(
                    (1360 - statelen, 67 + i * 70), format(v, ","), font=config_font(26)
                )
            else:
                statelen = D.textlength(f"{float(v)}%", config_font(26))
                D.text(
                    (1360 - statelen, 67 + i * 70), f"{float(v)}%", font=config_font(26)
                )

            if k in ["HP", "防御力", "攻撃力"]:
                HPpls, HPbase, HPsize, HPbsize = genbasetext(k)
                D.text(
                    (1360 - HPsize, 97 + i * 70),
                    HPpls,
                    fill=(0, 255, 0, 180),
                    font=config_font(12),
                )
                D.text(
                    (1360 - HPsize - HPbsize - 1, 97 + i * 70),
                    HPbase,
                    font=config_font(12),
                    fill=(255, 255, 255, 180),
                )

        D.text((1582, 47), WeaponName, font=config_font(26))
        wlebellen = D.textlength(f"Lv.{WeaponLevel}", font=config_font(24))
        D.rounded_rectangle(
            (1582, 80, 1582 + wlebellen + 4, 108), radius=1, fill="black"
        )
        D.text((1584, 82), f"Lv.{WeaponLevel}", font=config_font(24))

        BaseAtk = Image.open(f"{self.cwd}/emotes/基礎攻撃力.png").resize((23, 23))
        BaseAtkmask = BaseAtk.copy().convert("RGBA")
        Base.paste(BaseAtk, (1600, 120), mask=BaseAtkmask)
        D.text((1623, 120), f"基礎攻撃力  {WeaponBaseATK}", font=config_font(23))

        optionmap = {
            "攻撃パーセンテージ": "攻撃%",
            "防御パーセンテージ": "防御%",
            "元素チャージ効率": "元チャ効率",
            "HPパーセンテージ": "HP%",
        }
        if WeaponSubOPKey:
            BaseAtk = Image.open(f"{self.cwd}/emotes/{WeaponSubOPKey}.png").resize(
                (23, 23)
            )
            BaseAtkmask = BaseAtk.copy().convert("RGBA")
            Base.paste(BaseAtk, (1600, 155), mask=BaseAtkmask)

            D.text(
                (1623, 155),
                f"{optionmap.get(WeaponSubOPKey) or WeaponSubOPKey}  {str(WeaponSubOPValue)+'%' if isinstance(WeaponSubOPValue,float) else format(WeaponSubOPValue,',')}",
                font=config_font(23),
            )

        D.rounded_rectangle((1430, 45, 1470, 70), radius=1, fill="black")
        D.text((1433, 46), f"R{WeaponRank}", font=config_font(24))

        ScoreLen = D.textlength(f"{ScoreTotal}", config_font(75))
        D.text((1652 - ScoreLen // 2, 420), str(ScoreTotal), font=config_font(75))
        blen = D.textlength(f"{self.SCORE_MAP[ScoreCVBasis]}換算", font=config_font(24))
        D.text(
            (1867 - blen, 585),
            f"{self.SCORE_MAP[ScoreCVBasis]}換算",
            font=config_font(24),
        )

        if ScoreTotal >= 220:
            ScoreEv = Image.open(f"{self.cwd}/artifactGrades/SS.png")
        elif ScoreTotal >= 200:
            ScoreEv = Image.open(f"{self.cwd}/artifactGrades/S.png")
        elif ScoreTotal >= 180:
            ScoreEv = Image.open(f"{self.cwd}/artifactGrades/A.png")
        else:
            ScoreEv = Image.open(f"{self.cwd}/artifactGrades/B.png")

        ScoreEv = ScoreEv.resize((ScoreEv.width // 8, ScoreEv.height // 8))
        EvMask = ScoreEv.copy()

        Base.paste(ScoreEv, (1806, 345), mask=EvMask)

        # 聖遺物
        atftype = list()
        for i, parts in enumerate(["flower", "wing", "clock", "cup", "crown"]):
            details = ArtifactsData.get(parts)

            if not details:
                continue

            atftype.append(details["type"])
            PreviewPaste = Image.new("RGBA", Base.size, (255, 255, 255, 0))
            Preview = Image.open(details["filename"]).resize((256, 256))
            enhancer = ImageEnhance.Brightness(Preview)
            Preview = enhancer.enhance(0.6)
            Preview = Preview.resize(
                (int(Preview.width * 1.3), int(Preview.height * 1.3))
            )
            Pmask1 = Preview.copy()

            Pmask = (
                Image.open(f"{self.cwd}/Assets/ArtifactMask.png")
                .convert("L")
                .resize(Preview.size)
            )
            Preview.putalpha(Pmask)
            if parts in ["flower", "crown"]:
                PreviewPaste.paste(Preview, (-37 + 373 * i, 570), mask=Pmask1)
            elif parts in ["wing", "cup"]:
                PreviewPaste.paste(Preview, (-36 + 373 * i, 570), mask=Pmask1)
            else:
                PreviewPaste.paste(Preview, (-35 + 373 * i, 570), mask=Pmask1)
            Base = Image.alpha_composite(Base, PreviewPaste)
            D = ImageDraw.Draw(Base)

            mainop = details["main"]["option"]

            mainoplen = D.textlength(
                optionmap.get(mainop) or mainop, font=config_font(29)
            )
            D.text(
                (375 + i * 373 - int(mainoplen), 655),
                optionmap.get(mainop) or mainop,
                font=config_font(29),
            )
            MainIcon = (
                Image.open(f"{self.cwd}/emotes/{mainop}.png")
                .convert("RGBA")
                .resize((35, 35))
            )
            MainMask = MainIcon.copy()
            Base.paste(MainIcon, (340 + i * 373 - int(mainoplen), 655), mask=MainMask)

            mainv = details["main"]["value"]
            if mainop in disper:
                mainvsize = D.textlength(f"{float(mainv)}%", config_font(49))
                D.text(
                    (375 + i * 373 - mainvsize, 690),
                    f"{float(mainv)}%",
                    font=config_font(49),
                )
            else:
                mainvsize = D.textlength(format(mainv, ","), config_font(49))
                D.text(
                    (375 + i * 373 - mainvsize, 690),
                    format(mainv, ","),
                    font=config_font(49),
                )
            levlen = D.textlength(f"+{details['Level']}", config_font(21))
            D.rounded_rectangle(
                (373 + i * 373 - int(levlen), 748, 375 + i * 373, 771),
                fill="black",
                radius=2,
            )
            D.text(
                (374 + i * 373 - levlen, 749),
                f"+{details['Level']}",
                font=config_font(21),
            )

            if len(details["sub"]) == 0:
                continue

            for a, sub in enumerate(details["sub"]):
                SubOP = sub["option"]
                SubVal = sub["value"]
                SubVals = sub["values"]
                if SubOP in ["HP", "攻撃力", "防御力"]:
                    D.text(
                        (79 + 373 * i, 811 + 50 * a),
                        optionmap.get(SubOP) or SubOP,
                        font=config_font(25),
                        fill=(255, 255, 255, 190),
                    )
                else:
                    D.text(
                        (79 + 373 * i, 811 + 50 * a),
                        optionmap.get(SubOP) or SubOP,
                        font=config_font(25),
                    )
                SubIcon = Image.open(f"{self.cwd}/emotes/{SubOP}.png").resize((30, 30))
                SubMask = SubIcon.copy().convert("RGBA")
                Base.paste(SubIcon, (44 + 373 * i, 811 + 50 * a), mask=SubMask)
                if SubOP in disper:
                    SubSize = D.textlength(f"{float(SubVal)}%", config_font(25))
                    D.text(
                        (375 + i * 373 - SubSize, 811 + 50 * a),
                        f"{float(SubVal)}%",
                        font=config_font(25),
                    )
                else:
                    SubSize = D.textlength(format(SubVal, ","), config_font(25))
                    if SubOP in ["防御力", "攻撃力", "HP"]:
                        D.text(
                            (375 + i * 373 - SubSize, 811 + 50 * a),
                            format(SubVal, ","),
                            font=config_font(25),
                            fill=(255, 255, 255, 190),
                        )
                    else:
                        D.text(
                            (375 + i * 373 - SubSize, 811 + 50 * a),
                            format(SubVal, ","),
                            font=config_font(25),
                            fill=(255, 255, 255),
                        )

                if details["Level"] == 20 and details["rarelity"] == 5:
                    nobi = D.textlength(
                        "+".join(map(str, SubVals)), font=config_font(11)
                    )
                    D.text(
                        (375 + i * 373 - nobi, 840 + 50 * a),
                        "+".join(map(str, SubVals)),
                        fill=(255, 255, 255, 160),
                        font=config_font(11),
                    )

            Score = float(ScoreData[parts])
            ATFScorelen = D.textlength(str(Score), config_font(36))
            D.text(
                (380 + i * 373 - ATFScorelen, 1016), str(Score), font=config_font(36)
            )
            D.text(
                (295 + i * 373 - ATFScorelen, 1025),
                "Score",
                font=config_font(27),
                fill=(160, 160, 160),
            )

            PointRefer = {
                "total": {"SS": 220, "S": 200, "A": 180},
                "flower": {"SS": 50, "S": 45, "A": 40},
                "wing": {"SS": 50, "S": 45, "A": 40},
                "clock": {"SS": 45, "S": 40, "A": 35},
                "cup": {"SS": 45, "S": 40, "A": 37},
                "crown": {"SS": 40, "S": 35, "A": 30},
            }

            if Score >= PointRefer[parts]["SS"]:
                ScoreImage = Image.open(f"{self.cwd}/artifactGrades/SS.png")
            elif Score >= PointRefer[parts]["S"]:
                ScoreImage = Image.open(f"{self.cwd}/artifactGrades/S.png")
            elif Score >= PointRefer[parts]["A"]:
                ScoreImage = Image.open(f"{self.cwd}/artifactGrades/A.png")
            else:
                ScoreImage = Image.open(f"{self.cwd}/artifactGrades/B.png")

            ScoreImage = ScoreImage.resize(
                (ScoreImage.width // 11, ScoreImage.height // 11)
            )
            SCMask = ScoreImage.copy()

            Base.paste(ScoreImage, (85 + 373 * i, 1013), mask=SCMask)

        SetBounus = Counter([x for x in atftype if atftype.count(x) >= 2])
        for i, (n, q) in enumerate(SetBounus.items()):
            if len(SetBounus) == 2:
                D.text((1536, 243 + i * 35), n, fill=(0, 255, 0), font=config_font(23))
                D.rounded_rectangle(
                    (1818, 243 + i * 35, 1862, 266 + i * 35), 1, "black"
                )
                D.text((1835, 243 + i * 35), str(q), font=config_font(19))
            if len(SetBounus) == 1:
                D.text((1536, 263), n, fill=(0, 255, 0), font=config_font(23))
                D.rounded_rectangle((1818, 263, 1862, 288), 1, "black")
                D.text((1831, 265), str(q), font=config_font(19))

        buffer = BytesIO()
        Base.save(buffer, "png")
        if self.rounded:
            Base.save("test-round.png")
        else:
            Base.save("test.png")
        return buffer
        # return pil_to_base64(Base)


def pil_to_base64(img: Image.Image, fmt: str = "png") -> str:
    with BytesIO() as buffer:
        img.save(buffer, format=fmt)
        encoded_string = base64.b64encode(buffer.getvalue()).decode("ascii")

    return encoded_string
