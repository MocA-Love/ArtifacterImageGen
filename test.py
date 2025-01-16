import asyncio

from Generator import CynoGenerator


async def main():
    UID = "847902683"

    client = CynoGenerator(cwd=".")

    player_data = await client.client.fetch_user_by_uid(UID)

    if player_data.characters:
        characters = {v.name+" Lv." +
                      str(v.level): v for v in player_data.characters}
        print(characters.keys())

    score_types = {"攻撃力": "ATTACK", "防御力": "DEFENSE",
                   "HP": "HP", "元素チャージ効率": "EFFICIENCY", "元素熟知": "ELEMENT"}

    score_type = "攻撃力"

    # print(player_data)

    client.generation(characters[list(characters)[0]], score_types[score_type], None)

    client.client.__http.close()



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
