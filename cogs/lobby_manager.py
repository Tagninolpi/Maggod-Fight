import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
from bot.checks import Check as c
from bot.utils import matchmaking_dict

class LobbyManager(commands.Cog):
    """Manage Maggod Fight lobby channels."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="create_maggod_lobbies",
        description="Create 2 Maggod Fight Lobby channels under existing category."
    )
    @c.is_allowed_player()
    @c.is_allowed_channel()
    @c.is_lobby_channel()
    async def create_lobbies(self, interaction: discord.Interaction):
        # Defer the response for ephemeral reply
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=Config.LOBBY_CATEGORY_ID)
        existing = [ch for ch in category.channels if ch.name.startswith("🔘・maggod-fight-lobby-")]

        to_create = 2 - len(existing)
        if to_create <= 0:
            await interaction.followup.send("ℹ️ There are already 2 or more lobby channels. No new channels created.", ephemeral=True)
            return

        created = 0
        for i in range(1, 3):
            name = f"🔘・maggod-fight-lobby-{i:02d}"
            if any(ch.name == name for ch in existing):
                continue
            await guild.create_text_channel(
                name,
                category=category,
                topic="Maggod Fight Lobby - Build your team and fight!"
            )
            created += 1

        await interaction.followup.send(f"✅ Created {created} new lobby channel(s).", ephemeral=True)

    @app_commands.command(
        name="delete_maggod_lobbies",
        description="Delete all Maggod Fight lobby channels in the lobby category."
    )
    @c.is_allowed_player()
    @c.is_allowed_channel()
    @c.is_lobby_channel()
    async def delete_lobbies(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category = discord.utils.get(guild.categories, id=Config.LOBBY_CATEGORY_ID)

        lobby_channels = [ch for ch in category.channels if ch.name.startswith("🔘・maggod-fight-lobby-")]

        for ch in lobby_channels:
            if ch.id in matchmaking_dict:
                del matchmaking_dict[ch.id]
            await ch.delete()

        await interaction.followup.send(f"🗑️ Deleted {len(lobby_channels)} lobby channels and cleared matchmaking data.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(LobbyManager(bot))
