import re
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
        self.last_messages = {}  # user_id -> discord.Message (to delete old ephemeral views)

    @app_commands.command(name="hangman", description="Open hangman menu")
    async def hangman(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Use this command in a text channel.", ephemeral=True)
            return

        if not channel.category or not(channel.category.id in Config.LOBBY_CATEGORY_ID):
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
        # Prevent players who have not made a word from guessing
        player_data = self.manager.get_balance(user_id)
        player_word = player_data.get("words") if isinstance(player_data, dict) else None
        if not player_word or player_word.lower() in ("none", ""):
            await interaction.response.send_message(
                "❌ You must first **create your own word** before guessing others'!",
                ephemeral=True
            )
            return

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
        can_play, remaining = self.manager.can_player_guess(self.player_id, self.user_id)
        if not can_play:
            await interaction.response.send_message(
                f"⏳ You must wait **{remaining} more minutes** before guessing the word again.",
                ephemeral=True
            )
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
        label="Enter your word (max 100 letters)", placeholder="Example: magic forest", required=True, max_length=100
    )

    def __init__(self, manager, cog, user_id):
        super().__init__()
        self.manager = manager
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        word = str(self.word_input.value).strip()
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿẞß ',]+", word):
            await interaction.response.send_message(
                "❌ Invalid word! Use only standard or accented Latin letters (A-Z, é, ö, ß, etc.).",
                ephemeral=True
            )
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
            self.word = word_part.strip()
            self.guessed_letters = [
    ch for ch in guessed_part.lower()
    if ch.isalpha()
]

        else:
            self.word = data_text.strip()
            self.guessed_letters = []

        self.add_item(ChooseLetterButton(self))
        self.add_item(GuessWordButton(self))


    def get_display_word(self):
        return "".join(
            ch if ch in {" ", "'", ","}
            else ch if normalize_letter(ch) in self.guessed_letters
            else "_"
            for ch in self.word
        )



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

class GuessWordButton(discord.ui.Button):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(
            label="Guess Word",
            style=discord.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GuessWordModal(self.parent_view))
class GuessWordModal(discord.ui.Modal, title="Guess the Word / Sentence"):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

        self.guess_input = discord.ui.TextInput(
            label="Enter your guess",
            placeholder="Type any sequence of letters",
            required=True,
            max_length=len(parent_view.word)
        )
        self.add_item(self.guess_input)

    async def on_submit(self, interaction: discord.Interaction):
        guess = self.guess_input.value.strip()
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿẞß ',]+", guess):
            await interaction.response.send_message(
                "❌ Invalid input! Use only letters and spaces.", ephemeral=True
            )
            return

        def normalize(s):
            return "".join(normalize_letter(c) for c in s)

        word = self.parent_view.word
        word_n = normalize(word)
        guess_n = normalize(guess)

        user_id = self.parent_view.user_id
        player_id = self.parent_view.player_id
        manager = self.parent_view.manager

        guesser_user = await self.parent_view.bot.fetch_user(user_id)
        player_user = await self.parent_view.bot.fetch_user(player_id)

        # Only proceed if the full guessed sequence exists at least once
        if guess_n in word_n:
            # Add any new letters from the guess to guessed_letters
            for ch in guess_n:
                if ch.isalpha() and ch not in self.parent_view.guessed_letters:
                    self.parent_view.guessed_letters.append(ch)


            correct = True
            reward = 1000 * len(guess_n)
            manager.update_balance(user_id, reward)

            # Update stored word with guessed letters
            manager.set_words(player_id, f"{word}:{''.join(self.parent_view.guessed_letters)}")

            # Update display word
            display_word = self.parent_view.get_display_word()

        else:
            # Incorrect guess, no letters added
            display_word = self.parent_view.get_display_word()
            correct = False
            reward = -2000 * len(guess_n)
            manager.update_balance(user_id, reward)

        used_letters = self.parent_view.get_used_letters()

        # Public feedback
        await interaction.response.send_message(
            f"🔠 **{guesser_user.display_name}** guessed `{guess}` in **{player_user.display_name}`'s word!\n"
            f"{'✅ Correct!' if correct else '❌ Incorrect!'}\n"
            f"🧩 Current word → ```{display_word}```\n"
            f"🔤 Used letters: `{used_letters}`\n"
            f"💰 {guesser_user.display_name} {'earned' if correct else 'lost'} **{abs(reward)}**"
        )

        # Check if the full word is now revealed
        if "_" not in display_word:
            manager.set_words(player_id, None)

            # Get all participants
            player_times = manager.get_player_times(player_id)
            player_ids = player_times.keys()

            participants = []

            for pid in player_ids:
                manager.update_balance(pid, 10000)
                user_obj = await self.parent_view.bot.fetch_user(pid)
                participants.append(user_obj.display_name)

            manager.set_player_times(player_id, {})

            # Stop the game UI
            self.parent_view.stop()

            # Public win message
            await interaction.channel.send(
                f"🎉 **{player_user.display_name}'s word was `{word}`!**\n"
                f"👏 Congratulations to everyone who participated: {', '.join(participants)} 🎊\n"
                f"💰 Each helper earned **+10,000**!"
            )

            # Reminder to create a new word
            await interaction.channel.send(
                f"📝 {player_user.mention}, please **create a new word or sentence** using `/hangman` ➕"
            )

            return





