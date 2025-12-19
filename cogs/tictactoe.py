import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import logging
from currency.money_manager import MoneyManager

logger = logging.getLogger(__name__)

# -------------------- GLOBAL STATE --------------------

TTT_QUEUE: list[int] = []                 # waiting player IDs
ACTIVE_GAMES: dict[int, int] = {}         # player_id -> opponent_id
MATCHMAKING_LOCK = asyncio.Lock()         # serialize matchmaking notifications


# -------------------- COG --------------------

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = MoneyManager()

    @app_commands.command(name="ttt", description="Play Tic-Tac-Toe")
    async def ttt(self, interaction: discord.Interaction):
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Use this command in a text channel.", ephemeral=True
            )
            return

        user_id = interaction.user.id

        if user_id in ACTIVE_GAMES or user_id in TTT_QUEUE:
            await interaction.response.send_message(
                "❌ You are already in a Tic-Tac-Toe game or queue.", ephemeral=True
            )
            return

        async with MATCHMAKING_LOCK:
            if not TTT_QUEUE:
                TTT_QUEUE.append(user_id)
                try:
                    await interaction.response.send_message(
                        "⏳ You are now in the Tic-Tac-Toe queue. Waiting for an opponent...", ephemeral=True
                    )
                except discord.errors.HTTPException as e:
                    logger.warning(f"Rate-limited while sending ephemeral queue: {e}")
                return

            # Match found
            opponent_id = TTT_QUEUE.pop(0)

            # Register active game
            ACTIVE_GAMES[user_id] = opponent_id
            ACTIVE_GAMES[opponent_id] = user_id

            # Notify opponent via DM (safely)
            try:
                opponent = await self.bot.fetch_user(opponent_id)
                await asyncio.sleep(0.3)  # small delay to reduce rate-limit risk
                await opponent.send(f"🎮 You have been matched for **Tic-Tac-Toe** with {interaction.user.mention}!")
            except discord.errors.HTTPException:
                logger.warning(f"Could not send DM to {opponent_id}, possibly rate-limited.")

            # Notify current player (ephemeral)
            try:
                await interaction.response.send_message(
                    f"🎮 Match found! You are playing against <@{opponent_id}>", ephemeral=True
                )
            except discord.errors.HTTPException as e:
                logger.warning(f"Rate-limited while sending ephemeral match message: {e}")

        # Start game in THIS channel
        players = [user_id, opponent_id]
        random.shuffle(players)

        view = TicTacToeView(
            bot=self.bot,
            manager=self.manager,
            channel=interaction.channel,
            p1=players[0],
            p2=players[1]
        )

        try:
            msg = await interaction.channel.send(view.get_status_text(), view=view)
            view.message = msg
        except discord.errors.HTTPException as e:
            logger.warning(f"Rate-limited while sending game message: {e}")
            # Remove from active games if cannot send
            ACTIVE_GAMES.pop(user_id, None)
            ACTIVE_GAMES.pop(opponent_id, None)


# -------------------- VIEW --------------------

class TicTacToeView(discord.ui.View):
    def __init__(self, bot, manager, channel, p1, p2):
        super().__init__(timeout=600)
        self.bot = bot
        self.manager = manager
        self.channel = channel

        self.players = [p1, p2]
        self.turn = p1
        self.colors = {p1: discord.ButtonStyle.primary, p2: discord.ButtonStyle.danger}
        self.board = [None] * 9
        self.message: discord.Message | None = None

        for i in range(9):
            self.add_item(TTTButton(i, self, row=i // 3))

    def get_status_text(self) -> str:
        return f"🎮 **Tic-Tac-Toe**\n\n<@{self.turn}> it is your turn"

    def check_winner(self):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in wins:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        if all(self.board):
            return "draw"
        return None

    async def end_game(self, winner=None, timeout=False):
        for child in self.children:
            child.disabled = True

        p1, p2 = self.players

        if winner == "draw":
            self.manager.update_balance(p1, 7500)
            self.manager.update_balance(p2, 7500)
            text = "🤝 **Draw!** Both players receive **+7,500**"
        else:
            loser = p2 if winner == p1 else p1
            self.manager.update_balance(winner, 10000)
            self.manager.update_balance(loser, 5000)
            if timeout:
                text = f"⏱️ <@{loser}> took too long!\n🏆 <@{winner}> wins **(+10,000)**"
            else:
                text = f"🏆 <@{winner}> wins **(+10,000)**\n💀 <@{loser}> gets **+5,000**"

        try:
            if self.message:
                await self.message.edit(content=text, view=self)
        except discord.errors.HTTPException:
            logger.warning("Rate-limited while editing end-game message")

        ACTIVE_GAMES.pop(p1, None)
        ACTIVE_GAMES.pop(p2, None)
        self.stop()

    async def on_timeout(self):
        winner = self.players[1] if self.turn == self.players[0] else self.players[0]
        await self.end_game(winner=winner, timeout=True)


# -------------------- BUTTON --------------------

class TTTButton(discord.ui.Button):
    def __init__(self, index, view, row):
        super().__init__(style=discord.ButtonStyle.secondary, label=" ", row=row)
        self.index = index
        self.view_ref: TicTacToeView = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.turn:
            try:
                await interaction.response.send_message("❌ It is not your turn.", ephemeral=True)
            except discord.errors.HTTPException:
                pass
            return

        if self.view_ref.board[self.index] is not None:
            try:
                await interaction.response.send_message("❌ This cell is already taken.", ephemeral=True)
            except discord.errors.HTTPException:
                pass
            return

        # Place move
        player = interaction.user.id
        self.view_ref.board[self.index] = player
        self.style = self.view_ref.colors[player]
        self.disabled = True

        result = self.view_ref.check_winner()
        if result:
            try:
                await interaction.response.defer()
            except discord.errors.HTTPException:
                pass
            await self.view_ref.end_game(winner=None if result == "draw" else result)
            return

        # Switch turn
        self.view_ref.turn = self.view_ref.players[1] if self.view_ref.turn == self.view_ref.players[0] else self.view_ref.players[0]

        try:
            await interaction.response.edit_message(content=self.view_ref.get_status_text(), view=self.view_ref)
        except discord.errors.HTTPException:
            pass


# -------------------- SETUP --------------------

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
