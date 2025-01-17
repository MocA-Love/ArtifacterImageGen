import json


class PropDetail:
    def __init__(self, depotId: int, groupId: int, propValue: float):
        self.depotId = depotId
        self.groupId = groupId
        self.propValue = propValue


class Config(object):
    RELIQUARY_AFFIX_DATA = "https://raw.githubusercontent.com/Sycamore0/GenshinData/main/ExcelBinOutput/ReliquaryAffixExcelConfigData.json"
    RELIQUARY_AFFIX_DATA_2 = "https://gitlab.com/YuukiPS/GC-Resources/-/raw/5.0/Resources/ExcelBinOutput/ReliquaryAffixExcelConfigData.json"

    SCORE_MAP = {
        "ATTACK": "攻撃力",
        "HP": "HP",
        "DEFENSE": "防御力",
        "EFFICIENCY": "元素チャージ効率",
        "ELEMENT": "元素熟知",
    }

    ELEMENT_MAP = {
        "PYRO": "炎元素ダメージ",
        "ELECTRO": "雷元素ダメージ",
        "HYDRO": "水元素ダメージ",
        "DENDRO": "草元素ダメージ",
        "ANEMO": "風元素ダメージ",
        "GEO": "岩元素ダメージ",
        "CRYO": "氷元素ダメージ",
    }

    MAIN_STATS_PROPS = [
        "FIGHT_PROP_ELEMENT_MASTERY",
        "FIGHT_PROP_HP",
        "FIGHT_PROP_ATTACK",
        "FIGHT_PROP_DEFENSE",
    ]
    SCORE_MODIFIERS = {"FIGHT_PROP_CRITICAL": 2, "FIGHT_PROP_CRITICAL_HURT": 1}
    PERCENT_STATS = {
        "HP": "FIGHT_PROP_HP_PERCENT",
        "ATTACK": "FIGHT_PROP_ATTACK_PERCENT",
        "DEFENSE": "FIGHT_PROP_DEFENSE_PERCENT",
        "EFFICIENCY": "FIGHT_PROP_CHARGE_EFFICIENCY",
        "ELEMENT": "FIGHT_PROP_ELEMENT_MASTERY",
    }

    def __init__(self):
        pass

    def read_json(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data

    def write_json(self, data, path):
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
