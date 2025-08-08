from discord import Interaction, TextChannel
from discord.app_commands import check
from bot.config import Config
from bot.utils import matchmaking_dict

def is_lobby_channel():
    @check
    async def predicate(interaction: Interaction) -> bool:
        channel = interaction.channel
        if not isinstance(channel, TextChannel):
            await interaction.followup.send(
                f"❌ This command must be used in a text channel (`{Config.LOBBY_CATEGORY_NAME}`).",
                ephemeral=True
            )
            return False
        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.followup.send(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return False
        return True
    return predicate

def is_match_participant():
    @check
    async def predicate(interaction: Interaction) -> bool:
        match = matchmaking_dict.get(interaction.channel.id)
        if not match or interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.followup.send(
                "🚫 You are not a participant in this match.",
                ephemeral=True
            )
            return False
        return True
    return predicate

def is_allowed_channel(allowed_channel_id: int):
    @check
    async def predicate(interaction: Interaction) -> bool:
        if interaction.channel.id != allowed_channel_id:
            await interaction.followup.send(
                "❌ You can't use this command here.",
                ephemeral=True
            )
            return False
        return True
    return predicate

def match_phase(required_phase: str):
    @check
    async def predicate(interaction: Interaction) -> bool:
        match = matchmaking_dict.get(interaction.channel.id)
        if not match or match.game_phase != required_phase:
            await interaction.followup.send(
                f"You can't use this command now (required: {required_phase}).",
                ephemeral=True
            )
            return False
        return True
    return predicate

def turn_not_in_progress():
    @check
    async def predicate(interaction: Interaction) -> bool:
        match = matchmaking_dict.get(interaction.channel.id)
        if match and match.turn_in_progress:
            await interaction.followup.send(
                "⏳ A turn is already in progress. Please choose a god.",
                ephemeral=True
            )
            return False
        return True
    return predicate
