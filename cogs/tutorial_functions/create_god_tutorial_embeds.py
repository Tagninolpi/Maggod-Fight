import discord
import unicodedata
from utils.game_test_on_discord import gods, Effect

def simple_embed(message: str) -> discord.Embed:
    """Returns a simple Discord Embed with a purple border and the given message as the title."""
    return discord.Embed(title=message, color=discord.Color.purple())

def create_god_tutorial_embeds(god_names: list[str], success: bool = True, overrides: dict[str, dict] = None) -> list[discord.Embed]:
    """
    Create a tutorial embed for a list of 5 gods with optional overrides.

    god_names: List of 5 god name strings.
    success: If True, embed border is green; otherwise, red.
    overrides: Dictionary mapping god names to dictionaries of attributes to override.
               Example: {"poseidon": {"hp": 50, "visible": True, "effects": {"posi_shield": 5}}}
    """
    if len(god_names) != 5:
        raise ValueError("Exactly 5 gods must be provided.")

    overrides = overrides or {}
    gods_list = []

    for name in god_names:
        god = gods[name.lower()]
        # Make a copy
        god_copy = god.__class__(god.name, god.hp, god.dmg, god.reload_max)
        god_copy.max_hp = god.max_hp
        # Copy effects as new Effect instances
        god_copy.effects = {k: Effect(v.value, v.duration) for k, v in god.effects.items()}
        god_copy.visible = god.visible
        god_copy.alive = god.alive
        god_copy.reload = god.reload

        # Apply overrides
        if name.lower() in overrides:
            for attr, val in overrides[name.lower()].items():
                if attr == "effects":
                    # Convert plain dict to proper Effect objects
                    for effect_name, effect_val in val.items():
                        god_copy.effects[effect_name] = Effect(effect_val, 2)  # default duration 2 for tutorial
                else:
                    setattr(god_copy, attr, val)

        gods_list.append(god_copy)

    def visual_len(s: str) -> int:
        return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

    def pad(s: str, width: int = 11) -> str:
        return s + " " * max(0, width - visual_len(s))

    def get_shield(god):
        icons = []
        for effect in ["posi_shield", "hep_shield", "hades_uw_shield"]:
            if effect in god.effects:
                icons.append(f"{'🔱' if effect=='posi_shield' else '🛡️' if effect=='hep_shield' else '☠️'}{god.effects[effect].value}")
        return " ".join(icons)

    def get_dmg_boost(god):
        icons = []
        for effect, icon in [("ares_do_more_dmg","🔥"), ("hades_ow_do_more_dmg","💥"), ("mega_do_less_dmg","💚")]:
            if effect in god.effects:
                prefix = "+" if "more" in effect else "-"
                icons.append(f"{prefix}{god.effects[effect].value}{icon}")
        return " ".join(icons)

    def get_hp_boost_icon(god):
        icons = []
        if "athena_more_max_hp" in god.effects:
            icons.append("📯")
        if "cerberus_more_max_hp_per_visible_ally" in god.effects:
            icons.append("⛑️")
        return " ".join(icons)

    def get_misc_effects_icons(god):
        icons_map = {
            "zeus_stun": "💫",
            "aphro_charm": "💘",
            "charon_invisible_duration": "🧿",
            "tisi_freeze_timer": "❄️",
            "cerberus_more_max_hp_per_visible_ally": "🐶",
            "alecto_get_more_dmg": "💢"
        }
        icons = [icons_map[effect] for effect in god.effects if effect in icons_map]
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
            is_hp_boosted = "athena_more_max_hp" in god.effects or "cerberus_more_max_hp_per_visible_ally" in god.effects
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

    return embed
