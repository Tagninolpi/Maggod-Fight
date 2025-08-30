import os


class Config:
    """Configuration class for the Discord bot."""
    
    # Discord Bot Token (required)
    DISCORD_TOKEN = os.getenv("TOKEN")
    # Bot Configuration
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    # Replit Configuration
    REPLIT_URL = os.getenv("REPL_URL", "")
    # Bot Settings
    MAX_MESSAGE_LENGTH = 2000
    EMBED_COLOR = 0x00ff00  # Green
    ERROR_COLOR = 0xff0000  # Red
    # God Selection Settings
    MAX_GODS_PER_BUTTON_VIEW = 25  # Discord limit
    BUTTONS_PER_ROW = 5
    # Turn Settings
    TURN_TIMEOUT = 300  # 5 minutes per turn
    TEAM_SIZE = 5
    SELECTION_TIMEOUT = 300  # 5 minutes

    # Game Settings
    LOBBY_CATEGORY_NAME = "Maggod Gaming"
    LOBBY_CATEGORY_ID = 1407088161364115682
                            # me
    ALLOWED_PLAYER_IDS = [1360749637299998870,1126876428915449958,1314290931314200690] # allowed to use /create /delete (lobby)
    allowed_channel_id = 1407094327573872723# channel to use /create /delete (lobby)
    ANNOUNCE_CHANNEL_ID = 1407094852709253302 # channel to annouce that the bot is online
    OWNER_ID = 1360749637299998870 # id of player that is pinged when bot is online

    coin = "<:maggot_coin:1281718478054887476>"

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required! Please set it in your environment variables.")
        
        if len(cls.DISCORD_TOKEN) < 50:
            raise ValueError("DISCORD_TOKEN appears to be invalid (too short).")
        
        return True
