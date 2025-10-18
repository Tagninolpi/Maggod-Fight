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
        # Track last ephemeral messages per user to delete them
        self.last_messages = {}  # user_id -> discord.Message

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
        player_data = self.manager.get_balance(user_id)
        player_word = player_data["words"] if isinstance(player_data, dict) and "words" in player_data else None
        all_players = self.manager.get_balance(all=True)
        any_word_exists = any(u.get("words") not in (None, "", "none") for u in all_players)

        view = HangmanMainView(self.manager, player_word, any_word_exists, self.bot, self)
        # Delete previous game message if exists
        if user_id in self.last_messages:
            try:
                await self.last_messages[user_id].delete()
            except Exception:
                pass
        message = await interaction.response.send_message(
            f"🎮 **Welcome to Hangman, {interaction.user.display_name}!**",
            view=view,
            ephemeral=True,
        )
        self.last_messages[user_id] = await interaction.original_response()


# ---------- Main View ----------
class HangmanMainView(discord.ui.View):
    def __init__(self, manager: MoneyManager, player_word: str, any_word_exists: bool, bot, cog: Hangman):
        super().__init__(timeout=None)
        self.manager = manager
        self.player_word = player_word
        self.any_word_exists = any_word_exists
        self.bot = bot
        self.cog = cog
        self.add_item(MakeWordButton(manager, player_word, cog))
        self.add_item(PlayButton(manager, any_word_exists, bot, cog))


