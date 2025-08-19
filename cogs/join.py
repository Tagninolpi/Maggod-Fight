import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging
import asyncio
logger = logging.getLogger(__name__)
join_in_progress = False
class Join(commands.Cog):
    """Cog for joining Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join", description="Join a Maggod Lobby")

    async def join_lobby(self, interaction: discord.Interaction):
        global join_in_progress
        """Join a Maggod lobby."""
        # At the start of your command
        if interaction.response.is_done():
            return
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
        
        if join_in_progress:
            await interaction.response.send_message(
                "❌ A turn is already in progress. Please choose a god.",
                ephemeral=True
            )
            return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=False)

        
        join_in_progress = True
        try:
            from bot.utils import update_lobby_status_embed
                
            channel_id = channel.id

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
                #asyncio.create_task(update_lobby_status_embed(self.bot))

                
                
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
                    value=f"""Another player can do `/join` to join this lobby or <@{interaction.user.id}> can do `/join` to play against the bot.""",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)

            elif match and not match.player2_id:
                if interaction.user.id == match.player1_id:
                    # Same user joins again to play both sides
                    match.player2_id = 123
                    match.player2_name = "bot"
                    match.started = True
                    match.game_phase = "ready"
                    match.solo_mode = True

                    logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) joined as both players in channel {channel_id}")
                    #asyncio.create_task(update_lobby_status_embed(self.bot))

                    embed = discord.Embed(
                        title="🤖 Solo Match Ready!",
                        description="You play against the Maggod bot",
                        color=0x9932CC
                    )
                    embed.add_field(
                        name="⚔️ Warriors",
                        value=f"**{interaction.user.display_name}** and Maggod bot",
                        inline=False
                    )
                    embed.add_field(
                        name="🎯 Next Step",
                        value=f"<@{interaction.user.id}> do `/start` to begin team building.",
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
                #asyncio.create_task(update_lobby_status_embed(self.bot))
                
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
                    value="Use `/start` to decide if you want random teams or you want to assemble your teams!\nEach player will choose 5 gods for their army.",
                    inline=False
                )
                embed.add_field(
                    name="🏛️ Gods Available",
                    value="20 unique Greek gods await your command, each with special abilities!",
                    inline=False
                )
                
                try:
                    await interaction.followup.send(embed=embed)
                except discord.HTTPException as e:
                    logger.warning(f"Failed to send followup: {e}")

            elif match.started:
                if interaction.user.id in [match.player1_id, match.player2_id]:
                    await interaction.followup.send("❌ You are already in this match!!!", ephemeral=True)

                else:
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
                    try:
                        await interaction.followup.send(embed=embed)
                    except discord.HTTPException as e:
                        logger.warning(f"Failed to send followup: {e}")
            logger.info("Current matchmaking_dict:")
            for cid, match in matchmaking_dict.items():
                logger.info(f"Channel {cid}: Player1={match.player1_name} ({match.player1_id}), "
                            f"Player2={match.player2_name} ({match.player2_id}), "
                            f"Phase={match.game_phase}")
        finally:
            await asyncio.sleep(2)
            join_in_progress = False


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Join(bot))
 
