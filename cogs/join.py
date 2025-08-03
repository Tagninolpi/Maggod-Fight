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
        await interaction.response.defer(ephemeral=False)
        channel = interaction.channel
        from bot.utils import update_lobby_status_embed
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send(
            "❌ This command must be used in a Mggod fight lobby channel.",
                ephemeral=True
            )
            return
            
        channel_id = channel.id

        # Validate location
        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.followup.send(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        # Import here to avoid circular imports
        from main import  Match
        from bot.utils import matchmaking_dict

        #start
        match = matchmaking_dict.get(channel_id)
        if not match:
            # First player joins
            matchmaking_dict[channel_id] = Match(player1_id=interaction.user.id)
            match = matchmaking_dict[channel_id]
            match.player1_name = interaction.user.display_name
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
                value=f"""Another player can do `/join` to join this lobby or **{interaction.user.display_name}** can do `/join` to play against the bot.""",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)

        elif match and not match.player2_id:
            if interaction.user.id == match.player1_id:
                # Same user joins again to play both sides
                match.player2_id = "bot"
                match.player2_name = "bot"
                match.started = True
                match.game_phase = "ready"
                match.solo_mode = True

                logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) joined as both players in channel {channel_id}")
                asyncio.create_task(update_lobby_status_embed(self.bot))

                embed = discord.Embed(
                    title="🤖 Solo Match Ready!",
                    description="You do the /commands for the bot. But it decides on it's own.",
                    color=0x9932CC
                )
                embed.add_field(
                    name="⚔️ Warriors",
                    value=f"**{interaction.user.display_name}** and Maggod bot",
                    inline=False
                )
                embed.add_field(
                    name="🎯 Next Step",
                    value="Use `/start` to begin team building.",
                    inline=False
                )

                await interaction.followup.send(embed=embed)
                return

            # Second player joins
            match.player2_id = interaction.user.id
            match.started = True
            match.game_phase = "ready"
            match = matchmaking_dict[channel_id]
            match.player2_name = interaction.user.display_name
            logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) joined as Player 2 in channel {channel_id}")
            asyncio.create_task(update_lobby_status_embed(self.bot))
            
            embed = discord.Embed(
                title="🔴 Match Ready!",
                description="Both players have joined. The battle can begin!",
                color=0xff0000
            )
            embed.add_field(
                name="⚔️ Warriors",
                value=f"**Player 1:** {match.player1_name}\n**Player 2:** {match.player2_name}",
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
            
            await interaction.followup.send(embed=embed)

        elif match.started:
            
            embed = discord.Embed(
                title="👥 Match in Progress",
                description="This lobby is currently occupied, but you can spectate!",
                color=0xffa500
            )
            embed.add_field(
                name="🥊 Current Match",
                value=f"**{match.player1_name}** vs **{match.player2_name}**",
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
            
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Join(bot))
