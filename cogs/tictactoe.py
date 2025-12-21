import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import logging
from currency.money_manager import MoneyManager

logger = logging.getLogger(__name__)

# -------------------- GLOBAL STATE --------------------
QUEUE: list[dict] = []  # {"user_id": int, "channel": TextChannel, "timeout_task": Task}
ACTIVE_GAMES: dict[int, int] = {}  # player_id -> opponent_id
MATCHMAKING_LOCK = asyncio.Lock()

# ======================================================
#                        COG
# ======================================================
class GridGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.manager = MoneyManager()

    @app_commands.command(name="ttt", description="Play the 5×5 button game")
    async def gridgame(self, interaction: discord.Interaction):
        if not interaction.channel or not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("❌ Use this in a text channel.", ephemeral=True)
            return

        user_id = interaction.user.id

        # Remove from old game
        if user_id in ACTIVE_GAMES:
            opponent_id = ACTIVE_GAMES.pop(user_id)
            ACTIVE_GAMES.pop(opponent_id, None)
            try:
                await interaction.channel.send(
                    f"⚠️ <@{opponent_id}> has been removed from the current game because <@{user_id}> rejoined the queue."
                )
            except:
                pass

        # Remove from queue if already waiting
        for entry in QUEUE:
            if entry["user_id"] == user_id:
                QUEUE.remove(entry)
                try:
                    entry["timeout_task"].cancel()
                except:
                    pass
                break

        # Queue logic
        async with MATCHMAKING_LOCK:
            if not QUEUE:
                timeout_task = asyncio.create_task(self.queue_timeout(user_id, interaction.channel))
                QUEUE.append({"user_id": user_id, "channel": interaction.channel, "timeout_task": timeout_task})
                await interaction.response.send_message("⏳ Waiting for an opponent...", ephemeral=True)
                return

            # Match found
            entry = QUEUE.pop(0)
            entry["timeout_task"].cancel()
            opponent = entry["user_id"]

            ACTIVE_GAMES[user_id] = opponent
            ACTIVE_GAMES[opponent] = user_id

            await interaction.response.send_message(
                f"🎮 Match found! You're playing <@{opponent}>", ephemeral=True
            )
            await interaction.channel.send(
                f"🎮 <@{opponent}> and <@{user_id}>, your 5×5 game is starting!"
            )

        # Start game
        players = [user_id, opponent]
        random.shuffle(players)

        view = GridGameView(self.bot, self.manager, interaction.channel, players[0], players[1])
        msg = await interaction.channel.send(view.get_status_text(), view=view)
        view.message = msg

    async def queue_timeout(self, user_id, channel):
        await asyncio.sleep(120)
        for entry in QUEUE:
            if entry["user_id"] == user_id:
                QUEUE.remove(entry)
                try:
                    await channel.send(f"⌛ <@{user_id}> was removed from the queue due to inactivity.")
                except:
                    pass
                break


# ======================================================
#                     GAME VIEW
# ======================================================
class GridGameView(discord.ui.View):
    def __init__(self, bot, manager, channel, p1, p2):
        super().__init__(timeout=600)
        self.bot = bot
        self.manager = manager
        self.channel = channel
        self.players = [p1, p2]
        self.turn = p1

        self.colors = {p1: discord.ButtonStyle.primary, p2: discord.ButtonStyle.danger}

        # 5×5 = 25 cells
        self.board = [None] * 25
        self.message = None

        for i in range(25):
            self.add_item(GridButton(i, self, row=i // 5))

    # -----------------------------------------
    def get_status_text(self):
        return f"🎮 **5×5 Button Game**\n<@{self.turn}> your turn."

    # -----------------------------------------
    def compute_score(self):
        """
        Compute both players' money from all sequences:
        rows, columns, diagonals (both directions), length >= 3.
        Only longest contiguous segment per sequence is counted, no overlaps.
        """
        SIZE = 5
        reward = {3: 450, 4: 1800, 5: 4650}

        money = {self.players[0]: 0, self.players[1]: 0}

        lines = []

        # --- Rows ---
        for r in range(SIZE):
            lines.append([r * SIZE + c for c in range(SIZE)])

        # --- Columns ---
        for c in range(SIZE):
            lines.append([r * SIZE + c for r in range(SIZE)])

        # --- Diagonals ↘ (top-left → bottom-right) ---
        for r in range(SIZE):
            for c in range(SIZE):
                diag = []
                rr, cc = r, c
                while rr < SIZE and cc < SIZE:
                    diag.append(rr * SIZE + cc)
                    rr += 1
                    cc += 1
                if len(diag) >= 3:
                    lines.append(diag)

        # --- Diagonals ↙ (top-right → bottom-left) ---
        for r in range(SIZE):
            for c in range(SIZE):
                diag = []
                rr, cc = r, c
                while rr < SIZE and cc >= 0:
                    diag.append(rr * SIZE + cc)
                    rr += 1
                    cc -= 1
                if len(diag) >= 3:
                    lines.append(diag)

        # --- Evaluate all lines ---
        for line in lines:
            vals = [self.board[i] for i in line]

            current = None
            length = 0

            for v in vals + [None]:  # sentinel to flush last streak
                if v == current and v is not None:
                    length += 1
                else:
                    if current is not None and length >= 3:
                        # only the longest contiguous sequence counts
                        length = min(length, 5)
                        money[current] += reward[length]
                    current = v
                    length = 1 if v is not None else 0

        return money


    # -----------------------------------------
    async def end_game(self, timed_out=False):
        for child in self.children:
            child.disabled = True

        p1, p2 = self.players

        if timed_out:
            # no rewards if someone leaves or times out
            text = "⏱️ Game ended due to timeout. Nobody receives rewards."
        else:
            scores = self.compute_score()
            p1_money = scores[p1] * 150
            p2_money = scores[p2] * 150

            self.manager.update_balance(p1, p1_money)
            self.manager.update_balance(p2, p2_money)

            text = (
                f"🏁 **Game Over!**\n\n"
                f"<@{p1}> earns **{p1_money}**\n"
                f"<@{p2}> earns **{p2_money}**"
            )

        ACTIVE_GAMES.pop(p1, None)
        ACTIVE_GAMES.pop(p2, None)

        if self.message:
            await self.message.edit(content=text, view=self)

        self.stop()

    # -----------------------------------------
    async def on_timeout(self):
        await self.end_game(timed_out=True)


# ======================================================
#                     BUTTON
# ======================================================
class GridButton(discord.ui.Button):
    def __init__(self, index, view, row):
        super().__init__(style=discord.ButtonStyle.secondary, label="-", row=row)
        self.index = index
        self.view_ref: GridGameView = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view_ref.turn:
            await interaction.response.send_message("❌ Not your turn.", ephemeral=True)
            return

        if self.view_ref.board[self.index] is not None:
            await interaction.response.send_message("❌ Already taken.", ephemeral=True)
            return

        player = interaction.user.id

        # Place move
        self.view_ref.board[self.index] = player
        self.style = self.view_ref.colors[player]
        self.disabled = True

        # Check if board is full → end game
        if all(self.view_ref.board):
            await interaction.response.defer()
            await self.view_ref.end_game()
            return

        # Next turn
        p1, p2 = self.view_ref.players
        self.view_ref.turn = p2 if self.view_ref.turn == p1 else p1

        await interaction.response.edit_message(
            content=self.view_ref.get_status_text(),
            view=self.view_ref
        )


# ======================================================
#                     SETUP
# ======================================================
async def setup(bot):
    await bot.add_cog(GridGame(bot))
