import logging
import os
from datetime import datetime
from bot.config import Config

def setup_logging():
    """Set up logging configuration for the bot."""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    log_filename = f"{log_dir}/{datetime.now().strftime('%Y-%m-%d')}-{Config.LOG_FILE}"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Set discord.py logging level to WARNING to reduce noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    
    # Log setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {Config.LOG_LEVEL}")
    logger.info(f"Log file: {log_filename}")

def format_uptime(uptime_seconds):
    """Format uptime seconds into a readable string."""
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{int(days)}d")
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if seconds > 0 or not parts:
        parts.append(f"{int(seconds)}s")
    
    return " ".join(parts)

def create_error_embed(title, description, color=0xff0000):
    """Create a standardized error embed."""
    import discord
    
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    return embed

def create_success_embed(title, description, color=0x00ff00):
    """Create a standardized success embed."""
    import discord
    
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    return embed

def create_info_embed(title, description, color=0x00ffff):
    """Create a standardized info embed."""
    import discord
    
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    return embed

def truncate_text(text, max_length=2000):
    """Truncate text to fit within Discord's message limits."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def format_god_status(god):
    """Format a god's status for display."""
    status_icon = "💀" if not god.alive else "👁️" if god.visible else "👻"
    
    # Format effects
    effects = []
    for effect_name, effect_list in god.effects.items():
        for effect in effect_list:
            effects.append(f"{effect_name}({effect.value},{effect.duration})")
    
    effects_str = ", ".join(effects[:2]) if effects else "None"
    if len(effects) > 2:
        effects_str += f" +{len(effects) - 2} more"
    
    return f"{status_icon} **{god.name}** - HP: {god.hp}/{god.max_hp} | DMG: {god.dmg} | Effects: {effects_str}"

class BotStats:
    """Simple bot statistics tracker."""
    
    def __init__(self):
        self.commands_used = 0
        self.messages_seen = 0
        self.matches_started = 0
        self.matches_completed = 0
        self.start_time = datetime.utcnow()
    
    def increment_command_usage(self):
        """Increment command usage counter."""
        self.commands_used += 1
    
    def increment_message_count(self):
        """Increment message count."""
        self.messages_seen += 1
    
    def increment_match_started(self):
        """Increment match started counter."""
        self.matches_started += 1
    
    def increment_match_completed(self):
        """Increment match completed counter."""
        self.matches_completed += 1
    
    def get_uptime(self):
        """Get bot uptime."""
        return datetime.utcnow() - self.start_time
    
    def get_stats_dict(self):
        """Get stats as dictionary."""
        uptime = self.get_uptime()
        return {
            'commands_used': self.commands_used,
            'messages_seen': self.messages_seen,
            'matches_started': self.matches_started,
            'matches_completed': self.matches_completed,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': format_uptime(uptime.total_seconds())
        }
