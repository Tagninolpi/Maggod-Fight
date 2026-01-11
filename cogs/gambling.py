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

# canonical best->worst order you provided
NAME_ORDER = [
    "athena", "hephaestus", "hera", "megaera", "poseidon", "alecto", "hecate",
    "aphrodite", "charon", "ares", "thanatos", "persephone", "artemis", "tisiphone",
    "hades_uw", "apollo", "hermes", "cerberus", "zeus", "hades_ow"
]

def assign_gods(match, your_var: int, enemy_var: int, start_random: bool = True, rng=random):
    """
    Assigns gods to match.teams based on your_var and enemy_var.
    - match.gods must be a list of God instances (match.gods = list(match.gods.values()))
    - match.available_gods must be a copy of match.gods (mutable)
    - your_var, enemy_var in [-5,5]. Positive -> that many good; negative -> that many bad.
    - Returns (team_p1, team_p2) where each is a list of God instances (len == 5).
    - Side: player1 = match.player1_id, player2 = match.player2_id.
    - start_random: if True, starting picker is random between player1 and player2.
    """
    # --- validation ---
    if not (-5 <= your_var <= 5 and -5 <= enemy_var <= 5):
        raise ValueError("your_var and enemy_var must be between -5 and 5")

    # Prepare ordered_all according to NAME_ORDER
    all_objs = list(getattr(match, "gods", []))  # list of God instances
    name_to_god = {g.name: g for g in all_objs}
    ordered_all = []
    for name in NAME_ORDER:
        if name in name_to_god:
            ordered_all.append(name_to_god[name])
        else:
            logger.warning("Expected god name '%s' missing from match.gods", name)
    # append any gods that exist in match.gods but were not in NAME_ORDER
    for g in all_objs:
        if g.name not in NAME_ORDER:
            ordered_all.append(g)

    # Working pools
    all_pool = ordered_all.copy()
    good_pool = []
    bad_pool = []

    # Compute how many good/bad we need in pools (defaults to 7 each)
    positive_sum = max(0, your_var) + max(0, enemy_var)
    negative_sum = abs(min(0, your_var)) + abs(min(0, enemy_var))
    good_size = max(7, positive_sum)
    bad_size = max(7, negative_sum)

    # Build good_pool from top (best) in order
    i = 0
    while len(good_pool) < good_size and i < len(ordered_all):
        candidate = ordered_all[i]
        if candidate not in good_pool:
            good_pool.append(candidate)
        i += 1

    # Build bad_pool from bottom (worst) in order, skipping any already taken by good_pool
    j = 1
    while len(bad_pool) < bad_size and j <= len(ordered_all):
        candidate = ordered_all[-j]
        if candidate not in bad_pool and candidate not in good_pool:
            bad_pool.append(candidate)
        j += 1

    # Sanity clamp: ensure pools don't exceed available gods
    # (if pools cover almost all gods, it's okay — there are 20 total)
    # NOTE: we do not remove pool elements from all_pool now; removals happen when a god is chosen.

    # Prepare team containers (store God instances)
    p1 = match.player1_id
    p2 = match.player2_id
    team_p1 = []
    team_p2 = []

    # Compute per-player special needs and types
    def special_info(var):
        if var > 0:
            return ("good", var)
        elif var < 0:
            return ("bad", abs(var))
        else:
            return (None, 0)

    p1_type, p1_need = special_info(your_var)
    p2_type, p2_need = special_info(enemy_var)

    # Helper: pick and remove from pools + all_pool
    def pick_from_pool(pool_list):
        """Pick random from pool_list; remove from pool_list and from all_pool; return picked instance or None."""
        if not pool_list:
            return None
        chosen = rng.choice(pool_list)
        # remove from pool_list
        pool_list.remove(chosen)
        # also remove from all_pool if present
        if chosen in all_pool:
            all_pool.remove(chosen)
        # also ensure removed from the other pool if present
        if chosen in good_pool:
            try: good_pool.remove(chosen)
            except ValueError: pass
        if chosen in bad_pool:
            try: bad_pool.remove(chosen)
            except ValueError: pass
        return chosen

    def pick_from_all_pool():
        if not all_pool:
            return None
        chosen = rng.choice(all_pool)
        all_pool.remove(chosen)
        # remove from special pools if present
        if chosen in good_pool:
            try: good_pool.remove(chosen)
            except ValueError: pass
        if chosen in bad_pool:
            try: bad_pool.remove(chosen)
            except ValueError: pass
        return chosen

    # Alternating picks to satisfy specials
    current = rng.choice([p1, p2]) if start_random else p1
    # Loop until both special needs are zero
    while p1_need > 0 or p2_need > 0:
        if current == p1:
            if p1_need > 0:
                if p1_type == "good":
                    chosen = pick_from_pool(good_pool)
                    if chosen is None:
                        # fallback to all_pool
                        chosen = pick_from_all_pool()
                else:  # bad
                    chosen = pick_from_pool(bad_pool)
                    if chosen is None:
                        chosen = pick_from_all_pool()
                if chosen:
                    team_p1.append(chosen)
                    p1_need -= 1
            # else: nothing this turn
            current = p2
        else:  # current == p2
            if p2_need > 0:
                if p2_type == "good":
                    chosen = pick_from_pool(good_pool)
                    if chosen is None:
                        chosen = pick_from_all_pool()
                else:  # bad
                    chosen = pick_from_pool(bad_pool)
                    if chosen is None:
                        chosen = pick_from_all_pool()
                if chosen:
                    team_p2.append(chosen)
                    p2_need -= 1
            current = p1

    # Now fill remaining slots until each team has 5, alternating
    # (continue alternating from current)
    while len(team_p1) < 5 or len(team_p2) < 5:
        if current == p1:
            if len(team_p1) < 5:
                chosen = pick_from_all_pool()
                if chosen is None:
                    break  # no more gods
                team_p1.append(chosen)
            current = p2
        else:
            if len(team_p2) < 5:
                chosen = pick_from_all_pool()
                if chosen is None:
                    break
                team_p2.append(chosen)
            current = p1

    # Final shuffle of each team's order
    rng.shuffle(team_p1)
    rng.shuffle(team_p2)

    # Save to match.teams (God instances)
    match.teams = {
        match.player1_id: team_p1,
        match.player2_id: team_p2
    }

    # Remove assigned gods from match.available_gods if present
    try:
        remaining = [g for g in getattr(match, "available_gods", []) if g not in (team_p1 + team_p2)]
        match.available_gods = remaining
    except Exception:
        # If match.available_gods doesn't exist or is not a list, ignore
        logger.debug("Could not update match.available_gods; check structure.")

    return team_p1, team_p2

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
    return round((base * scale)+100)  # only the gain


