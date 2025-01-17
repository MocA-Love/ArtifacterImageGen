import asyncio
import logging

import enka
import streamlit as st

from gen import Generator

logger = logging.getLogger()


async def main():
    client = Generator()
    await client.initialize()

    if "player_info" not in st.session_state:
        st.session_state.player_info = False

    params = st.query_params
    if params.get("uid"):
        queryUID = params["uid"]
    else:
        queryUID = None

    st.set_page_config(
        page_title="Build-Card Generator",
        page_icon="Assets/cyno.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
        unsafe_allow_html=True,
    )
    try:
        await on_start()
    except:
        pass
    content = """
  # Build-Card Generator
  ##### 原神のUIDからビルドカードを生成できます
  ※バグ報告はDiscordからお願いします
  """
    st.write(content, unsafe_allow_html=True)
    UID = st.text_input("UIDを入力", value=queryUID if queryUID else "")
    queryUID = None
    if UID:
        st.query_params["uid"] = UID
    if (
        st.button(
            "プレイヤー情報の取得", key="get_player_info", on_click=session_player
        )
        or st.session_state.player_info
    ):
        placeholder = st.empty()
        placeholder.empty()
        placeholder.write("プレイヤー情報を取得中...")

        try:
            int(UID)
        except:
            placeholder.empty()
            st.write("数字で入力してね。")
            return

        try:
            player_data = await client.client.fetch_showcase(UID)
        except EnkaServerRateLimit:
            placeholder.empty()
            st.write("レートリミットに達しました。")
            return
        except EnkaServerMaintanance:
            placeholder.empty()
            st.write("EnkaNetworkがメンテナンス中です。")
            return
        except EnkaPlayerNotFound:
            placeholder.empty()
            st.write("プレイヤーが見つかりませんでした。")
            return
        except EnkaServerError:
            placeholder.empty()
            st.write("EnkaNetworkでエラーが発生しました。")
            return
        except Exception as e:
            placeholder.empty()
            st.write(f"プレイヤー情報の取得に失敗しました。{e}")
            return
        placeholder.empty()
        player_info = f"""
### プレイヤー情報
##### {player_data.player.nickname} Lv.{player_data.player.level}
- 世界ランク{player_data.player.world_level}
- 螺旋 {player_data.player.abyss_floor}-{player_data.player.abyss_level}
- アチーブメント数 {player_data.player.achievements}
"""
        st.write(player_info)
        if player_data.characters:
            characters = {
                v.name + " Lv." + str(v.level): v for v in player_data.characters
            }
            character = st.selectbox("キャラクターを選択", characters.keys())

            base_hp, hp, base_atk, atk, base_def, _def = 0, 0, 0, 0, 0, 0
            ms, cr, cd, er = 0, 0, 0, 0

            for prop_type, stat in characters[character].stats.items():
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

            weapon = characters[character].weapon
            WeaponBaseATK: int = next(
                (
                    int(stat.value)
                    for stat in weapon.stats
                    if stat.type == "FIGHT_PROP_BASE_ATTACK"
                ),
                None,
            )
            WeaponSubOP: list[enka.gi.Stat] = (
                weapon.stats[1] if len(weapon.stats) > 1 else None
            )
            WeaponSubOPKey: str = weapon.stats[1].name if WeaponSubOP else None
            WeaponSubOPValue: int | float = weapon.stats[1].value if WeaponSubOP else None

            character_info = f"""
### キャラクター情報
##### {characters[character].name} Lv.{characters[character].level}
- HP: {hp}
- 攻撃力: {atk}
- 防御力: {_def}
- 元素熟知: {ms}
- 会心率: {cr}%
- 会心ダメージ: {cd}%
- 元素チャージ効率: {er}%
- 命ノ星座: {characters[character].constellations_unlocked}凸
##### {weapon.name} Lv.{weapon.level}
- 基礎攻撃力: {WeaponBaseATK}
- 精錬ランク: {weapon.refinement}
"""
            if WeaponSubOP:
                character_info += f"- {WeaponSubOPKey}: {WeaponSubOPValue}"
            st.write(character_info)
            score_types = {
                "攻撃力": "ATTACK",
                "防御力": "DEFENSE",
                "HP": "HP",
                "元素チャージ効率": "EFFICIENCY",
                "元素熟知": "ELEMENT",
            }
            score_type = st.selectbox("スコア計算", score_types.keys())
            if st.button("ビルドカードを生成"):
                placeholder = st.empty()
                placeholder.write("ビルドカードを生成中...")
                Image = client.generation(
                    characters[character], score_types[score_type], None
                )
                placeholder.image(Image)
                st.write("画像を長押し / 右クリックで保存できます。")
        else:
            st.write("キャラクター情報の取得に失敗しました。")

    await client.client.close()
    print("closed")

def session_player():
    st.session_state.player_info = True


def gen_image(client, character):
    st.write("ビルドカードを生成中...")
    Image = client.generation(character, score_type="ATTACK")
    st.image(Image)


if __name__ == "__main__":
    asyncio.run(main())
