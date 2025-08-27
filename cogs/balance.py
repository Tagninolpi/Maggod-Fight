import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging
from bot.utils import update_lobby_status_embed
from database.manager import db_manager
from currency.money_manager import MoneyManager

logger = logging.getLogger(__name__)

class Balance(commands.Cog):
    """Cog for seing balance Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="see money.")
    async def balance(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.id != Config.LOBBY_CATEGORY_ID:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Balance(bot))
 