import discord
from discord import app_commands
from discord.ext import commands
from bot.config import Config
from .tutorial_functions.tutorial_main_view import TutorialMainView

# Embed 1: Introduction
embed1 = discord.Embed(
    title="🏟️ Welcome to the Maggod Fight Arena!",
    description=(
        "This is a **turn-based combat game** where you can battle against "
        "other players or bots to **win rewards** and prove your strength!"
    ),
    color=discord.Color.gold()
)

# Embed 2: Channels overview
embed2 = discord.Embed(
    title="📜 Channels Overview",
    color=discord.Color.blue()
)
embed2.add_field(
    name="📊 lobby-status",
    value="A text channel where you can **see active fights** and check if someone is looking for an opponent.",
    inline=False
)
embed2.add_field(
    name="💬 information",
    value=(
        "The **main multipurpose text channel** for anything related to the game:\n"
        "• Chat with other players\n"
        "• Use `/tutorial`\n"
        "• Get updates and announcements\n"
        "• Report bugs and give feedback"
    ),
    inline=False
)
embed2.add_field(
    name="🔘・maggod-fight-lobby-01 / 02",
    value=(
        "Dedicated **battle arenas** where you fight players or bots.\n"
        "To join a match use `/join`.\n"
        "If you want to fight a bot, use `/join` again.\n\n"
        "Once you join, you’ll receive instructions on how to use other `/commands`."
    ),
    inline=False
)

class TutorialCog(commands.Cog):
    """Self-contained tutorial system for Maggod Fight Arena."""

    def __init__(self, bot: commands.Bot):
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

        # ---------- Passed checks, defer the response ----------
        await interaction.response.defer(ephemeral=True)

        # ---------- Tutorial view ----------
        view = TutorialMainView(interaction.user)

        # Send the message using followup to avoid 404
        await interaction.followup.send(embeds=[embed1, embed2], view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TutorialCog(bot))
