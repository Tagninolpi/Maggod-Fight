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


class GodSelectionView(discord.ui.View):
    """View for selecting gods during team building."""

    def __init__(self, all_gods: list, available_gods: list, allowed_user: discord.Member,
                 picked_gods: dict, player1_id: int, player2_id: int):
        super().__init__(timeout=60)
        self.allowed_user = allowed_user
        self.selected_god = None
        self.picked_gods = picked_gods
        self.player1_id = player1_id
        self.player2_id = player2_id

        # Create buttons for each god (up to 25 buttons max)
        gods_to_show = all_gods[:25]  # Discord has a 25 component limit
        for i, god in enumerate(gods_to_show):
            row = i // 5  # 5 buttons per row
            self.add_item(self.make_button(god, available_gods, row))

    def make_button(self, god, available_gods, row: int):
        """Create a button for a god."""

        # Make sure name is exactly 11 characters wide
        label = god.name.ljust(11)  

        # Default style
        style = discord.ButtonStyle.primary

        # Check if god was already picked
        if god.name in self.picked_gods:
            picker_id = self.picked_gods[god.name]
            if picker_id == self.player1_id:
                style = discord.ButtonStyle.success  # Green
            elif picker_id == self.player2_id:
                style = discord.ButtonStyle.primary  # Blue
            disabled = True
        else:
            # Disable if not in available_gods
            disabled = god not in available_gods

        button = discord.ui.Button(
            label=label,
            style=style,
            row=row,
            disabled=disabled
        )

        async def callback(interaction: discord.Interaction):
            if interaction.user != self.allowed_user:
                await interaction.response.send_message(
                    "⚠️ You're not allowed to pick right now.",
                    ephemeral=True
                )
                return

            self.picked_gods[god.name] = interaction.user.id

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
        DEBUG_SKIP_BUILD = False
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
        if not match or interaction.user.id not in [match.player1_id, match.player2_id]:
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
        match.turn_in_progress = True
        
        if match.solo_mode and match.next_picker == "bot":
            # Bot turn in solo mode: pick randomly from available gods
            chosen = random.choice(match.available_gods)
        else:
            if interaction.user.id != match.next_picker:
                await interaction.followup.send(
                    "⏳ Please wait for your turn.",
                    ephemeral=False
                )
                return
            # Show god selection UI
            view = GodSelectionView(
                all_gods=match.gods,
                available_gods=match.available_gods,
                allowed_user=interaction.user,
                picked_gods=match.picked_gods,
                player1_id=match.player1_id,
                player2_id=match.player2_id
                )

        
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

                await channel.send("❌ Team building timed out. The lobby has been reset.",ephemeral = True)
                return

            # Process the selection
            chosen = view.selected_god
        if match.solo_mode and match.next_picker == "bot":  # assuming you have a flag indicating bot mode
            match.teams["bot"].append(chosen)
            match.picked_gods[chosen.name] = "bot"
        else:
            # Multiplayer mode - assign based on user id (or your previous logic)
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
            value=f"{len(match.teams[interaction.user.id])}/5 gods chosen" if match.solo_mode else f"{len(match.teams["bot"])}/5 gods chosen",
            inline=True
        )
        await channel.send(embed=embed)

        # Switch to the other player
        if match.solo_mode and match.next_picker == "bot":
            match.next_picker = (match.player1_id)
        else:
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
            await channel.send(f"<@{interaction.user.id}>, use `/do_turn` to take the first move.")
            match.turn_in_progress = False
        else:
            # Continue team building
            next_player = interaction.guild.get_member(match.next_picker)
            next_player_name = next_player.display_name if next_player else "Next Player"
            
            await channel.send(f"<@{match.next_picker}>, it's your turn! **{next_player_name}** use `/choose` to pick your next god.")
            match.turn_in_progress = False

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
