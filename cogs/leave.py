import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging
from bot.utils import update_lobby_status_embed
from database.manager import db_manager
from currency.money_manager import MoneyManager

logger = logging.getLogger(__name__)

class Leave(commands.Cog):
    """Cog for leaving Maggod Fight lobbies."""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leave", description="Leave the current Maggod lobby and reset the match.")
    async def leave_lobby(self, interaction: discord.Interaction):
        """Leave the current lobby."""
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
        await interaction.response.defer(ephemeral=False)
        
        channel_id = channel.id

        # Import here to avoid circular imports
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel_id)

        #db_manager.delete_game_save(channel.id, match)

        # Get the other player's info for notification
        other_player_id = None
        other_player_name = "the other player"

        from currency.money_manager import MoneyManager
        money = MoneyManager()
        if match.game_phase == "playing":
            team1_survivors = sum(1 for god in match.teams[match.player1_id] if god.alive)
            team2_survivors = sum(1 for god in match.teams[match.player2_id] if god.alive)
            p1_gain = (team1_survivors-team2_survivors)*1000
            if match.gamb_bet != 0:
                p1_gain -= match.gamb_bet
            p2_gain = (team2_survivors-team1_survivors)*1000
            P1_new_bal = money.update_balance(match.player1_id,p1_gain)
            P2_new_bal = money.update_balance(match.player2_id,p2_gain)  

        if match.player1_id and match.player2_id:
            other_player_id = match.player1_id if interaction.user.id == match.player2_id else match.player2_id
            other_player = interaction.guild.get_member(other_player_id)
            other_player_name = other_player.display_name if other_player else "the other player"

        # Create response embed
        embed = discord.Embed(
            title="⚠️ Player Left Match",
            description=f"**{interaction.user.display_name}** has left the match.",
            color=0xffa500
        )
        embed.add_field(
                name=f" {match.player1_name}",
                value = (f"**Gains:** {p1_gain:,.2f}".replace(",", " ") + f" {Config.coin}\n"f"**New Balance:** {P1_new_bal:,}".replace(",", " ")),
                inline=False
            )
        if not(match.solo_mode):
            embed.add_field(
                    name=f"{match.player2_name}",
                    value = (f"**Gains:** {p2_gain:,.2f}".replace(",", " ") + f" {Config.coin}\n"f"**New Balance:** {P2_new_bal:,}".replace(",", " ")),
                    inline=False
                )
        
        if other_player_id:
            embed.add_field(
                name="🔄 Match Reset",
                value=f"The lobby has been reset. {other_player_name} can start a new match.",
                inline=False
            )
            embed.add_field(
                name="🎯 Next Step",
                value="Use `/join` to start a new match in this lobby." \
                "",
                inline=False
            )
        else:
            embed.add_field(
                name="🔄 Lobby Reset",
                value="The lobby is now available for new players.",
                inline=False
            )
        
        # Send main response
        await interaction.followup.send(embed=embed)
        
        # Notify the other player if they exist
        if other_player_id and not(match.solo_mode):
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

        #await update_lobby_status_embed(self.bot)
        logger.info(f"Player {interaction.user.id} ({interaction.user.display_name}) left match in channel {channel_id}")
        match.turn_in_progress = False
        match.start_view
        #remove the match
        del matchmaking_dict[channel_id]
        
async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Leave(bot))
 