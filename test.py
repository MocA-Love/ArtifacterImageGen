import asyncio

from gen import Generator


async def main():
    UID = "847902683"

    client = Generator()
    await client.initialize()

    player_data = await client.client.fetch_showcase(UID)

    if player_data.player:
        player = player_data.player
        print(f"{player.nickname} : 冒険ランク{player.level}")

    if player_data.characters:
        characters = {f"{v.name} Lv.{v.level}": v for v in player_data.characters}
        print("\n".join(list(characters)))

    score_types = {
        "攻撃力": "ATTACK",
        "防御力": "DEFENSE",
        "HP": "HP",
        "元素チャージ効率": "EFFICIENCY",
        "元素熟知": "ELEMENT"
    }

    score_type = "攻撃力"

    #print(characters[list(characters)[0]])

    client.generation(characters[list(characters)[0]], score_types[score_type], None)

    # アセットの更新
    #await client.update_assets()

    await client.client.close()

if __name__ == "__main__":
    asyncio.run(main())
