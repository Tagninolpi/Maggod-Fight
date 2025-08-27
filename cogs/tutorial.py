import discord
from discord import app_commands
from discord.ext import commands
from bot.config import Config
from .tutorial_functions.tutorial_main_view import TutorialMainView,main_embeds

class TutorialCog(commands.Cog):
    """Self-contained tutorial system for Maggod Fight Arena."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ---------------- Slash Command ----------------
    @app_commands.command(name="tutorial", description="Learn how the Maggod Fight Arena works.")
    async def tutorial(self, interaction: discord.Interaction):
        channel = interaction.channel
        log_channel = self.bot.get_channel(Config.ANNOUNCE_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"<@{Config.OWNER_ID}> Player **{interaction.user}** started the tutorial"
            )
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

        # ---------- Passed checks ----------
        view = TutorialMainView(interaction.user)

        # Send the ephemeral response
        await interaction.response.send_message(
            embeds=[main_embeds[0]],
            view=view,
            ephemeral=True
        )

        # Fetch the *real* message object from followup
        message = await interaction.original_response()
        view.message = message



async def setup(bot: commands.Bot):
    await bot.add_cog(TutorialCog(bot))
