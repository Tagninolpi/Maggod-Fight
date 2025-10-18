import re
import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging
from datetime import datetime, timezone
from currency.money_manager import MoneyManager  # adjust import if needed

logger = logging.getLogger(__name__)


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
                ephemeral=True,
            )
            return

        if not channel.category or channel.category.id != Config.LOBBY_CATEGORY_ID:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True,
            )
            return

        user_id = interaction.user.id

        # Check player word in DB
        player_data = self.manager.get_balance(user_id)
        player_word = (
            player_data["words"] if isinstance(player_data, dict) else None
        )

        # Check if any player has words for the play button
        all_players = self.manager.get_balance(all=True)
        any_word_exists = any(
            u.get("words") not in (None, "", "none") for u in all_players
        )

        view = HangmanMainView(self.manager, player_word, any_word_exists,self.bot)
        await interaction.response.send_message(
            f"🎮 **Welcome to Hangman, {interaction.user.display_name}!**",
            view=view,
            ephemeral=True,
        )


class HangmanMainView(discord.ui.View):
    def __init__(self, manager: MoneyManager, player_word: str, any_word_exists: bool):
        super().__init__(timeout=None)
        self.manager = manager
        self.player_word = player_word
        self.any_word_exists = any_word_exists
        self.add_item(MakeWordButton(manager, player_word))
        self.add_item(PlayButton(manager, any_word_exists, bot))

        # Add buttons
        self.make_word_button = MakeWordButton(manager, player_word)
        self.play_button = PlayButton(any_word_exists)
        self.add_item(self.make_word_button)
        self.add_item(self.play_button)


class MakeWordButton(discord.ui.Button):
    def __init__(self, manager: MoneyManager, player_word: str):
        self.manager = manager
        style = (
            discord.ButtonStyle.danger
            if player_word and player_word.lower() != "none"
            else discord.ButtonStyle.success
        )
        super().__init__(
            label="Make Word",
            style=style,
            disabled=style == discord.ButtonStyle.danger,
        )

    async def callback(self, interaction: discord.Interaction):
        # Open the modal to create a word
        await interaction.response.send_modal(WordModal(self.manager))


class PlayButton(discord.ui.Button):
    def __init__(self, any_word_exists: bool):
        style = (
            discord.ButtonStyle.success
            if any_word_exists
            else discord.ButtonStyle.danger
        )
        super().__init__(label="Play", style=style, disabled=not any_word_exists)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🎯 The Play feature will be added soon!",
            ephemeral=True,
        )


class WordModal(discord.ui.Modal, title="Create Your Hangman Word"):
    word_input = discord.ui.TextInput(
        label="Enter your word (max 30 letters)",
        placeholder="Example: magic forest",
        required=True,
        max_length=30,
    )

    def __init__(self, manager: MoneyManager):
        super().__init__()
        self.manager = manager

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        word = str(self.word_input.value).strip()

        # Validation: only letters & spaces
        if not re.fullmatch(r"[A-Za-z ]+", word):
            await interaction.response.send_message(
                "❌ Invalid word! Use **letters and spaces only** (A-Z). Try again.",
                ephemeral=True,
            )
            # Re-open the modal for retry
            await interaction.followup.send_modal(WordModal(self.manager))
            return

        # Save to DB
        self.manager.set_words(user_id, word)

        await interaction.response.send_message(
            f"✅ Your word **'{word}'** has been saved! You can now play Hangman.",
            ephemeral=True,
        )

class PlayButton(discord.ui.Button):
    def __init__(self, manager: MoneyManager, any_word_exists: bool, bot):
        self.manager = manager
        self.bot = bot
        style = (
            discord.ButtonStyle.success
            if any_word_exists
            else discord.ButtonStyle.danger
        )
        super().__init__(label="Play", style=style, disabled=not any_word_exists)

    async def callback(self, interaction: discord.Interaction):
        # Build the play menu
        all_players = self.manager.get_balance(all=True)
        user_id = interaction.user.id

        # Filter out players with no word or your own word
        valid_players = [
            u for u in all_players
            if u.get("words") not in (None, "", "none")
            and u["user_id"] != user_id
        ]

        if not valid_players:
            await interaction.response.send_message(
                "❌ No other players have provided words yet.",
                ephemeral=True,
            )
            return

        # Create and show the grid view
        view = PlayWordSelectionView(valid_players, self.bot)
        await interaction.response.send_message(
            "🧩 **Choose a word to play!**",
            view=view,
            ephemeral=True,
        )


class PlayWordSelectionView(discord.ui.View):
    def __init__(self, valid_players, bot):
        super().__init__(timeout=None)
        self.bot = bot

        # Create up to 25 buttons (5x5 grid)
        for i, player in enumerate(valid_players[:25]):
            player_id = player["user_id"]
            self.add_item(PlayerWordButton(player_id, bot))


class PlayerWordButton(discord.ui.Button):
    def __init__(self, player_id: int, bot):
        self.player_id = player_id
        self.bot = bot
        super().__init__(
            label=f"Player {player_id}",
            style=discord.ButtonStyle.primary,
            row=(player_id % 5),
        )

    async def callback(self, interaction: discord.Interaction):
        user = await self.bot.fetch_user(self.player_id)
        await interaction.response.send_message(
            f"🕹️ You selected **{user.display_name}**'s word! (game coming soon)",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(Hangman(bot))
