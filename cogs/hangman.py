import re
import string
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import logging
from bot.config import Config
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

        # Fetch player info
        player_data = self.manager.get_balance(user_id)
        player_word = (
            player_data["words"] if isinstance(player_data, dict) and "words" in player_data else None
        )

        all_players = self.manager.get_balance(all=True)
        any_word_exists = any(
            u.get("words") not in (None, "", "none") for u in all_players
        )

        view = HangmanMainView(self.manager, player_word, any_word_exists, self.bot)
        await interaction.response.send_message(
            f"🎮 **Welcome to Hangman, {interaction.user.display_name}!**",
            view=view,
            ephemeral=True,
        )


# ---------- Main View ----------
class HangmanMainView(discord.ui.View):
    def __init__(self, manager: MoneyManager, player_word: str, any_word_exists: bool, bot):
        super().__init__(timeout=None)
        self.manager = manager
        self.player_word = player_word
        self.any_word_exists = any_word_exists
        self.bot = bot

        # Add buttons
        self.add_item(MakeWordButton(manager, player_word))
        self.add_item(PlayButton(manager, any_word_exists, bot))


# ---------- Make Word ----------
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
        await interaction.response.send_modal(WordModal(self.manager))


# ---------- Play ----------
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

        view = PlayWordSelectionView(valid_players, self.bot, self.manager)
        await interaction.response.send_message(
            "🧩 **Choose a word to play!**",
            view=view,
            ephemeral=True,
        )


# ---------- Word Selection ----------
class PlayWordSelectionView(discord.ui.View):
    def __init__(self, valid_players, bot, manager):
        super().__init__(timeout=None)
        self.bot = bot
        self.manager = manager

        for i, player in enumerate(valid_players[:25]):
            player_id = player["user_id"]
            self.add_item(PlayerWordButton(player_id, bot, manager, row=i // 5))


class PlayerWordButton(discord.ui.Button):
    def __init__(self, player_id: int, bot, manager, row):
        self.player_id = player_id
        self.bot = bot
        self.manager = manager
        super().__init__(
            label=f"Player {player_id}",
            style=discord.ButtonStyle.primary,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction):
        target_word = self.manager.get_words(self.player_id)
        if not target_word:
            await interaction.response.send_message(
                "⚠️ That player doesn’t have a word set.",
                ephemeral=True,
            )
            return

        view = LetterGuessView(self.player_id, target_word, self.bot, [])
        display_word = view.get_display_word()

        user = await self.bot.fetch_user(self.player_id)
        await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`",
            view=view,
            ephemeral=True,
        )


# ---------- Guessing View ----------
class LetterGuessView(discord.ui.View):
    def __init__(self, player_id, word, bot, guessed_letters):
        super().__init__(timeout=None)
        self.player_id = player_id
        self.word = word.lower()
        self.bot = bot
        self.guessed_letters = guessed_letters

        letters = list(string.ascii_uppercase.replace('Z', ''))
        for i, letter in enumerate(letters):
            self.add_item(LetterButton(letter, self))

    def get_display_word(self):
        result = []
        for ch in self.word:
            if ch == " ":
                result.append(" ")
            elif ch.lower() in self.guessed_letters:
                result.append(ch.upper())
            else:
                result.append("_")
        return " ".join(result)

    async def update_view(self, interaction: discord.Interaction):
        self.clear_items()
        letters = list(string.ascii_uppercase.replace('Z', ''))
        for i, letter in enumerate(letters):
            self.add_item(LetterButton(letter, self))
        display_word = self.get_display_word()

        await interaction.edit_original_response(
            content=f"🎯 Guessing `{await self.bot.fetch_user(self.player_id)}`'s word:\n\n`{display_word}`",
            view=self,
        )

# ---------- Modal ----------
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

        if not re.fullmatch(r"[A-Za-z ]+", word):
            await interaction.response.send_message(
                "❌ Invalid word! Use **letters and spaces only** (A-Z). Try again.",
                ephemeral=True,
            )
            await interaction.followup.send_modal(WordModal(self.manager))
            return

        self.manager.set_words(user_id, word)
        await interaction.response.send_message(
            f"✅ Your word **'{word}'** has been saved! You can now play Hangman.",
            ephemeral=True,
        )

class LetterGuessView(discord.ui.View):
    def __init__(self, player_id, data_text: str, bot, manager):
        super().__init__(timeout=None)
        self.player_id = player_id
        self.bot = bot
        self.manager = manager

        # Split DB text into word and guessed letters
        if ":" in data_text:
            word_part, guessed_part = data_text.split(":", 1)
            self.word = word_part.strip().lower()
            self.guessed_letters = list(guessed_part.strip().lower())
        else:
            self.word = data_text.strip().lower()
            self.guessed_letters = []

        # Build letter buttons (A-Z)
        letters = list(string.ascii_uppercase)
        for i, letter in enumerate(letters):
            self.add_item(LetterButton(letter, self))

    def get_display_word(self):
        display = []
        for ch in self.word:
            if ch == " ":
                display.append(" ")
            elif ch.lower() in self.guessed_letters:
                display.append(ch.upper())
            else:
                display.append("_")
        return " ".join(display)


class LetterButton(discord.ui.Button):
    def __init__(self, letter, parent_view: LetterGuessView):
        self.letter = letter
        self.parent_view = parent_view

        if letter.lower() in parent_view.guessed_letters:
            if letter.lower() in parent_view.word:
                style = discord.ButtonStyle.success  # green
            else:
                style = discord.ButtonStyle.danger  # red
            disabled = True
        else:
            style = discord.ButtonStyle.secondary  # gray
            disabled = False

        super().__init__(label=letter, style=style, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        letter = self.letter.lower()
        if letter in self.parent_view.guessed_letters:
            return  # Already guessed

        # Add to guessed letters
        self.parent_view.guessed_letters.append(letter)

        # Save back to DB as "word : guessedletters"
        new_text = f"{self.parent_view.word} : {''.join(self.parent_view.guessed_letters)}"
        self.parent_view.manager.set_words(self.parent_view.player_id, new_text)

        # Close the current view and show updated word
        display_word = self.parent_view.get_display_word()
        user = await self.parent_view.bot.fetch_user(self.parent_view.player_id)

        await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(Hangman(bot))
