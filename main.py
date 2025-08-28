import asyncio
import logging
import os
import discord
from discord.ext import commands
from datetime import datetime
from datetime import timezone

# Import bot components
from bot.config import Config
from bot.utils import setup_logging, BotStats
from bot.events import setup_events
from bot.commands import setup_commands

# Import keep alive
from keep_alive import keep_alive

from currency.money_manager import MoneyManager

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
 
class Match:
    """Represents a single Maggod Fight match."""
    def __init__(self, player1_id=None, player2_id=None):
        self.player1_id = player1_id #str
        self.player1_name = "Player 1" #str
        self.player2_id = player2_id #str
        self.player2_name = "Player 2" #str
        self.started = False #bool
        self.teams = {} #List in dict {Player_id : [Gods]}
        self.gods = {} # copy of all the gods (no modification of the initial dict)
        self.available_gods = [] # list of all the remaining gods (used during team building)
        self.picked_gods = {}
        self.next_picker = None # str (player id or "bot")
        self.current_turn_player = None 
        self.turn_number = 0
        self.teams_initialized = False
        self.game_phase = "Waiting for first player"  # Waiting for second player,ready, building, playing, finished

        self.current_attacking_team = None
        self.turn_state = {
            "current_player": None,
            "turn_number": 1
        }
        self.solo_mode = False
        self.turn_in_progress = False
        self.start_view = False
        self.DEBUG_SKIP_BUILD = False
        self.ai_bot_name = "random"
        self.money_sys_type = "2 players"
        self.bot_type = "random"

class MaggodFightBot(commands.Bot):
    """Main bot class for Maggod Fight."""
    
    def __init__(self):
        # Configure intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix=Config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Bot statistics
        self.stats = BotStats()
        self.start_time = datetime.now(timezone.utc)
        
    async def setup_hook(self):
        """Setup hook called when bot is starting."""
        logger.info("Bot is starting up...")
    
        # Load all cogs
        cogs_to_load = [
            'cogs.lobby_manager',
            'cogs.join',
            'cogs.leave',
            'cogs.build_team',
            'cogs.turn',
            'cogs.tutorial',
            'cogs.balance',
            'cogs.gambling'
        ]
    
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")

        # Setup events and commands
        setup_events(self)
        #await setup_commands(self)
        logger.info("Commands loaded successfully")
 
    async def on_ready(self):
        """Called when the bot is ready."""
        self.start_time = datetime.utcnow()
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Game(name="Maggod Fight | /help")
        await self.change_presence(activity=activity)
        # Announce bot online
        try:
            channel = self.get_channel(Config.ANNOUNCE_CHANNEL_ID)
            if channel:
                await channel.send(f"<@{Config.OWNER_ID}>✅ **Maggod Fight Bot is now online!**")
            else:
                logger.error(f"Invalid ANNOUNCE_CHANNEL_ID: {Config.ANNOUNCE_CHANNEL_ID} "
                            f"(not a TextChannel)")
        except Exception as e:
            logger.error(f"Failed to send online message: {e}")


        # Sync commands globally first (this fixes the unknown integration error)
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} global commands")
            all_commands = [cmd.name for cmd in self.tree.get_commands()]
            logger.info(f"Available slash commands: {all_commands}")
        except Exception as e:
            logger.error(f"Failed to sync global commands: {e}")
        
        # Also sync for each guild for faster propagation
        for guild in self.guilds:
            try:
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands for guild {guild.name}")
            except Exception as e:
                logger.error(f"Failed to sync commands for guild {guild.name}: {e}")

async def main():
    """Main function to run the bot."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Start keep alive server
    keep_alive()
    
    # Create and run bot
    bot = MaggodFightBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
