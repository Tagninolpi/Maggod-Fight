import discord
from discord.ext import commands
from discord import app_commands
import logging
from bot.config import Config
logger = logging.getLogger(__name__)



class Connect4(commands.Cog):

    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="connect4", description="Open connect4 menu")
    async def connect4(self, interaction: discord.Interaction):
        # At the start of your command
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not(channel.id in Config.ARCADE_CHANNELS_IDS):
            await interaction.response.send_message(
                "❌ You must use this command in gaming or bot-commands channel",
                ephemeral=True
            )
            return
        

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Connect4(bot))
