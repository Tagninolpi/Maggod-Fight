import re
import discord
from discord.ext import commands
from discord import app_commands
import logging
from bot.config import Config


logger = logging.getLogger(__name__)


class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from currency.money_manager import MoneyManager
        self.manager = MoneyManager()
        self.last_messages = {}  # user_id -> discord.Message (to delete old ephemeral views)

    @app_commands.command(name="hangman", description="Open hangman menu")
    async def hangman(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Use this command in a text channel.", ephemeral=True)
            return

        if not channel.category or channel.category.id != Config.LOBBY_CATEGORY_ID:
            await interaction.response.send_message(
                f"❌ Use this in `{Config.LOBBY_CATEGORY_NAME}` channel.", ephemeral=True
            )
            return

        user_id = interaction.user.id
        player_data = self.manager.get_balance(user_id)
        player_word = player_data["words"] if isinstance(player_data, dict) and "words" in player_data else None
        all_players = self.manager.get_balance(all=True)
        any_word_exists = any(u.get("words") not in (None, "", "none") for u in all_players)

        view = HangmanMainView(self.manager, player_word, any_word_exists, self.bot, self)

        # Delete previous ephemeral message
        if user_id in self.last_messages:
            try:
                await self.last_messages[user_id].delete()
            except Exception:
                pass

        await interaction.response.send_message(
            f"🎮 **Welcome to Hangman, {interaction.user.display_name}!**",
            view=view,
            ephemeral=True,
        )
        self.last_messages[user_id] = await interaction.original_response()


# ---------- Main Menu ----------
class HangmanMainView(discord.ui.View):
    def __init__(self, manager, player_word, any_word_exists, bot, cog):
        super().__init__(timeout=None)
        self.manager = manager
        self.player_word = player_word
        self.any_word_exists = any_word_exists
        self.bot = bot
        self.cog = cog
        self.add_item(MakeWordButton(manager, player_word, cog))
        self.add_item(PlayButton(manager, any_word_exists, bot, cog))


# ---------- Word Creation ----------
class MakeWordButton(discord.ui.Button):
    def __init__(self, manager, player_word, cog):
        self.manager = manager
        self.cog = cog
        style = (
            discord.ButtonStyle.danger
            if player_word and player_word.lower() != "none"
            else discord.ButtonStyle.success
        )
        super().__init__(label="Make Word", style=style, disabled=style == discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(WordModal(self.manager, self.cog, interaction.user.id))


# ---------- Play Menu ----------
class PlayButton(discord.ui.Button):
    def __init__(self, manager, any_word_exists, bot, cog):
        self.manager = manager
        self.bot = bot
        self.cog = cog
        style = discord.ButtonStyle.success if any_word_exists else discord.ButtonStyle.danger
        super().__init__(label="Play", style=style, disabled=not any_word_exists)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        all_players = self.manager.get_balance(all=True)
        valid_players = [
            u for u in all_players if u.get("words") not in (None, "", "none") and u["user_id"] != user_id
        ]

        if not valid_players:
            await interaction.response.send_message("❌ No players have set words yet.", ephemeral=True)
            return

        view = PlayWordSelectionView(valid_players, self.bot, self.manager, self.cog, user_id)
        await view.setup()

        # Replace old ephemeral message
        if user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[user_id].delete()
            except Exception:
                pass

        await interaction.response.send_message("🧩 **Choose a word to play!**", view=view, ephemeral=True)
        self.cog.last_messages[user_id] = await interaction.original_response()


# ---------- Word Selection ----------
class PlayWordSelectionView(discord.ui.View):
    def __init__(self, valid_players, bot, manager, cog, user_id):
        super().__init__(timeout=900.0)
        self.bot = bot
        self.manager = manager
        self.cog = cog
        self.user_id = user_id
        self.valid_players = valid_players

    async def setup(self):
        for i, player in enumerate(self.valid_players[:25]):
            player_id = player["user_id"]
            try:
                user = await self.bot.fetch_user(player_id)
                label = user.display_name
            except Exception:
                label = f"Player {player_id}"
            self.add_item(PlayerWordButton(label, player_id, self.bot, self.manager, self.cog, self.user_id, row=i // 5))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.user_id in self.cog.last_messages:
                await self.cog.last_messages[self.user_id].edit(view=self)
        except Exception:
            pass


class PlayerWordButton(discord.ui.Button):
    def __init__(self, label, player_id, bot, manager, cog, user_id, row):
        self.player_id = player_id
        self.bot = bot
        self.manager = manager
        self.cog = cog
        self.user_id = user_id
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        data_text = self.manager.get_words(self.player_id)
        if not data_text:
            await interaction.response.send_message("⚠️ That player has no word set.", ephemeral=True)
            return

        view = LetterGuessView(self.player_id, data_text, self.bot, self.manager, self.cog, self.user_id)
        display_word = view.get_display_word()
        used_letters = view.get_used_letters()
        user = await self.bot.fetch_user(self.player_id)

        if self.user_id in self.cog.last_messages:
            try:
                await self.cog.last_messages[self.user_id].delete()
            except Exception:
                pass

        await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`\n\nUsed letters: `{used_letters}`",
            view=view,
            ephemeral=True,
        )
        self.cog.last_messages[self.user_id] = await interaction.original_response()


# ---------- Word Modal ----------
class WordModal(discord.ui.Modal, title="Create Your Hangman Word"):
    word_input = discord.ui.TextInput(
        label="Enter your word (max 30 letters)", placeholder="Example: magic forest", required=True, max_length=30
    )

    def __init__(self, manager, cog, user_id):
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
        self.manager.update_balance(self.user_id, 500)  # ✅ reward for creating a word
        await interaction.response.send_message(f"✅ Your word **'{word}'** has been saved! (+500💰)", ephemeral=True)


# ---------- Guessing Logic ----------
class LetterGuessView(discord.ui.View):
    def __init__(self, player_id, data_text, bot, manager, cog, user_id):
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
        try:
            if self.user_id in self.cog.last_messages:
                await self.cog.last_messages[self.user_id].edit(view=self)
        except Exception:
            pass


class ChooseLetterButton(discord.ui.Button):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(label="Choose Letter", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LetterInputModal(self.parent_view))


class LetterInputModal(discord.ui.Modal, title="Guess a Letter"):
    letter_input = discord.ui.TextInput(label="Enter a single letter", placeholder="A-Z", required=True, min_length=1, max_length=1)

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        letter = self.letter_input.value.lower()
        if not re.fullmatch(r"[a-z]", letter):
            await interaction.response.send_message("❌ Invalid input! Enter a single letter A-Z.", ephemeral=True)
            return

        if letter in self.parent_view.guessed_letters:
            await interaction.response.send_message(
                f"⚠️ Letter `{letter.upper()}` already used: `{self.parent_view.get_used_letters()}`", ephemeral=True
            )
            return

        self.parent_view.guessed_letters.append(letter)
        word = self.parent_view.word
        user_id = self.parent_view.user_id
        player_id = self.parent_view.player_id
        manager = self.parent_view.manager

        correct = letter in word
        reward = 2000 if correct else 1000
        manager.update_balance(user_id, reward)

        new_text = f"{word} : {''.join(self.parent_view.guessed_letters)}"
        manager.set_words(player_id, new_text)

        display_word = self.parent_view.get_display_word()
        used_letters = self.parent_view.get_used_letters()
        user = await self.parent_view.bot.fetch_user(player_id)

        # Delete old ephemeral message
        if user_id in self.parent_view.cog.last_messages:
            try:
                await self.parent_view.cog.last_messages[user_id].delete()
            except Exception:
                pass

        # ✅ If completed
        if "_" not in display_word:
            manager.set_words(player_id, None)
            all_users = manager.get_balance(all=True)
            for u in all_users:
                if u["user_id"] == user_id or u["words"] not in (None, "", "none"):
                    manager.update_balance(u["user_id"], 10000)

            if interaction.channel:
                await interaction.channel.send(
                    f"🎉 **{user.display_name}'s word was '{word.upper()}'!**\n"
                    f"👏 Congratulations to everyone who participated!\n💰 Each helper earned **+10,000**!"
                )
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass
            return

        await interaction.response.send_message(
            f"🎯 **Guessing {user.display_name}'s word!**\n\n`{display_word}`\n\nUsed letters: `{used_letters}`\n💰 You earned **+{reward}**",
            view=self.parent_view,
            ephemeral=True,
        )
        self.parent_view.cog.last_messages[user_id] = await interaction.original_response()


async def setup(bot):
    await bot.add_cog(Hangman(bot))
