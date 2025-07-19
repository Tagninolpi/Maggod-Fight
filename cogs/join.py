import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging
import asyncio
logger = logging.getLogger(__name__)

class Join(commands.Cog):
    """Cog for joining Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Join a Maggod Fight Lobby")
    async def join_lobby(self, interaction: discord.Interaction):
        """Join a Maggod Fight lobby."""
        channel = interaction.channel
        from bot.utils import update_lobby_status_embed
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return
            
        channel_id = channel.id

        # Validate location
        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        # Import here to avoid circular imports
        from main import  Match
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel_id)

        if not match:
            # First player joins
            matchmaking_dict[channel_id] = Match(player1_id=interaction.user.id)
            match = matchmaking_dict[channel_id]
            logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) joined in channel {channel_id}")

            # Update bot stats
            if hasattr(self.bot, 'stats'):
                self.bot.stats.increment_match_started()
            match.game_phase = "Waiting for second player"
            asyncio.create_task(update_lobby_status_embed(self.bot))

            
            
            embed = discord.Embed(
                title="🟢 Player 1 Joined!",
                description=f"**{interaction.user.display_name}** has joined the lobby.",
                color=0x00ff00
            )
            embed.add_field(
                name="⏳ Waiting...",
                value="Looking for a second player to join the battle!",
                inline=False
            )
            embed.add_field(
                name="🎯 Next Step",
                value="Another player needs to use `/join` to start the match.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)

        elif match and not match.player2_id:
            if interaction.user.id == match.player1_id:
                await interaction.response.send_message(
                    "⚠️ You already joined this lobby. Waiting for another player!",
                    ephemeral=True
                )
                return

            # Second player joins
            match.player2_id = interaction.user.id
            match.started = True
            match.game_phase = "ready"
            match = matchmaking_dict[channel_id]
            logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) joined as Player 2 in channel {channel_id}")
            asyncio.create_task(update_lobby_status_embed(self.bot))

            # Get player names
            player1 = interaction.guild.get_member(match.player1_id)
            player1_name = player1.display_name if player1 else "Player 1"
            
            embed = discord.Embed(
                title="🔴 Match Ready!",
                description="Both players have joined. The battle can begin!",
                color=0xff0000
            )
            embed.add_field(
                name="⚔️ Warriors",
                value=f"**Player 1:** {player1_name}\n**Player 2:** {interaction.user.display_name}",
                inline=False
            )
            embed.add_field(
                name="🎯 Next Step",
                value="Use `/start` to begin building your teams!\nEach player will choose 5 gods for their army.",
                inline=False
            )
            embed.add_field(
                name="🏛️ Gods Available",
                value="20 unique Greek gods await your command, each with special abilities!",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)

        elif match.started:
            # Get player names for spectator message
            player1 = interaction.guild.get_member(match.player1_id) if match.player1_id else None
            player2 = interaction.guild.get_member(match.player2_id) if match.player2_id else None
            
            player1_name = player1.display_name if player1 else "Player 1"
            player2_name = player2.display_name if player2 else "Player 2"
            
            embed = discord.Embed(
                title="👥 Match in Progress",
                description="This lobby is currently occupied, but you can spectate!",
                color=0xffa500
            )
            embed.add_field(
                name="🥊 Current Match",
                value=f"**{player1_name}** vs **{player2_name}**",
                inline=False
            )
            embed.add_field(
                name="📊 Match Status",
                value=f"Phase: {match.game_phase.title()}",
                inline=False
            )
            embed.add_field(
                name="🔍 Spectating",
                value="You can watch the battle unfold, but cannot participate.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Join(bot))
