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
    
    # Game Settings
    LOBBY_CATEGORY_NAME = "Maggod Fight Lobbies"
    TEAM_SIZE = 5
    SELECTION_TIMEOUT = 300  # 5 minutes
    
    # God Selection Settings
    MAX_GODS_PER_BUTTON_VIEW = 25  # Discord limit
    BUTTONS_PER_ROW = 5
    
    # Turn Settings
    TURN_TIMEOUT = 300  # 5 minutes per turn
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is required! Please set it in your environment variables.")
        
        if len(cls.DISCORD_TOKEN) < 50:
            raise ValueError("DISCORD_TOKEN appears to be invalid (too short).")
        
        return True