class ChooseLetterButton(discord.ui.Button):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        super().__init__(label="Choose Letter", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LetterInputModal(self.parent_view))

def normalize_letter(letter: str) -> str:
    """Return a normalized lowercase ASCII base for accented letters."""
    replacements = {
        "a": ["a", "à", "á", "â", "ä", "ã", "å", "ā"],
        "c": ["c", "ç"],
        "e": ["e", "è", "é", "ê", "ë", "ē"],
        "i": ["i", "ì", "í", "î", "ï", "ī"],
        "o": ["o", "ò", "ó", "ô", "ö", "õ", "ø", "ō"],
        "u": ["u", "ù", "ú", "û", "ü", "ū"],
        "y": ["y", "ÿ", "ý"],
        "s": ["s", "ß"],
        "n": ["n", "ñ"],
    }
    for base, variants in replacements.items():
        if letter.lower() in variants:
            return base
    return letter.lower()

class LetterInputModal(discord.ui.Modal, title="Guess a Letter"):
    letter_input = discord.ui.TextInput(
        label="Enter a single letter", placeholder="A-Z", required=True, min_length=1, max_length=1
    )

    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        letter = self.letter_input.value
        if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿẞß]", letter):
            await interaction.response.send_message("❌ Invalid input! Enter a single valid letter.", ephemeral=True)
            return
        
        letter_lower = normalize_letter(letter)

        if letter_lower in self.parent_view.guessed_letters:
            await interaction.response.send_message(
                f"⚠️ Letter `{letter}` already used: `{self.parent_view.get_used_letters()}`", ephemeral=True
            )
            return

        self.parent_view.guessed_letters.append(letter_lower)
        word = self.parent_view.word
        user_id = self.parent_view.user_id
        player_id = self.parent_view.player_id
        manager = self.parent_view.manager

        correct = any(normalize_letter(ch) == letter_lower for ch in word)
        reward = 2000 if correct else 1000
        manager.update_balance(user_id, reward)

        new_text = f"{word}:{''.join(self.parent_view.guessed_letters)}"
        manager.set_words(player_id, new_text)

        display_word = self.parent_view.get_display_word()


        used_letters = self.parent_view.get_used_letters()
        player_user = await self.parent_view.bot.fetch_user(player_id)
        guesser_user = await self.parent_view.bot.fetch_user(user_id)

        # Record the guess in the cooldown system
        self.parent_view.manager.add_player_guess_time(player_id, user_id)


        # Delete old ephemeral message (failsafe)
        if user_id in self.parent_view.cog.last_messages:
            try:
                await self.parent_view.cog.last_messages[user_id].delete()
            except Exception:
                pass

        # ✅ If the word is completed
        if "_" not in display_word:
            manager.set_words(player_id, None)
            player_times = manager.get_player_times(player_id)
            player_ids = player_times.keys()


            participants = []

            for pid in player_ids:
                manager.update_balance(pid, 10000)
                user_obj = await self.parent_view.bot.fetch_user(pid)
                participants.append(user_obj.display_name)
            manager.set_player_times(player_id, {})


            # Stop the view and announce publicly
            self.parent_view.stop()
            try:
                await interaction.message.delete()
            except Exception:
                pass

            if interaction.channel:
                await interaction.channel.send(
                    f"🎉 **{player_user.display_name}'s word was `{word}`!**\n"
                    f"👏 Congratulations to everyone who participated: {', '.join(participants)} 🎊\n"
                    f"💰 Each helper earned **+10,000**!"
                )
                   # 🧩 Follow-up reminder for the player to make a new word
                await interaction.channel.send(
                    f"📝 {player_user.mention}, please **create a new word or sentence** using `/hangman` ➕"
                )
            return

        # ✅ Otherwise, announce the guess publicly instead of updating ephemeral
        # After sending the public message:
        self.parent_view.stop()  # close view
        try:
            await interaction.message.delete()
        except Exception:
            pass

        if interaction.channel:
            correctness = "✅ Correct!" if correct else "❌ Incorrect!"
            await interaction.channel.send(
                f"🔠 **{guesser_user.display_name}** guessed `{letter.upper()}` "
                f"in **{player_user.display_name}**'s word!\n"
                f"{correctness}\n\n"
                f"🧩 Current word: ```\n{display_word}\n```"

                f"🔤 Used letters: `{used_letters}`\n"
                f"💰 {guesser_user.display_name} earned **+{reward}**"
            )

        # Save reference for deletion next time
        self.parent_view.cog.last_messages[user_id] = await interaction.original_response()

        # With this
        try:
            await interaction.response.defer()  # mark as responded
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(Hangman(bot))
