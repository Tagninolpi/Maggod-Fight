import discord
from discord import app_commands
from discord.ext import commands
import unicodedata
from utils.gameplay_tag import God
from bot.config import Config  # make sure this contains LOBBY_CATEGORY_NAME and allowed_channel_id
from utils.game_test_on_discord import gods
from .tutorial_functions.tutorial_main_view import TutorialMainView



class TutorialCog(commands.Cog):
    """Self-contained tutorial system for Maggod Fight Arena."""

    def __init__(self, bot):
        self.bot = bot

    # ---------------- Slash Command ----------------
    @app_commands.command(name="tutorial", description="Learn how the Maggod Fight Arena works.")
    async def tutorial(self, interaction: discord.Interaction):
        channel = interaction.channel

        # ---------- Checks ----------
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        if interaction.channel.id != Config.allowed_channel_id:
            await interaction.response.send_message(
                "❌ You can't use this command here.",
                ephemeral=True
            )
            return

        # ---------- Passed checks, show main tutorial ----------
        embed = discord.Embed(
            title="📚 Tutorial",
            description="Welcome! Press 'Gods Tutorial' to learn about gods or 'Exit' to close.",
            color=discord.Color.green()
        )
        view = TutorialMainView(interaction.user, self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TutorialCog(bot))
