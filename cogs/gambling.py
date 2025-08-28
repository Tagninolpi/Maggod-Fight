import discord
from discord.ext import commands
from discord import app_commands
import random
import copy
import logging
import asyncio

from utils.game_test_on_discord import gods as all_gods_template
from bot.utils import update_lobby_status_embed
from bot.config import Config
import asyncio
logger = logging.getLogger(__name__)


# --- Gain function ---
def true_gain(v, bet, wealth, reduction_neg=0.5, reduction_pos=0.2):
    fraction = bet / wealth
    if v > 0:
        base = bet * (89 - 8 * v) / 90.0
        scale = 1 - fraction * reduction_pos
    elif v == 0:
        base = bet
        scale = 1 - fraction * reduction_pos
    else:  # v < 0
        base = bet * (-v + 1)
        scale = 1 - fraction * reduction_neg
    return base * scale  # only the gain


class GamblingView(discord.ui.View):
    def __init__(self, user: discord.User, wealth: int):
        super().__init__(timeout=None)
        self.user = user
        self.wealth = wealth
        self.bet = 100  # default bet
        self.your_var = 0
        self.enemy_var = 0

        # Storage for button groups so we can reset styles later
        self.button_groups = {"your_good": [], "your_bad": [], "enemy_good": [], "enemy_bad": []}

        # Dynamically add rows of buttons
        self.add_button_row("Your Good",  range(1, 6), "your", True, "your_good", row=0)
        self.add_button_row("Your Bad",   range(1, 6), "your", False, "your_bad", row=1)
        self.add_button_row("Enemy Good", range(1, 6), "enemy", False, "enemy_good", row=2)
        self.add_button_row("Enemy Bad",  range(1, 6), "enemy", True, "enemy_bad", row=3)

        # Bet + Start buttons
        self.add_item(self.SetBetButton(self))
        self.add_item(self.StartButton())

    async def update_message(self, interaction: discord.Interaction):
        v = self.your_var + self.enemy_var
        gain = true_gain(v, self.bet, self.wealth)

        embed = discord.Embed(
            title="🎲 Gambling Menu",
            description="Welcome to the gambling menu",
            color=discord.Color.gold()
        )
        embed.add_field(name="Your Team", value=str(self.your_var), inline=True)
        embed.add_field(name="Enemy Team", value=str(self.enemy_var), inline=True)
        embed.add_field(name="Bet", value=f"{self.bet}", inline=True)
        embed.add_field(name="Potential Gain", value=f"{gain:.2f}", inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

    def add_button_row(self, label_prefix, values, team, positive, group_name, row):
        """Dynamically create a row of toggle buttons for a team."""
        for v in values:
            label = f"{v}"
            value = v if positive else -v
            style = discord.ButtonStyle.success if positive else discord.ButtonStyle.danger

            async def callback(interaction: discord.Interaction, value=value, group_name=group_name, team=team):
                if interaction.user.id != self.user.id:
                    await interaction.response.send_message("❌ This menu isn’t for you!", ephemeral=True)
                    return

                # Toggle: if same button clicked again → reset to 0
                already_selected = False
                for btn in self.button_groups[group_name]:
                    if btn.label == str(abs(value)) and btn.style == discord.ButtonStyle.blurple:
                        already_selected = True
                        break

                # Reset styles in this group
                for btn in self.button_groups[group_name]:
                    btn.style = discord.ButtonStyle.success if positive else discord.ButtonStyle.danger

                if already_selected:
                    # Turn off selection
                    if team == "your":
                        self.your_var = 0
                    else:
                        self.enemy_var = 0
                else:
                    # Highlight selected
                    for btn in self.button_groups[group_name]:
                        if btn.label == str(abs(value)):
                            btn.style = discord.ButtonStyle.blurple
                    if team == "your":
                        self.your_var = value
                    else:
                        self.enemy_var = value

                await self.update_message(interaction)

            button = discord.ui.Button(label=label, style=style, row=row)
            button.callback = callback
            self.button_groups[group_name].append(button)
            self.add_item(button)

    # --- Bet button ---
    class SetBetButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(label="Set Bet", style=discord.ButtonStyle.primary, row=4)
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.parent_view.user.id:
                await interaction.response.send_message("❌ This menu isn’t for you!", ephemeral=True)
                return

            class BetModal(discord.ui.Modal, title="Set Your Bet"):
                bet_input = discord.ui.TextInput(label="Bet Amount", style=discord.TextStyle.short)

                async def on_submit(inner_self, modal_interaction: discord.Interaction):
                    try:
                        self.parent_view.bet = int(inner_self.bet_input.value)
                    except ValueError:
                        self.parent_view.bet = 100
                    await self.parent_view.update_message(modal_interaction)

            await interaction.response.send_modal(BetModal())

    # --- Start button ---
    class StartButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Start", style=discord.ButtonStyle.success, row=4)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="✅ Gambling menu closed.",
                embed=None,
                view=None
            )

class Gambling(commands.Cog):

    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="gambling", description="")
    async def gambling(self, interaction: discord.Interaction):
        # At the start of your command
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

        if not channel.name.startswith("⚔️-maggod-lobby-"):
            await interaction.response.send_message(
                "❌ You must use this command in a Maggod lobby channel.",
                ephemeral=True
            )
            return
        from bot.utils import matchmaking_dict
        match = matchmaking_dict.get(interaction.channel.id)
        if not match or interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.response.send_message(
                "❌ You are not a participant in this match.",
                ephemeral=True
            )
            return

        if not match or match.game_phase != "gambling":
            await interaction.response.send_message(
                f"❌ You can't use this command now (required phase: ready).",
                ephemeral=True
            )
            return
        if match.start_view:
            await interaction.response.send_message(
                f"❌ You can't use this command now, opponent is choosing.",
                ephemeral=True
            )
            return
        match.start_view = True
        # start
        await interaction.response.defer(ephemeral=False)  # or ephemeral=True if needed

        channel = interaction.channel
        channel_id = channel.id

        wealth = 10000  # hard-coded for now
        view = GamblingView(interaction.user, wealth)

        embed = discord.Embed(
            title="🎲 Gambling Menu",
            description="Welcome to the gambling menu",
            color=discord.Color.gold()
        )
        embed.add_field(name="Your Team", value="0", inline=True)
        embed.add_field(name="Enemy Team", value="0", inline=True)
        embed.add_field(name="Bet", value="100", inline=True)
        embed.add_field(name="Potential Gain", value="0.00", inline=False)

        await interaction.response.send_message(embed=embed, view=view)

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict
        from utils.game_test_on_discord import gods as all_gods_template

        match = matchmaking_dict.get(channel_id)

        # Common setup for both modes
        match.gods = copy.deepcopy(all_gods_template)
        match.gods = list(match.gods.values())
        match.available_gods = copy.deepcopy(match.gods)

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Gambling(bot))
