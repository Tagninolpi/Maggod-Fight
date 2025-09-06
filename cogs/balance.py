import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
from currency.money_manager import MoneyManager
import logging

logger = logging.getLogger(__name__)

class Balance(commands.Cog):
    """Cog for seeing player balances in Maggod Fight lobbies."""

    def __init__(self, bot):
        self.bot = bot
        self.money_manager = MoneyManager()  # Initialize your MoneyManager

    @app_commands.command(name="balance", description="See the leaderboard of all balances.")
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

        # Fetch all balances
        all_users = self.money_manager.get_balance(all=True)  # List of dicts [{"user_id": ..., "balance": ...}]
        if not all_users:
            await interaction.response.send_message("No balances found in the database.", ephemeral=True)
            return

        # Sort descending by balance
        sorted_users = sorted(all_users, key=lambda x: x["balance"], reverse=True)

        # Build leaderboard string
        description_lines = []
        for idx, user in enumerate(sorted_users, start=1):
            uid = user["user_id"]
            balance = user["balance"]

            # Try to fetch member from guild
            try:
                member = await interaction.guild.fetch_member(uid)
                name = member.display_name
            except discord.NotFound:
                # If not in guild, fetch global user
                try:
                    user_obj = await interaction.client.fetch_user(uid)
                    name = str(user_obj)  # username#1234
                except discord.NotFound:
                    name = f"User {uid}"  # fallback

            # Format balance with spaces for thousands
            balance_str = f"{balance:,d}".replace(",", " ")

            # Highlight the command user
            if uid == user_id:
                line = f"**{idx}. {name} — {balance_str} {Config.coin} 👈 You**"
            else:
                line = f"{idx}. {name} — {balance_str} {Config.coin}"

            description_lines.append(line)

        # Join lines without extra blank lines
        description = "\n".join(description_lines)

        # Create embed
        embed = discord.Embed(
            title="💰 Leaderboard",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Balance(bot))
