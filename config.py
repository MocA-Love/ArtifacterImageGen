import json


class Config(object):
    SCORE_MAP = {
        "ATTACK": "攻撃力",
        "HP": "HP",
        "DEFENSE": "防御力",
        "EFFICIENCY": "元素チャージ効率",
        "ELEMENT": "元素熟知",
    }

    ELEMENT_MAP = {
        "Pyro": "炎元素ダメージ",
        "Electro": "雷元素ダメージ",
        "Hydro": "水元素ダメージ",
        "Dendro": "草元素ダメージ",
        "Anemo": "風元素ダメージ",
        "Geo": "岩元素ダメージ",
        "Cryo": "氷元素ダメージ"
    }

    def __init__(self):
        pass

    def read_json(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data

    def write_json(self, data, path):
        with open(path, mode="w", encoding="utf-8") as f:
            json.dump(data, f)