class GamblingView(discord.ui.View):
    def __init__(self, user: discord.User, wealth: int):
        super().__init__(timeout=None)
        self.user = user
        self.wealth = wealth
        self.bet = 100  # default bet
        self.your_var = 0
        self.enemy_var = 0

        # Storage for button groups so we can reset styles later
        self.button_groups = {"your": [], "enemy": []} 

        # Dynamically add rows of buttons
        self.add_button_row(  range(1, 6), "your", True, "your", row=0)
        self.add_button_row(   range(1, 6), "your", False, "your", row=1)
        self.add_button_row( range(1, 6), "enemy", False, "enemy", row=2)
        self.add_button_row(  range(1, 6), "enemy", True, "enemy", row=3)

        # Bet + Start buttons
        self.add_item(self.SetBetButton(self))
        self.add_item(self.StartButton(self))

    async def update_message(self, interaction: discord.Interaction):
        v = self.your_var + self.enemy_var
        gain = true_gain(v, self.bet, self.wealth)

        embed = discord.Embed(
            title="🎲 Gambling Menu",
            description="Welcome to the gambling menu",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Your Team",
            value=f"{int(self.your_var):,d}".replace(",", " "),
            inline=True
        )
        embed.add_field(
            name="Enemy Team",
            value=f"{int(self.enemy_var):,d}".replace(",", " "),
            inline=True
        )
        embed.add_field(
            name="Bet",
            value=f"{int(self.bet):,d}".replace(",", " "),
            inline=True
        )
        embed.add_field(
            name="Potential Gain",
            value=f"{int(gain):,d}".replace(",", " "),
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    def add_button_row(self, values, team, positive, group_name, row):
        """Dynamically create a row of toggle buttons for a team (toggle per team, not per row)."""
        for v in values:
            value = v if positive else -v
            label = f"{v}"
            style = discord.ButtonStyle.success if positive else discord.ButtonStyle.danger

            button = discord.ui.Button(label=label, style=style, row=row)
            button.value = value  # store signed value in the button
 
            async def callback(interaction: discord.Interaction, btn=button, team=team):
                if interaction.user.id != self.user.id:
                    await interaction.response.send_message("❌ This menu isn’t for you!", ephemeral=True)
                    return

                # Select/deselect this button for the team
                if team == "your":
                    self.your_var = btn.value if self.your_var != btn.value else 0
                else:
                    self.enemy_var = btn.value if self.enemy_var != btn.value else 0

                # Reset all buttons in this team
                for b in self.button_groups[team]:
                    b.style = discord.ButtonStyle.success if b.value > 0 else discord.ButtonStyle.danger
                    if (team == "your" and b.value == self.your_var) or (team == "enemy" and b.value == self.enemy_var):
                        b.style = discord.ButtonStyle.blurple  # highlight selected

                await self.update_message(interaction)

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
                bet_input = discord.ui.TextInput(
                    label=f"Bet Amount (max {self.parent_view.wealth})",
                    style=discord.TextStyle.short
                )

                async def on_submit(inner_self, modal_interaction: discord.Interaction):
                    try:
                        bet = int(inner_self.bet_input.value)
                        bet = max(1, min(bet, self.parent_view.wealth))
                        self.parent_view.bet = bet
                    except ValueError:
                        self.parent_view.bet = 100
                    await self.parent_view.update_message(modal_interaction)

            await interaction.response.send_modal(BetModal())


    # --- Start button ---
    class StartButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(label="Start", style=discord.ButtonStyle.success, row=4)
            self.parent_view = parent_view

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.parent_view.user.id:
                await interaction.response.send_message("❌ This menu isn’t for you!", ephemeral=True)
                return

            # Store the result in the view
            self.parent_view.result = {
                "bet": self.parent_view.bet,
                "your_var": self.parent_view.your_var,
                "enemy_var": self.parent_view.enemy_var
            }

            await interaction.response.edit_message(
                content="✅ Gambling menu closed.",
                embed=None,
                view=None
            )
            # Stop the view
            self.parent_view.stop()



class Gambling(commands.Cog):

    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="gambling", description="Open the gambling menu")
    async def gambling(self, interaction: discord.Interaction):
        # At the start of your command
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or not(channel.category.id in Config.LOBBY_CATEGORY_ID):
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        # if not channel.name.startswith("⚔️-maggo"):
        #     await interaction.response.send_message(
        #         "❌ You must use this command in a Maggod lobby channel.",
        #         ephemeral=True
        #     )
        #     return
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
        # start

        channel = interaction.channel
        channel_id = channel.id
        from currency.money_manager import MoneyManager
        money_manager = MoneyManager()
        wealth_data = money_manager.get_balance(user_id=match.player1_id)
        wealth = wealth_data["balance"]
        if wealth<100:
            wealth =100
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

        # Wait until the user clicks Start
        await view.wait()

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict
        from utils.game_test_on_discord import gods as all_gods_template
        match = matchmaking_dict.get(channel_id)

        # Retrieve result
        result = getattr(view, "result", None)
        if result:
            bet = result["bet"]
            your_var = result["your_var"]
            enemy_var = result["enemy_var"]

            # Compute gain
            gain = true_gain(your_var + enemy_var, bet, wealth)

            # Store in match
            match.gamb_bet = bet
            match.gamb_gain = gain

        match.gods = copy.deepcopy(all_gods_template)
        match.gods = list(match.gods.values())
        match.available_gods = copy.deepcopy(match.gods)
        team_p1, team_p2 = assign_gods(match, your_var, -enemy_var, start_random=True)

        match.teams_initialized = True
        match.game_phase = "playing"
        match.money_sys_type = "gambling"

        match.ai_bot_name = "bot_overloard"

        match.turn_state = {
            "current_player": random.choice([match.player1_id, match.player2_id]),
            "turn_number": 1
        }

        # Send confirmation message
        await interaction.followup.send(
            "✅ Debug: Teams auto-assigned. The battle begins now! Use `/do` to play."
            #f"{team_p1}"
            #f"{team_p2}"
        )

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Gambling(bot))
