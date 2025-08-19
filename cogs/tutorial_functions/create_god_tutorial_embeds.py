import discord
import unicodedata
from utils.game_test_on_discord import gods

def simple_embed(message: str) -> discord.Embed:
    """
    Returns a simple Discord Embed with a purple border and the given message as the title.
    
    message: The title of the embed.
    """
    embed = discord.Embed(
        title=message,
        color=discord.Color.purple()
    )
    return embed

def create_god_tutorial_embeds(god_names: list[str], success: bool = True) -> list[discord.Embed]:
    """
        Create a tutorial embed for a list of 5 gods using the global `gods` dictionary.

        god_names: List of 5 god name strings.
        success: If True, embed border is green; otherwise, red.
        """
    if len(god_names) != 5:
        raise ValueError("Exactly 5 gods must be provided.")

    gods_list = [gods[name.lower()] for name in god_names]

    def visual_len(s: str) -> int:
        width = 0
        for c in s:
            if unicodedata.east_asian_width(c) in "WF":
                width += 2
            else:
                width += 1
        return width

    def pad(s: str, width: int = 11) -> str:
        vis_length = visual_len(s)
        padding = max(0, width - vis_length)
        return s + " " * padding

    def get_shield(god):
        icons = []
        if "posi_shield" in god.effects:
            icons.append(f"🔱{god.effects['posi_shield'].value}")
        if "hep_shield" in god.effects:
            icons.append(f"🛡️{god.effects['hep_shield'].value}")
        if "hades_uw_shield" in god.effects:
            icons.append(f"☠️{god.effects['hades_uw_shield'].value}")
        return " ".join(icons)

    def get_dmg_boost(god):
        icons = []
        if "ares_do_more_dmg" in god.effects:
            icons.append(f"+{god.effects['ares_do_more_dmg'].value}🔥")
        if "hades_ow_do_more_dmg" in god.effects:
            icons.append(f"+{god.effects['hades_ow_do_more_dmg'].value}💥")
        if "mega_do_less_dmg" in god.effects:
            icons.append(f"-{god.effects['mega_do_less_dmg'].value}💚")
        return " ".join(icons)

    def get_hp_boost_icon(god):
        icons = []
        if "athena_more_max_hp" in god.effects:
            icons.append("📯")
        if "cerberus_more_max_hp_per_visible_ally" in god.effects:
            icons.append("⛑️")
        return " ".join(icons)

    def get_misc_effects_icons(god):
        icons = []
        if "zeus_stun" in god.effects:
            icons.append("💫")
        if "aphro_charm" in god.effects:
            icons.append("💘")
        if "charon_invisible_duration" in god.effects:
            icons.append("🧿")
        if "tisi_freeze_timer" in god.effects:
            icons.append("❄️")
        if "cerberus_more_max_hp_per_visible_ally" in god.effects:
            icons.append("🐶")
        if "alecto_get_more_dmg" in god.effects:
            icons.append("💢")
        if god.reload > 0:
            icons.append(f"{god.reload}⏳")
        return " ".join(icons)

    def format_team(team: list) -> str:
        names = [pad(god.name[:10]) for god in team]

        def bold_digits(s: str) -> str:
            return s.translate(str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"))

        hp_numbers = []
        hp_icons = []
        dmg_numbers = []
        dmg_icons = []
        states = []
        visions = []

        for god in team:
            hp_str = f"{god.hp}/"
            is_hp_boosted = (
                "athena_more_max_hp" in god.effects or
                "cerberus_more_max_hp_per_visible_ally" in god.effects
            )
            max_hp_str = bold_digits(str(god.max_hp)) if is_hp_boosted else str(god.max_hp)
            hp_numbers.append(pad(hp_str + max_hp_str))
            hp_icons.append(pad(get_hp_boost_icon(god) + get_shield(god)))
            dmg_numbers.append(pad(str(god.dmg)))
            dmg_icons.append(pad(get_dmg_boost(god)))
            states.append(pad("❤️" if god.alive else "💀", 11))
            visions.append(pad("👁️" if god.visible else "👻", 11))

        misc_effects_line = "".join(pad(get_misc_effects_icons(god)) for god in team)

        lines = [
            "".join(names),
            "".join(hp_numbers),
            "".join(hp_icons),
            "".join(dmg_numbers),
            "".join(dmg_icons),
            "".join(states),
            "".join(visions),
        ]

        if any(get_misc_effects_icons(god) for god in team):
            lines.append(misc_effects_line)

        return "```\n" + "\n".join(lines) + "\n```"

    embed_color = discord.Color.green() if success else discord.Color.red()
    embed_title = "🛡️ Your Team" if success else "🔥 Enemy Team"

    embed = discord.Embed(
        title=embed_title,
        description=format_team(gods_list),
        color=embed_color
    )


    return [embed]