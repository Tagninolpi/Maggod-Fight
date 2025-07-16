import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging


logger = logging.getLogger(__name__)

class Leave(commands.Cog):
    """Cog for leaving Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leave", description="Leave the current Maggod Fight lobby and reset the match.")
    async def leave_lobby(self, interaction: discord.Interaction):
        """Leave the current lobby."""
        channel = interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return
            
        channel_id = channel.id

        # Import here to avoid circular imports
        from main import matchmaking_dict

        match = matchmaking_dict.get(channel_id)
        if not match:
            await interaction.response.send_message(
                "❌ You're not currently in a match.",
                ephemeral=True
            )
            return

        # Check if the user is one of the players
        if interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.response.send_message(
                "❌ You're not a participant in the current match.",
                ephemeral=True
            )
            return

        # Get the other player's info for notification
        other_player_id = None
        other_player_name = "the other player"
        
        if match.player1_id and match.player2_id:
            other_player_id = match.player1_id if interaction.user.id == match.player2_id else match.player2_id
            other_player = interaction.guild.get_member(other_player_id)
            other_player_name = other_player.display_name if other_player else "the other player"

        # Remove the match
        del matchmaking_dict[channel_id]
        logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) left match in channel {channel_id}")
 #change
        # Reset the channel name to default if it's a Maggod Fight Lobby
        if channel.category and channel.category.name == Config.LOBBY_CATEGORY_NAME:
            suffix = channel.name[-2:] if channel.name[-2:].isdigit() else "XX"
            new_name = f"🔘・maggod-fight-lobby-{suffix}"
            try:
                await channel.edit(name=new_name)
            except discord.Forbidden:
                logger.warning(f"Cannot rename channel {channel.name}")

        # Create response embed
        embed = discord.Embed(
            title="⚠️ Player Left Match",
            description=f"**{interaction.user.display_name}** has left the match.",
            color=0xffa500
        )
        
        if other_player_id:
            embed.add_field(
                name="🔄 Match Reset",
                value=f"The lobby has been reset. {other_player_name} can start a new match.",
                inline=False
            )
            embed.add_field(
                name="🎯 Next Step",
                value="Use `/join` to start a new match in this lobby.",
                inline=False
            )
        else:
            embed.add_field(
                name="🔄 Lobby Reset",
                value="The lobby is now available for new players.",
                inline=False
            )
        
        # Send main response
        await interaction.response.send_message(embed=embed)
        
        # Notify the other player if they exist
        if other_player_id:
            try:
                notification_embed = discord.Embed(
                    title="👋 Opponent Left",
                    description=f"Your opponent has left the match. You can start a new battle anytime!",
                    color=0x00bfff
                )
                notification_embed.add_field(
                    name="🎮 Ready to Play Again?",
                    value="Use `/join` to start matchmaking for a new opponent.",
                    inline=False
                )
                
                await interaction.followup.send(
                    f"<@{other_player_id}>",
                    embed=notification_embed
                )
            except Exception as e:
                logger.error(f"Error notifying other player: {e}")

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Leave(bot))
