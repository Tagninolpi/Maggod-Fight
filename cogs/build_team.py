import discord
from discord.ext import commands
from discord import app_commands
import random
import copy
import logging
import asyncio

from database.manager import db_manager
from utils.game_test_on_discord import gods as all_gods_template
from bot.utils import update_lobby_status_embed
from bot.config import Config
import asyncio

logger = logging.getLogger(__name__)
DEBUG_SKIP_BUILD = False  # global variable
class StartChoiceView(discord.ui.View):
    def __init__(self, match, initiator_id, timeout=60):
        super().__init__(timeout=timeout)
        self.match = match
        self.initiator_id = initiator_id
        self.choice_made = asyncio.Event()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message(
                "❌ Only the player who started the game can make this choice.",
                ephemeral=True
            )
            return False
        return True

    def disable_all_buttons(self):
        """Manually disable all buttons in this view."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Skip Team Building", style=discord.ButtonStyle.red)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global DEBUG_SKIP_BUILD
        DEBUG_SKIP_BUILD = True

        self.disable_all_buttons()
        await interaction.response.edit_message(content="✅ Skipping team building phase!", view=self)

        self.choice_made.set()
        self.stop()

    @discord.ui.button(label="Do Team Building", style=discord.ButtonStyle.green)
    async def build_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global DEBUG_SKIP_BUILD
        DEBUG_SKIP_BUILD = False

        self.disable_all_buttons()
        await interaction.response.edit_message(content="✅ Proceeding with team building phase!", view=self)

        self.choice_made.set()
        self.stop()

class GodSelectionView(discord.ui.View):
    """View for selecting gods during team building."""

    def __init__(self, all_gods: list, available_gods: list, allowed_user: discord.Member,
                 picked_gods: dict, player1_id: int, player2_id: int):
        super().__init__(timeout=300)
        self.allowed_user = allowed_user
        self.selected_god = None
        self.picked_gods = picked_gods  # expected: {player_id: [god_names]}
        self.player1_id = player1_id
        self.player2_id = player2_id

        gods_to_show = all_gods[:25]  # Discord's limit per view
        for i, god in enumerate(gods_to_show):
            row = i // 5
            self.add_item(self.make_button(god, available_gods, row))

    def make_button(self, god, available_gods, row: int):
        """Create a button with proper style and disabled state."""
        label = god.name + "⠀" * max(0, 11 - len(god.name))
        disabled = False
        style = discord.ButtonStyle.secondary  # Default grey

        # Check if already picked by Player 1
        bot_id = 123  # ID of the bot player

        # Check if already picked by Player 1
        if god.name in self.picked_gods.get(self.player1_id, []):
            style = discord.ButtonStyle.success  # Green
            disabled = True

        # Check if already picked by Player 2 (human or bot)
        elif god.name in self.picked_gods.get(self.player2_id, []) or (
            self.player2_id == bot_id and god.name in self.picked_gods.get(bot_id, [])
        ):
            style = discord.ButtonStyle.danger  # Red
            disabled = True

        # Available to pick
        elif god in available_gods:
            style = discord.ButtonStyle.primary  # Blue
            disabled = False

        # Not available
        else:
            style = discord.ButtonStyle.secondary  # Grey
            disabled = True


        button = discord.ui.Button(label=label, style=style, row=row, disabled=disabled)

        # Only clickable if available
        if not disabled:
            async def callback(interaction: discord.Interaction):
                if interaction.user != self.allowed_user:
                    await interaction.response.send_message(
                        "⚠️ You're not allowed to pick right now.",
                        ephemeral=True
                    )
                    return

                # Record pick in correct player's list
                self.picked_gods.setdefault(interaction.user.id, []).append(god.name)
                self.selected_god = god
                self.stop()
                await interaction.response.send_message(
                    f"✅ **{interaction.user.display_name}** selected **{god.name}**! "
                    f"(HP: {god.hp}, DMG: {god.dmg})",
                    ephemeral=True
                )

            button.callback = callback

        return button

class BuildTeam(commands.Cog):
    """Cog for building teams in Maggod Fight."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="start", description="Start team building for a Maggod Fight match.")
    async def start_build(self, interaction: discord.Interaction):
        """Start the team building phase."""
        # At the start of your command
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        if not channel.name.startswith("🔘・maggod-fight-lobby-"):
            await interaction.response.send_message(
                "❌ You must use this command in a Maggod Fight lobby channel.",
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

        if not match or match.game_phase != "ready":
            await interaction.response.send_message(
                f"❌ You can't use this command now (required phase: ready).",
                ephemeral=True
            )
            return
        
        # start
        await interaction.response.defer(ephemeral=False)  # or ephemeral=True if needed

        channel = interaction.channel
        channel_id = channel.id

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict
        from utils.game_test_on_discord import gods as all_gods_template

        match = matchmaking_dict.get(channel_id)

        # Common setup for both modes
        match.gods = copy.deepcopy(all_gods_template)
        match.gods = list(match.gods.values())
        match.available_gods = match.gods
        if match.solo_mode:
            match.teams = {
                match.player1_id: [],
                "bot": []
                }
        else:
            match.teams = {
                match.player1_id: [],
                match.player2_id: []
                }
        
        # ✅ Restrict buttons to command initiator
        view = StartChoiceView(match, initiator_id=interaction.user.id)
        await interaction.followup.send("Choose how to start the game:", view=view)
        try:
            await asyncio.wait_for(view.choice_made.wait(), timeout=60)
        except asyncio.TimeoutError:
            return await interaction.followup.send("⌛ No choice made. Do /start again.", ephemeral=True)


        if DEBUG_SKIP_BUILD:
            # Assign 5 gods per player (random or predefined)
            gods_list = match.gods
            random.shuffle(gods_list)

            match.teams = {
                match.player1_id: gods_list[:5],
                match.player2_id: gods_list[5:10]
            }
            match.available_gods = gods_list[10:]  # remaining gods

            match.teams_initialized = True
            match.game_phase = "playing"

            match.turn_state = {
                "current_player": random.choice([match.player1_id, match.player2_id]),
                "turn_number": 1
            }

            # Send confirmation message
            await interaction.followup.send(
                "✅ Debug: Teams auto-assigned. The battle begins now! Use `/do_turn` to play."
            )
            await self.show_teams(interaction.channel, match)
            return  # skip the rest of /start normal flow

        
        # 🧑‍🤝‍🧑 Normal team building flow
        match.next_picker = random.choice([match.player1_id, match.player2_id])
        match.teams_initialized = True
        match.game_phase = "building"
        asyncio.create_task(update_lobby_status_embed(self.bot))

        logger.info(f"Team building started in channel {channel_id}")

        embed = discord.Embed(
            title="🎮 Team Building Phase",
            description="The draft begins! Each player will select 5 gods for their team.",
            color=0x00ff00
        )
        embed.add_field(
            name="⚔️ Players",
            value=f"**Player 1:** {match.player1_name}\n**Player 2:** {match.player2_name}",
            inline=False
        )
        embed.add_field(
            name="🎯 Draft Rules",
            value="• Each player picks 5 gods\n• No god can be picked twice\n• First picker is chosen randomly\n• Use `/choose` to select your gods",
            inline=False
        )
        embed.add_field(
            name="🏛️ Available Gods",
            value=f"20 unique Greek gods are available\nEach has different HP, damage, and abilities!",
            inline=False
        )

        await interaction.followup.send(embed=embed)
        if match.next_picker == "bot":
            await interaction.followup.send(f"<@{match.player1_id}>, Use `/choose` so the bot can pick it's first god.")
        else:
            await interaction.followup.send(f"<@{match.next_picker}>, you're up! Use `/choose` to pick your first god.")
        match.turn_state = {
        "current_player": match.next_picker,
        "turn_number": 1
        }
        logger.info("Current matchmaking_dict:")
        for cid, match in matchmaking_dict.items():
            logger.info(f"Channel {cid}: Player1={match.player1_name} ({match.player1_id}), "
                        f"Player2={match.player2_name} ({match.player2_id}), "
                        f"Phase={match.game_phase}")

    @app_commands.command(name="choose", description="Choose a god for your team.")
    async def choose(self, interaction: discord.Interaction):
        """Choose a god for the team."""
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        if not channel.name.startswith("🔘・maggod-fight-lobby-"):
            await interaction.response.send_message(
                "❌ You must use this command in a Maggod Fight lobby channel.",
                ephemeral=True
            )
            return
        from bot.utils import matchmaking_dict
        match = matchmaking_dict.get(interaction.channel.id)
        if match is None:
            logger.warning(f"Match not found for channel {interaction.channel.id} during /choose by {interaction.user.id}")
            await interaction.response.send_message(
                "❌ This match no longer exists in this channel.",
                ephemeral=True
            )
            return

        if interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.response.send_message(
                "❌ You are not a participant in this match.",
                ephemeral=True
            )
            return

        if not match or match.game_phase != "building":
            await interaction.response.send_message(
                f"❌ You can't use this command now (required phase: building).",
                ephemeral=True
            )
            return
        
        if match and match.turn_in_progress:
            await interaction.response.send_message(
                "❌ A turn is already in progress. Please choose a god.",
                ephemeral=True
            )
            return

        # start
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=False)  # or ephemeral=True if needed
            except discord.NotFound:
                logger.warning("Interaction expired before defer in /choose")            
        channel_id = channel.id

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel_id)
        # Inside your /choose command, replace the main selection logic with a while loop
        match.turn_in_progress = True

        while True:
            if match.solo_mode and match.next_picker == "bot":
                chosen = random.choice(match.available_gods)
                match.teams.setdefault(123, []).append(chosen)
                match.picked_gods[123] = chosen.name
                match.available_gods.remove(chosen)
                logger.info(f"Bot chose {chosen.name} in channel {channel_id}")

            else:
                if interaction.user.id != match.next_picker:
                    await interaction.followup.send(
                        f"⏳ Please wait for your turn. It's <@{match.next_picker}>'s turn.",
                        ephemeral=True
                    )


                # Create and show the god selection view
                view = GodSelectionView(
                    all_gods=match.gods,
                    available_gods=match.available_gods,
                    allowed_user=interaction.user,
                    picked_gods=match.picked_gods,
                    player1_id=match.player1_id,
                    player2_id=match.player2_id
                )

                embed = discord.Embed(
                    title="🏛️ Choose Your God",
                    description="Select a god for your team from the available options.",
                    color=0x00ff00
                )
                embed.add_field(
                    name="📊 Current Status",
                    value=f"Available Gods: {len(match.available_gods)}\n"
                        f"Your Team: {len(match.teams[interaction.user.id])}/5 gods",
                    inline=False
                )

                await interaction.followup.send(
                    f"<@{interaction.user.id}>, select your god:",
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

                # Wait for the player to pick or timeout
                try:
                    await asyncio.wait_for(view.wait(), timeout=900)
                except asyncio.TimeoutError:
                    # Timeout handling here
                    view.selected_god = None
                # 15 minutes

                if view.selected_god is None:
                    # Timeout handling
                    await interaction.followup.send(
                        "⏱️ Selection timed out. Match has been reset.",
                        ephemeral=True
                    )
                    match.game_phase = "Waiting for first player"
                    asyncio.create_task(update_lobby_status_embed(self.bot))
                    del matchmaking_dict[channel_id]
                    logger.info(f"Match timed out in channel {channel_id}")
                    return

                chosen = view.selected_god
                match.teams.setdefault(interaction.user.id, []).append(chosen)
                match.picked_gods[interaction.user.id] = chosen.name
                match.available_gods.remove(chosen)
                logger.info(f"Player {interaction.user.id} chose {chosen.name} in channel {channel_id}")

            # Send selection announcement
            embed = discord.Embed(
                title="⚡ God Selected!",
                description=f"**{interaction.user.display_name if not match.solo_mode else 'Bot'}** has chosen their god.",
                color=0x00bfff
            )
            embed.add_field(
                name="🏛️ Selected God",
                value=f"**{chosen.name}**\nHP: {chosen.hp} | DMG: {chosen.dmg}",
                inline=True
            )
            await channel.send(embed=embed)

            # Switch to next picker
            if match.solo_mode and match.next_picker == "bot":
                match.next_picker = match.player1_id
            else:
                match.next_picker = match.player1_id if match.next_picker == match.player2_id else match.player2_id

            # Check if both teams are complete
            p1_team = match.teams[match.player1_id]
            p2_team = match.teams[match.player2_id]

            if len(p1_team) == 5 and len(p2_team) == 5:
                match.game_phase = "playing"
                asyncio.create_task(update_lobby_status_embed(self.bot))
                await channel.send("✅ **Both teams are complete! Let the battle begin!**")
                await self.show_teams(channel, match)
                await channel.send(f"<@{match.next_picker}>, use `/do_turn` to take the first move.")
                match.turn_in_progress = False
                break
            else:
                # Prompt next player
                next_player = interaction.guild.get_member(match.next_picker)
                next_player_name = next_player.display_name if next_player else "Next Player"
                await channel.send(f"<@{match.next_picker}>, it's your turn! **{next_player_name}**, use `/choose` to pick your next god.")


    async def show_teams(self, channel, match):
        """Show the final teams."""
        try:
            embed = discord.Embed(
                title="⚔️ Battle Ready!",
                description="Both armies are assembled. The epic battle begins now!",
                color=discord.Color.gold()
            )

            # Team 1
            p1_gods = []
            for god in match.teams[match.player1_id]:
                p1_gods.append(f"• **{god.name}** - HP: {god.hp}, DMG: {god.dmg}")
            
            embed.add_field(
                name=f"🔵 {match.player1_name}'s Army",
                value="\n".join(p1_gods),
                inline=True
            )

            # Team 2
            p2_gods = []
            for god in match.teams[match.player2_id]:
                p2_gods.append(f"• **{god.name}** - HP: {god.hp}, DMG: {god.dmg}")
            
            embed.add_field(
                name=f"🔴 {match.player2_name}'s Army",
                value="\n".join(p2_gods),
                inline=True
            )
            
            embed.add_field(
                name="🎯 Battle Rules",
                value="• Take turns using `/do_turn`\n• Each god has unique abilities\n• Eliminate all enemy gods to win!\n• Gods become visible when they attack",
                inline=False
            )

            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing teams: {e}")
            await channel.send("✅ Teams are ready! Use `/do_turn` to start the battle.")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(BuildTeam(bot))
