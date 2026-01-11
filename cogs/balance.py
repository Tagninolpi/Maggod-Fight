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
        await interaction.response.defer(thinking=True)  # Keeps the interaction alive and shows a "thinking..." state

        try:
            channel = interaction.channel
            user_id = interaction.user.id

            if not isinstance(channel, discord.TextChannel):
                await interaction.followup.send("❌ This command must be used in a text channel.", ephemeral=True)
                return

            if not channel.category or not(channel.category.id in Config.LOBBY_CATEGORY_ID):
                await interaction.followup.send(
                    f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                    ephemeral=True
                )
                return

            # ⬇️ DB call here — if this fails, you'll catch it below
            all_users = self.money_manager.get_balance(all=True)

            if not all_users:
                await interaction.followup.send("No balances found in the database.", ephemeral=True)
                return

            sorted_users = sorted(all_users, key=lambda x: x["balance"], reverse=True)

            description_lines = []
            for idx, user in enumerate(sorted_users, start=1):
                uid = user["user_id"]
                balance = user["balance"]

                try:
                    member = await interaction.guild.fetch_member(uid)
                    name = member.display_name
                except discord.NotFound:
                    try:
                        user_obj = await interaction.client.fetch_user(uid)
                        name = str(user_obj)
                    except discord.NotFound:
                        name = f"User {uid}"

                balance_str = f"{int(balance):,d}".replace(",", " ")

                if uid == user_id:
                    line = f"**{idx}. {name} — {balance_str} {Config.coin} 👈 You**"
                else:
                    line = f"{idx}. {name} — {balance_str} {Config.coin}"

                description_lines.append(line)

            description = "\n".join(description_lines)

            embed = discord.Embed(
                title="💰 Leaderboard",
                description=description,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

            await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            # Log the actual traceback to console so you see the real DB or logic error
            logger.exception("Error in /balance command")
            await interaction.followup.send(f"❌ An unexpected error occurred: `{type(e).__name__}: {e}`", ephemeral=True)



async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Balance(bot))
