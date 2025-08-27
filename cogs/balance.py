import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
from currency.money_manager import MoneyManager
import logging

logger = logging.getLogger(__name__)

class Balance(commands.Cog):
    """Cog for seeing player balance in Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot
        self.money_manager = MoneyManager()  # Initialize your MoneyManager

    @app_commands.command(name="balance", description="See your money balance.")
    async def balance(self, interaction: discord.Interaction):
        channel = interaction.channel
        user_id = interaction.user.id

        # Make sure the command is used in a text channel in the correct category
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

        # Get the user's balance from MoneyManager
        self.money_manager.set_balance(user_id,0)
        balance = self.money_manager.get_balance(user_id)

        # Create an embed to display the balance
        embed = discord.Embed(
            title="💰 Your Balance",
            description=f"You currently have **{balance}** coins.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Balance(bot))
