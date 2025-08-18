import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

class Tutorial(commands.Cog):
    """Cog for the Maggod Fight tutorial system."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tutorial", description="Learn how the Maggod Fight Arena works.")
    async def tutorial(self, interaction: discord.Interaction):
        channel = interaction.channel
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

        # Buttons
        class TutorialView(discord.ui.View):
            def __init__(self, *, timeout=120):
                super().__init__(timeout=timeout)
                self.message = None  # Will store the sent message

            async def on_timeout(self):
                # Delete the message with embeds/buttons on timeout
                if self.message:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        pass

            @discord.ui.button(label="I got it", style=discord.ButtonStyle.danger)
            async def got_it(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                # Delete the message when the user presses "I got it"
                if self.message:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        pass
                self.stop()  # Stop listening to the view
                await interaction_button.response.send_message("✅ Tutorial closed.", ephemeral=True)

            @discord.ui.button(label="Next", style=discord.ButtonStyle.success)
            async def next_embed(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                await interaction_button.response.send_message("➡️ Next tutorial section coming soon!", ephemeral=True)
                # Later we will replace this with the actual next embed/buttons

        view = TutorialView()
        # Send the tutorial embeds with buttons (ephemeral)
        view.message = await interaction.response.send_message(
            embeds=[embed1, embed2], view=view, ephemeral=True
        )


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Tutorial(bot))
