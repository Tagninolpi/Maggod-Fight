import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import your MoneyManager to access words in DB
from bot.money_manager import MoneyManager  # adjust path if needed

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = MoneyManager()

    @app_commands.command(name="hangman", description="Open hangman menu")
    async def hangman(self, interaction: discord.Interaction):
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

        user_id = interaction.user.id

        # Check player word in DB
        player_data = self.manager.get_balance(user_id)
        player_word = player_data["words"] if isinstance(player_data, dict) else None

        # Check if any player has words for the play button
        all_players = self.manager.get_balance(all=True)
        any_word_exists = any(u.get("words") not in (None, "", "none") for u in all_players)

        # Create the buttons view
        view = HangmanMainView(player_word, any_word_exists)

        await interaction.response.send_message(
            f"🎮 **Welcome to Hangman, {interaction.user.display_name}!**",
            view=view,
            ephemeral=True
        )


class HangmanMainView(discord.ui.View):
    def __init__(self, player_word: str, any_word_exists: bool):
        super().__init__(timeout=None)

        # Determine color and enabled state for Make Word
        if player_word and player_word.lower() != "none":
            # Player already has a word
            make_word_button = discord.ui.Button(
                label="Make Word",
                style=discord.ButtonStyle.danger,
                disabled=True
            )
        else:
            make_word_button = discord.ui.Button(
                label="Make Word",
                style=discord.ButtonStyle.success,
                disabled=False
            )

        # Determine Play button
        if not any_word_exists:
            play_button = discord.ui.Button(
                label="Play",
                style=discord.ButtonStyle.danger,
                disabled=True
            )
        else:
            play_button = discord.ui.Button(
                label="Play",
                style=discord.ButtonStyle.success,
                disabled=False
            )

        # Add to the view
        self.add_item(make_word_button)
        self.add_item(play_button)


async def setup(bot):
    await bot.add_cog(Hangman(bot))