# ---------- Make Word ----------
class MakeWordButton(discord.ui.Button):
    def __init__(self, manager: MoneyManager, player_word: str, cog: Hangman):
        self.manager = manager
        self.cog = cog
        style = discord.ButtonStyle.danger if player_word and player_word.lower() != "none" else discord.ButtonStyle.success
        super().__init__(label="Make Word", style=style, disabled=style == discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(WordModal(self.manager, self.cog, interaction.user.id))


# ---------- Play ----------
class PlayButton(discord.ui.Button):
    def __init__(self, manager: MoneyManager, any_word_exists: bool, bot, cog: Hangman):
        self.manager = manager
        self.bot = bot
        self.cog = cog
        style = discord.ButtonStyle.success if any_word_exists else discord.ButtonStyle.danger
        super().__init__(label="Play", style=style, disabled=not any_word_exists)

    async def callback(self, interaction: discord.Interaction):
        all_players = self.manager.get_balance(all=True)
        user_id = interaction.user.id
        valid_players = [u for u in all_players if u.get("words") not in (None, "", "none") and u["user_id"] != user_id]

        if not valid_players:
            await interaction.response.send_message("❌ No other players have provided words yet.", ephemeral=True)
            return

        view = PlayWordSelectionView(valid_players, self.bot, self.manager, self.cog, user_id)
        # Delete previous message
        if user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[user_id].delete()
            except Exception:
                pass
        message = await interaction.response.send_message(
            "🧩 **Choose a word to play!**",
            view=view,
            ephemeral=True
        )
        self.cog.last_messages[user_id] = await interaction.original_response()


# ---------- Word Selection ----------
class PlayWordSelectionView(discord.ui.View):
    def __init__(self, valid_players, bot, manager, cog: Hangman, user_id: int):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.manager = manager
        self.cog = cog
        self.user_id = user_id
        for i, player in enumerate(valid_players[:25]):
            player_id = player["user_id"]
            self.add_item(PlayerWordButton(player_id, bot, manager, cog, user_id, row=i // 5))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[self.user_id].edit(view=self)
            except Exception:
                pass


class PlayerWordButton(discord.ui.Button):
    def __init__(self, player_id: int, bot, manager, cog: Hangman, user_id: int, row):
        self.player_id = player_id
        self.bot = bot
        self.manager = manager
        self.cog = cog
        self.user_id = user_id
        super().__init__(label=f"Player {player_id}", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        data_text = self.manager.get_words(self.player_id)
        if not data_text:
            await interaction.response.send_message("⚠️ That player doesn’t have a word set.", ephemeral=True)
            return

        view = LetterGuessView(self.player_id, data_text, self.bot, self.manager, self.cog, self.user_id)
        display_word = view.get_display_word()
        used_letters = view.get_used_letters()
        user = await self.bot.fetch_user(self.player_id)

        # Delete previous message
        if self.user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[self.user_id].delete()
            except Exception:
                pass

        message = await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`\n\nUsed letters: `{used_letters}`",
            view=view,
            ephemeral=True
        )
        self.cog.last_messages[self.user_id] = await interaction.original_response()


# ---------- Modal ----------
class WordModal(discord.ui.Modal, title="Create Your Hangman Word"):
    word_input = discord.ui.TextInput(label="Enter your word (max 30 letters)", placeholder="Example: magic forest", required=True, max_length=30)

    def __init__(self, manager: MoneyManager, cog: Hangman, user_id: int):
        super().__init__()
        self.manager = manager
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        word = str(self.word_input.value).strip()
        if not re.fullmatch(r"[A-Za-z ]+", word):
            await interaction.response.send_message("❌ Invalid word! Use letters A-Z only.", ephemeral=True)
            await interaction.followup.send_modal(WordModal(self.manager, self.cog, self.user_id))
            return
        self.manager.set_words(self.user_id, f"{word} : ")
        await interaction.response.send_message(f"✅ Your word **'{word}'** has been saved!", ephemeral=True)


# ---------- Letter Guessing ----------
class LetterGuessView(discord.ui.View):
    def __init__(self, player_id, data_text: str, bot, manager, cog: Hangman, user_id: int):
        super().__init__(timeout=900.0)
        self.player_id = player_id
        self.bot = bot
        self.manager = manager
        self.cog = cog
        self.user_id = user_id

        if ":" in data_text:
            word_part, guessed_part = data_text.split(":", 1)
            self.word = word_part.strip().lower()
            self.guessed_letters = list(guessed_part.strip().lower())
        else:
            self.word = data_text.strip().lower()
            self.guessed_letters = []

        self.add_item(ChooseLetterButton(self))

    def get_display_word(self):
        return " ".join(ch.upper() if ch.lower() in self.guessed_letters else "_" if ch != " " else " " for ch in self.word)

    def get_used_letters(self):
        return " ".join(sorted(self.guessed_letters))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[self.user_id].edit(view=self)
            except Exception:
                pass


class ChooseLetterButton(discord.ui.Button):
    def __init__(self, parent_view: LetterGuessView):
        self.parent_view = parent_view
        super().__init__(label="Choose Letter", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LetterInputModal(self.parent_view))


class LetterInputModal(discord.ui.Modal, title="Guess a Letter"):
    letter_input = discord.ui.TextInput(label="Enter a single letter", placeholder="A-Z", required=True, min_length=1, max_length=1)

    def __init__(self, parent_view: LetterGuessView):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        letter = self.letter_input.value.lower()
        if not re.fullmatch(r"[a-z]", letter):
            await interaction.response.send_message("❌ Invalid input! Enter a single letter A-Z.", ephemeral=True)
            return
        if letter in self.parent_view.guessed_letters:
            await interaction.response.send_message(f"⚠️ Letter `{letter.upper()}` already used: `{self.parent_view.get_used_letters()}`", ephemeral=True)
            return

        self.parent_view.guessed_letters.append(letter)
        new_text = f"{self.parent_view.word} : {''.join(self.parent_view.guessed_letters)}"
        self.parent_view.manager.set_words(self.parent_view.player_id, new_text)

        display_word = self.parent_view.get_display_word()
        used_letters = self.parent_view.get_used_letters()
        user = await self.parent_view.bot.fetch_user(self.parent_view.player_id)

        # Delete previous message if exists
        if self.parent_view.user_id in self.parent_view.cog.last_messages:
            try:
                await self.parent_view.cog.last_messages[self.parent_view.user_id].delete()
            except Exception:
                pass

        # Check if word is complete
        if "_" not in display_word:
            all_players = self.parent_view.manager.get_balance(all=True)
            participants = [await self.parent_view.bot.fetch_user(u["user_id"]) for u in all_players if u.get("words") not in (None, "", "none")]
            participant_names = ", ".join(p.display_name for p in participants)
            message = await interaction.response.send_message(
                f"🎉 **{user.display_name}'s word was '{self.parent_view.word}'!**\nCongratulations to all: {participant_names}",
                ephemeral=True
            )
            self.parent_view.cog.last_messages[self.parent_view.user_id] = await interaction.original_response()
            return

        # Send updated guessing message
        message = await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`\n\nUsed letters: `{used_letters}`",
            view=self.parent_view,
            ephemeral=True
        )
        self.parent_view.cog.last_messages[self.parent_view.user_id] = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Hangman(bot))
