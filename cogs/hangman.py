import re
import string
import discord
from discord.ext import commands
from discord import app_commands
import logging
from bot.config import Config
from currency.money_manager import MoneyManager

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
            discord.ButtonStyle.success if any_word_exists else discord.ButtonStyle.danger
        )
        super().__init__(label="Play", style=style, disabled=not any_word_exists)

    async def callback(self, interaction: discord.Interaction):
        all_players = self.manager.get_balance(all=True)
        user_id = interaction.user.id

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
        super().__init__(timeout=900.0)  # 15 minutes timeout
        self.bot = bot
        self.manager = manager

        for i, player in enumerate(valid_players[:25]):
            player_id = player["user_id"]
            self.add_item(PlayerWordButton(player_id, bot, manager, row=i // 5))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            # Disable the view message to prevent interactions
            await self.message.edit(view=self)
        except Exception:
            pass


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
        data_text = self.manager.get_words(self.player_id)
        if not data_text:
            await interaction.response.send_message(
                "⚠️ That player doesn’t have a word set.",
                ephemeral=True,
            )
            return

        view = LetterGuessView(self.player_id, data_text, self.bot, self.manager)
        display_word = view.get_display_word()
        used_letters = view.get_used_letters()

        user = await self.bot.fetch_user(self.player_id)
        msg = await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n"
            f"`{display_word}`\n\n"
            f"Used letters: `{used_letters}`",
            view=view,
            ephemeral=True,
        )
        # Save message for timeout edits
        view.message = await interaction.original_response()


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

        self.manager.set_words(user_id, f"{word} : ")
        await interaction.response.send_message(
            f"✅ Your word **'{word}'** has been saved! You can now play Hangman.",
            ephemeral=True,
        )


# ---------- Letter Guessing ----------
class LetterGuessView(discord.ui.View):
    def __init__(self, player_id, data_text: str, bot, manager):
        super().__init__(timeout=900.0)  # 15 min timeout
        self.player_id = player_id
        self.bot = bot
        self.manager = manager

        if ":" in data_text:
            word_part, guessed_part = data_text.split(":", 1)
            self.word = word_part.strip().lower()
            self.guessed_letters = list(guessed_part.strip().lower())
        else:
            self.word = data_text.strip().lower()
            self.guessed_letters = []

        self.add_item(ChooseLetterButton(self))
        self.message = None  # Will hold the interaction message

    def get_display_word(self):
        return " ".join(
            ch.upper() if ch.lower() in self.guessed_letters else "_" if ch != " " else " "
            for ch in self.word
        )

    def get_used_letters(self):
        return " ".join(sorted(self.guessed_letters))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class ChooseLetterButton(discord.ui.Button):
    def __init__(self, parent_view: LetterGuessView):
        self.parent_view = parent_view
        super().__init__(label="Choose Letter", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LetterInputModal(self.parent_view))


class LetterInputModal(discord.ui.Modal, title="Guess a Letter"):
    letter_input = discord.ui.TextInput(
        label="Enter a single letter",
        placeholder="A-Z",
        required=True,
        min_length=1,
        max_length=1
    )

    def __init__(self, parent_view: LetterGuessView):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        letter = self.letter_input.value.lower()

        if not re.fullmatch(r"[a-z]", letter):
            await interaction.response.send_message(
                "❌ Invalid input! Enter a single letter A-Z.",
                ephemeral=True
            )
            return

        if letter in self.parent_view.guessed_letters:
            await interaction.response.send_message(
                f"⚠️ Letter `{letter.upper()}` has already been used: "
                f"{self.parent_view.get_used_letters()}",
                ephemeral=True
            )
            return

        self.parent_view.guessed_letters.append(letter)
        new_text = f"{self.parent_view.word} : {''.join(self.parent_view.guessed_letters)}"
        self.parent_view.manager.set_words(self.parent_view.player_id, new_text)

        display_word = self.parent_view.get_display_word()
        used_letters = self.parent_view.get_used_letters()
        user = await self.parent_view.bot.fetch_user(self.parent_view.player_id)

        # Check if word is fully guessed
        if "_" not in display_word:
            # Fetch all participating players
            all_players = self.parent_view.manager.get_balance(all=True)
            participants = [await self.parent_view.bot.fetch_user(u["user_id"])
                            for u in all_players if u.get("words") not in (None, "", "none")]
            participant_names = ", ".join(p.display_name for p in participants)
            await interaction.response.edit_message(
                content=(
                    f"🎉 **{user.display_name}'s word was '{self.parent_view.word}'!**\n"
                    f"Congratulations to all: {participant_names}"
                ),
                view=None
            )
            return

        # Otherwise, update the same message
        await interaction.response.edit_message(
            content=(
                f"🎯 **Guessing {user.display_name}'s word!**\n\n"
                f"`{display_word}`\n\n"
                f"Used letters: `{used_letters}`"
            ),
            view=self.parent_view
        )
        self.parent_view.message = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Hangman(bot))
