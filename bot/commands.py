import discord
from discord.ext import commands
from discord import app_commands
import time
import psutil
import platform
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def setup_commands(bot):
    """Set up bot commands."""
    
    @bot.tree.command(name="ping", description="Check bot latency and status")
    async def ping(interaction: discord.Interaction):
        """Ping command to check bot responsiveness."""
        start_time = time.time()
        
        # Create initial embed
        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x00ff00
        )
        
        # Send initial response
        await interaction.response.send_message(embed=embed)
        
        # Calculate response time
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        # Update embed with timing information
        embed.add_field(
            name="📡 Latency",
            value=f"`{round(bot.latency * 1000)}ms`",
            inline=True
        )
        embed.add_field(
            name="⚡ Response Time",
            value=f"`{round(response_time)}ms`",
            inline=True
        )
        embed.add_field(
            name="🟢 Status",
            value="`Online`",
            inline=True
        )
        
        # Add uptime if available
        if hasattr(bot, 'start_time') and bot.start_time:
            uptime = discord.utils.utcnow() - bot.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
            embed.add_field(
                name="⏱️ Uptime",
                value=f"`{uptime_str}`",
                inline=False
            )
        
        embed.timestamp = discord.utils.utcnow()
        
        # Edit the original response
        await interaction.edit_original_response(embed=embed)
    
    @bot.tree.command(name="status", description="Get detailed bot status information")
    async def status(interaction: discord.Interaction):
        """Status command with detailed bot information."""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Get match statistics
            from main import matchmaking_dict
            active_matches = len(matchmaking_dict)
            
            embed = discord.Embed(
                title="🤖 Bot Status",
                color=0x00ff00,
                timestamp=discord.utils.utcnow()
            )
            
            # Bot Information
            embed.add_field(
                name="📊 Bot Info",
                value=f"**Guilds:** {len(bot.guilds)}\n"
                      f"**Users:** {len(bot.users)}\n"
                      f"**Latency:** {round(bot.latency * 1000)}ms",
                inline=True
            )
            
            # Game Statistics
            embed.add_field(
                name="🎮 Game Stats",
                value=f"**Active Matches:** {active_matches}\n"
                      f"**Commands Used:** {bot.stats.commands_used}\n"
                      f"**Messages Seen:** {bot.stats.messages_seen}",
                inline=True
            )
            
            # System Information
            embed.add_field(
                name="💻 System",
                value=f"**Platform:** {platform.system()}\n"
                      f"**CPU Usage:** {cpu_percent}%\n"
                      f"**Memory:** {memory.percent}%",
                inline=True
            )
            
            # Discord.py version
            embed.add_field(
                name="🔧 Version",
                value=f"**Discord.py:** {discord.__version__}\n"
                      f"**Python:** {platform.python_version()}",
                inline=True
            )
            
            # Uptime
            if hasattr(bot, 'start_time') and bot.start_time:
                uptime = discord.utils.utcnow() - bot.start_time
                days = uptime.days
                hours, remainder = divmod(uptime.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed.add_field(
                    name="⏱️ Uptime",
                    value=f"{days}d {hours}h {minutes}m {seconds}s",
                    inline=False
                )
            
            # Active matches details
            if active_matches > 0:
                match_details = []
                for channel_id, match in list(matchmaking_dict.items())[:5]:  # Show first 5
                    try:
                        channel = bot.get_channel(channel_id)
                        if channel:
                            match_details.append(f"• {channel.guild.name} - {match.game_phase}")
                    except:
                        pass
                
                if match_details:
                    embed.add_field(
                        name="🔄 Recent Matches",
                        value="\n".join(match_details),
                        inline=False
                    )
            
            embed.set_footer(text=f"Bot ID: {bot.user.id}")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching status information.",
                ephemeral=True
            )
    
    @bot.tree.command(name="help", description="Get help information")
    async def help_command(interaction: discord.Interaction):
        """Help command showing available commands."""
        embed = discord.Embed(
            title="⚔️ Maggod Fight Bot Help",
            description="Welcome to the ultimate Greek mythology battle arena!\n\n"
                       "**Maggod Fight** is a turn-based strategy game where you build teams of 5 Greek gods "
                       "and battle against other players using unique abilities and strategic combat.",
            color=0x00ff00
        )
        
        # Setup Commands
        embed.add_field(
            name="🏗️ Setup Commands",
            value="`/create_maggod_lobbies` - Create battle lobbies for your server\n"
                  "`/delete_maggod_lobbies` - Remove all lobbies",
            inline=False
        )
        
        # Game Commands
        embed.add_field(
            name="🎮 Game Commands",
            value="`/join` - Join a lobby and start matchmaking\n"
                  "`/leave` - Leave current match\n"
                  "`/start` - Begin team building phase\n"
                  "`/choose` - Select gods for your team\n"
                  "`/do_turn` - Make your move in battle",
            inline=False
        )
        
        # Bot Commands
        embed.add_field(
            name="🤖 Bot Commands",
            value="`/ping` - Check bot latency\n"
                  "`/status` - Detailed bot information\n"
                  "`/help` - Show this help message",
            inline=False
        )
        
        # How to Play
        embed.add_field(
            name="🎯 How to Play",
            value="1. **Create Lobbies** - Use `/create_maggod_lobbies` to set up battle channels\n"
                  "2. **Join a Match** - Use `/join` in a lobby channel\n"
                  "3. **Build Your Team** - Use `/start` then `/choose` to pick 5 gods\n"
                  "4. **Battle** - Use `/do_turn` to attack and use abilities\n"
                  "5. **Win** - Eliminate all enemy gods to claim victory!",
            inline=False
        )
        
        # Game Info
        embed.add_field(
            name="🏛️ About the Gods",
            value="Choose from **20 unique Greek gods** including:\n"
                  "• **Olympians** - Zeus, Poseidon, Athena, Apollo, and more\n"
                  "• **Underworld** - Hades, Persephone, Charon, Thanatos\n"
                  "• **Furies** - Tisiphone, Alecto, Megaera\n"
                  "• **Magic** - Hecate\n\n"
                  "Each god has unique HP, damage, and special abilities!",
            inline=False
        )
        
        embed.set_footer(text="Use slash commands (/) to interact with the bot • Bot runs 24/7 on Replit")
        embed.timestamp = discord.utils.utcnow()
        
        await interaction.response.send_message(embed=embed)
    
    # Traditional prefix commands for backup
    @bot.command(name="ping")
    async def prefix_ping(ctx):
        """Prefix version of ping command."""
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")
    
    @bot.command(name="test")
    async def prefix_test(ctx):
        """Test command to verify bot is responding."""
        await ctx.send("✅ Bot is working! Use slash commands (/) for the full experience.")
    
    logger.info("Commands loaded successfully")
