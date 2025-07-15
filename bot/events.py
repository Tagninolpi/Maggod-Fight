import discord
from discord.ext import commands
import logging
import traceback

logger = logging.getLogger(__name__)

def setup_events(bot):
    """Set up bot event handlers."""
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        """Handle general bot errors."""
        logger.error(f"An error occurred in event {event}")
        logger.error(traceback.format_exc())
    
    @bot.event
    async def on_command_error(ctx, error):
        """Handle command errors."""
        # Increment stats
        if hasattr(bot, 'stats'):
            bot.stats.increment_command_usage()
        
        if isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors
            return
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        
        else:
            # Log unexpected errors
            logger.error(f"Unexpected error in command {ctx.command}: {error}")
            logger.error(traceback.format_exc())
            await ctx.send("❌ An unexpected error occurred. Please try again later.")
    
    @bot.event
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle application command errors."""
        # Increment stats
        if hasattr(bot, 'stats'):
            bot.stats.increment_command_usage()
        
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"❌ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
                ephemeral=True
            )
        
        elif isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "❌ I don't have the required permissions to execute this command.",
                ephemeral=True
            )
        
        else:
            # Log unexpected errors
            logger.error(f"Unexpected error in app command: {error}")
            logger.error(traceback.format_exc())
            
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An unexpected error occurred. Please try again later.",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An unexpected error occurred. Please try again later.",
                    ephemeral=True
                )
    
    @bot.event
    async def on_guild_join(guild):
        """Handle bot joining a new guild."""
        logger.info(f"Bot joined guild: {guild.name} (ID: {guild.id})")
        
        # Sync commands for the new guild
        try:
            synced = await bot.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands for new guild {guild.name}")
        except Exception as e:
            logger.error(f"Failed to sync commands for new guild {guild.name}: {e}")
        
        # Try to send a welcome message to the system channel
        if guild.system_channel:
            try:
                embed = discord.Embed(
                    title="⚔️ Welcome to Maggod Fight!",
                    description="Thanks for adding me to your server! I'm ready to host epic battles between Greek gods.",
                    color=0x00ff00
                )
                embed.add_field(
                    name="🚀 Getting Started",
                    value="• Use `/create_maggod_lobbies` to create battle lobbies\n"
                          "• Use `/join` in a lobby to start matchmaking\n"
                          "• Use `/help` for all available commands",
                    inline=False
                )
                embed.add_field(
                    name="🎮 Game Features",
                    value="• Turn-based combat with 20 unique gods\n"
                          "• Strategic team building (5 gods per team)\n"
                          "• Complex ability and effect system\n"
                          "• Multiple concurrent matches\n"
                          "• Interactive Discord UI",
                    inline=False
                )
                embed.add_field(
                    name="🏛️ Available Gods",
                    value="Choose from Olympians, Underworld deities, Furies, and more!\n"
                          "Each god has unique abilities and strategic value.",
                    inline=False
                )
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Cannot send message to system channel in guild {guild.name}")
    
    @bot.event
    async def on_guild_remove(guild):
        """Handle bot being removed from a guild."""
        logger.info(f"Bot removed from guild: {guild.name} (ID: {guild.id})")
        
        # Clean up any matches in progress for this guild
        from main import matchmaking_dict
        
        channels_to_remove = []
        for channel_id, match in matchmaking_dict.items():
            try:
                channel = bot.get_channel(channel_id)
                if channel and channel.guild.id == guild.id:
                    channels_to_remove.append(channel_id)
            except Exception as e:
                logger.error(f"Error checking channel {channel_id}: {e}")
        
        for channel_id in channels_to_remove:
            del matchmaking_dict[channel_id]
            logger.info(f"Cleaned up match for channel {channel_id}")
    
    @bot.event
    async def on_message(message):
        """Handle messages."""
        if hasattr(bot, 'stats'):
            bot.stats.increment_message_count()
        
        # Process commands
        await bot.process_commands(message)
    
    @bot.event
    async def on_disconnect():
        """Handle bot disconnection."""
        logger.warning("Bot disconnected from Discord")
    
    @bot.event
    async def on_resumed():
        """Handle bot reconnection."""
        logger.info("Bot reconnected to Discord")
    
    logger.info("Event handlers loaded successfully")
