import discord
from discord.ext import commands
from discord import app_commands
import random
import copy
import logging
import asyncio
from utils.game_test_on_discord import gods as all_gods_template
from bot.utils import update_lobby_status_embed
import asyncio

logger = logging.getLogger(__name__)

class GodSelectionView(discord.ui.View):
    """View for selecting gods during team building."""
    
    def __init__(self, gods: list, allowed_user: discord.Member):
        super().__init__(timeout=300)
        self.allowed_user = allowed_user
        self.selected_god = None

        # Create buttons for each god (up to 25 buttons max)
        gods_to_show = gods[:25]  # Discord has a 25 component limit
        for i, god in enumerate(gods_to_show):
            row = i // 5  # 5 buttons per row
            self.add_item(self.make_button(god, row))

    def make_button(self, god, row: int):
        """Create a button for a god."""
        # Create label with god info
        label = f"{god.name} ({god.hp}HP/{god.dmg}DMG)"
        if len(label) > 80:  # Discord button label limit
            label = f"{god.name} ({god.hp}/{god.dmg})"
        
        button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.primary,
            row=row
        )

        async def callback(interaction: discord.Interaction):
            if interaction.user != self.allowed_user:
                await interaction.response.send_message(
                    "⚠️ You're not allowed to pick right now.",
                    ephemeral=True
                )
                return

            self.selected_god = god
            self.stop()
            await interaction.response.send_message(
                f"✅ You selected **{god.name}**! (HP: {god.hp}, DMG: {god.dmg})",
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
        DEBUG_SKIP_BUILD = True  # ⬅️ Set to False for normal use
        await interaction.response.defer(ephemeral=False)
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        channel_id = channel.id

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict
        from utils.game_test_on_discord import gods as all_gods_template

        match = matchmaking_dict.get(channel_id)

        if not match or not match.started:
            await interaction.followup.send(
                "❌ No ongoing match in this channel. Use `/join` to start a match.",
                ephemeral=True
            )
            return

        if match.game_phase != "ready":
            await interaction.followup.send(
                "🛑 Team building is complete! The battle has begun.\n"
                "The first player should use `/do_turn` to start.",
                ephemeral=True
            )
            return

        if hasattr(match, "teams_initialized") and match.teams_initialized:
            await interaction.followup.send(
                "✅ Team building already started.",
                ephemeral=True
            )
            return

        # Common setup for both modes
        match.gods = copy.deepcopy(all_gods_template)
        match.available_gods = list(match.gods.values())
        match.teams = {
            match.player1_id: [],
            match.player2_id: []
        }
        DEBUG_SKIP_BUILD = True
        # 🧪 Debug Skip Team Building
        if DEBUG_SKIP_BUILD:
            god_names_team1 = ["hephaestus", "aphrodite", "ares", "hera", "zeus"]
            god_names_team2 = ["athena", "poseidon", "apollo", "artemis", "hermes"]

            try:
                # Check match.gods contents before assignment
                for name in god_names_team1 + god_names_team2:
                    god_obj = match.gods.get(name)
                    if god_obj is None:
                        await interaction.followup.send(
                            f"❌ Debug skip failed. God not found: `{name}`", ephemeral=True
                        )
                        return
                    if isinstance(god_obj, list):
                        await interaction.followup.send(
                            f"❌ Debug skip failed. `match.gods[{name}]` is a list, expected a God instance", ephemeral=True
                        )
                        return

                # Assign teams
                match.teams[match.player1_id] = [match.gods[name] for name in god_names_team1]
                match.teams[match.player2_id] = [match.gods[name] for name in god_names_team2]

                # Check teams after assignment for nested lists
                for player_id in (match.player1_id, match.player2_id):
                    for god in match.teams[player_id]:
                        if isinstance(god, list):
                            await interaction.followup.send(
                                f"❌ Debug skip failed. Nested list found in `match.teams[{player_id}]`", ephemeral=True
                            )
                            return

                match.available_gods = [
                    god for name, god in match.gods.items()
                    if name not in god_names_team1 and name not in god_names_team2
                ]

            except KeyError as e:
                await interaction.followup.send(
                    f"❌ Debug skip failed. God not found: `{e}`", ephemeral=True
                )
                return

    # rest of your code here...


        
        # 🧑‍🤝‍🧑 Normal team building flow
        match.next_picker = random.choice([match.player1_id, match.player2_id])
        match.teams_initialized = True
        match.game_phase = "building"
        asyncio.create_task(update_lobby_status_embed(self.bot))

        logger.info(f"Team building started in channel {channel_id}")

        # Get player names
        player1 = interaction.guild.get_member(match.player1_id)
        player2 = interaction.guild.get_member(match.player2_id)
        first_picker = interaction.guild.get_member(match.next_picker)

        player1_name = player1.display_name if player1 else "Player 1"
        player2_name = player2.display_name if player2 else "Player 2"
        first_picker_name = first_picker.display_name if first_picker else "First Player"

        embed = discord.Embed(
            title="🎮 Team Building Phase",
            description="The draft begins! Each player will select 5 gods for their team.",
            color=0x00ff00
        )
        embed.add_field(
            name="⚔️ Players",
            value=f"**Player 1:** {player1_name}\n**Player 2:** {player2_name}",
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
        embed.add_field(
            name="🎲 First Pick",
            value=f"**{first_picker_name}** goes first!",
            inline=False
        )

        await interaction.followup.send(embed=embed)
        await interaction.followup.send(
            f"<@{match.next_picker}>, you're up! Use `/choose` to pick your first god."
        )
        match.turn_state = {
        "current_player": match.next_picker,
        "turn_number": 1
        }



    @app_commands.command(name="choose", description="Choose a god for your team.")
    async def choose(self, interaction: discord.Interaction):
        """Choose a god for the team."""
        channel = interaction.channel
        await interaction.response.defer(ephemeral=False)
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return
            
        channel_id = channel.id

        # Import here to avoid circular imports
        from main import matchmaking_dict

        match = matchmaking_dict.get(channel_id)
        
        if match.game_phase != "building":
            await interaction.followup.send(
                "🛑 Team building is complete! The battle has begun.\n"
                "The first player should use `/do_turn` to start.",
                ephemeral=True
            )
            return
        if not match or not hasattr(match, "teams"):
            await interaction.followup.send(
                "❌ Team building hasn't started yet. Use `/start` to begin.",
                ephemeral=True
            )
            return

        if interaction.user.id != match.next_picker:
            await interaction.followup.send(
                "⏳ Please wait for your turn.",
                ephemeral=True
            )
            return
            
        # Show god selection UI
        view = GodSelectionView(match.available_gods, interaction.user)
        
        # Create embed showing available gods
        embed = discord.Embed(
            title="🏛️ Choose Your God",
            description=f"Select a god for your team from the available options.",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📊 Current Status",
            value=f"**Available Gods:** {len(match.available_gods)}\n"
                  f"**Your Team:** {len(match.teams[interaction.user.id])}/5 gods",
            inline=False
        )
        
        # Show some god options in the embed
        god_preview = []
        for i, god in enumerate(match.available_gods[:10]):  # Show first 10
            god_preview.append(f"• **{god.name}** - HP: {god.hp}, DMG: {god.dmg}")

        await interaction.followup.send(
            f"<@{interaction.user.id}>, select your god:",
            embed=embed,
            view=view,
            ephemeral=True
        )

        # Wait for selection
        await view.wait()

        if view.selected_god is None:
            # Timeout occurred
            await interaction.followup.send(
                "⏱️ Selection timed out. Match has been reset.",
                ephemeral=True
            )
            match = matchmaking_dict[channel.id]
            match.game_phase = "Waiting for first player"
            asyncio.create_task(update_lobby_status_embed(self.bot))
            # Reset the match
            del matchmaking_dict[channel_id]
            logger.info(f"Match timed out in channel {channel_id}")

            await channel.send("❌ Team building timed out. The lobby has been reset.")
            return

        # Process the selection
        chosen = view.selected_god
        match.teams[interaction.user.id].append(chosen)
        match.available_gods.remove(chosen)
        
        logger.info(f"Player {interaction.user.id} chose {chosen.name} in channel {channel_id}")

        # Create selection announcement
        embed = discord.Embed(
            title="⚡ God Selected!",
            description=f"**{interaction.user.display_name}** has chosen their god.",
            color=0x00bfff
        )
        
        embed.add_field(
            name="🏛️ Selected God",
            value=f"**{chosen.name}**\n"
                  f"HP: {chosen.hp} | DMG: {chosen.dmg}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Team Progress",
            value=f"{len(match.teams[interaction.user.id])}/5 gods chosen",
            inline=True
        )
        await channel.send(embed=embed)

        # Switch to the other player
        match.next_picker = (
            match.player1_id if interaction.user.id == match.player2_id else match.player2_id
        )

        # Check if both teams are complete
        p1_team = match.teams[match.player1_id]
        p2_team = match.teams[match.player2_id]
        logger.debug(f"Post-pick: p1={len(p1_team)}, p2={len(p2_team)}")

        if len(p1_team) == 5 and len(p2_team) == 5:
            # Both teams complete
            match = matchmaking_dict[channel.id]
            match.game_phase = "playing"
            asyncio.create_task(update_lobby_status_embed(self.bot))
            
            # Initialize turn state
            match.turn_state = {
                "current_player": interaction.user.id,
                "turn_number": 1
            }
            
            logger.info(f"Both teams complete in channel {channel_id}")
            await channel.send("✅ **Both teams are complete! Let the battle begin!**")
            await self.show_teams(channel, match)
            # Prompt the player who just picked to start the game
            await channel.send(f"<@{interaction.user.id}>, use `/do_turn` to take the first move."
        )
        else:
            # Continue team building
            next_player = interaction.guild.get_member(match.next_picker)
            next_player_name = next_player.display_name if next_player else "Next Player"
            
            await channel.send(f"<@{match.next_picker}>, it's your turn! **{next_player_name}** use `/choose` to pick your next god.")

    async def show_teams(self, channel, match):
        """Show the final teams."""
        try:
            # Get player names
            player1 = channel.guild.get_member(match.player1_id)
            player2 = channel.guild.get_member(match.player2_id)
            first_turn_player = channel.guild.get_member(match.turn_state["current_player"])
            
            player1_name = player1.display_name if player1 else "Player 1"
            player2_name = player2.display_name if player2 else "Player 2"
            first_turn_name = first_turn_player.display_name if first_turn_player else "First Player"
            
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
                name=f"🔵 {player1_name}'s Army",
                value="\n".join(p1_gods),
                inline=True
            )

            # Team 2
            p2_gods = []
            for god in match.teams[match.player2_id]:
                p2_gods.append(f"• **{god.name}** - HP: {god.hp}, DMG: {god.dmg}")
            
            embed.add_field(
                name=f"🔴 {player2_name}'s Army",
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
