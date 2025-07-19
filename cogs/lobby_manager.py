import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging

allowed_channel_id = 1393219828080185374
logger = logging.getLogger(__name__)


class LobbyManager(commands.Cog):
    """Cog for managing Maggod Fight lobbies."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="create_maggod_lobbies",
        description="Create Maggod Fight Lobby text channels under a category."
    )
    @app_commands.describe(
        count="Number of lobbies to create (default: 10, max: 20)")
    async def create_lobbies(self,
                             interaction: discord.Interaction,
                             count: int = 10):
        """Create Maggod Fight lobbies."""
        await interaction.response.defer(ephemeral=False)

        # ✅ Restrict to specific channel
        if interaction.channel.id != allowed_channel_id:
            await interaction.followup.send(
                "❌ You can't use this command here.",
                ephemeral=True
            )
            return
        

        # Validate count
        if count < 1 or count > 20:
            await interaction.followup.send(
                "❌ Count must be between 1 and 20.", ephemeral=True)
            return

        guild = interaction.guild
        if not guild:
            await interaction.followup.send(
                "❌ This command must be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(
                "❌ I don't have permission to manage channels in this server.",
                ephemeral=True)
            return

        try:
            # Create or get the category
            category = discord.utils.get(guild.categories,
                                         name=Config.LOBBY_CATEGORY_NAME)
            if not category:
                category = await guild.create_category(
                    Config.LOBBY_CATEGORY_NAME,
                    overwrites={
                        guild.default_role:
                        discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True,
                        ),
                        guild.me:
                        discord.PermissionOverwrite(read_messages=True,
                                                    send_messages=True,
                                                    manage_messages=True,
                                                    embed_links=True,
                                                    manage_channels=True)
                    })
                logger.info(f"Created category: {Config.LOBBY_CATEGORY_NAME}")

            created = 0
            existing = 0

            for i in range(1, count + 1):
                channel_name = f"🔘・maggod-fight-lobby-{i:02d}"

                # Check if channel already exists
                if discord.utils.get(guild.channels, name=channel_name):
                    existing += 1
                    continue

                # Create the channel
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category,
                    topic=
                    f"Maggod Fight Lobby #{i:02d} - Use /join to start matchmaking! "
                    f"Epic battles between Greek gods await you here. "
                    f"Build your team of 5 gods and prove your strategic prowess!"
                )
                created += 1
                logger.info(f"Created lobby channel: {channel_name}")

            # Send response
            embed = discord.Embed(title="🏗️ Lobby Creation Complete",
                                  color=0x00ff00,
                                  timestamp=discord.utils.utcnow())

            if created > 0:
                embed.add_field(name="✅ Created",
                                value=f"{created} new lobby channels",
                                inline=True)

            if existing > 0:
                embed.add_field(name="⚠️ Already Existed",
                                value=f"{existing} lobby channels",
                                inline=True)

            embed.add_field(name="📍 Location",
                            value=f"Category: `{Config.LOBBY_CATEGORY_NAME}`",
                            inline=False)

            embed.add_field(
                name="🎮 Next Steps",
                value=
                "Players can now use `/join` in any lobby to start matchmaking!",
                inline=False)

            await interaction.followup.send(embed=embed)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create channels or categories.",
                ephemeral=True)
        except Exception as e:
            logger.error(f"Error creating lobbies: {e}")
            await interaction.followup.send(
                "❌ An error occurred while creating lobbies.", ephemeral=True)

    @app_commands.command(
        name="delete_maggod_lobbies",
        description=
        "Delete the Maggod Fight Lobbies category and all its channels.")
    async def delete_lobbies(self, interaction: discord.Interaction):
        """Delete all Maggod Fight lobbies."""
        await interaction.response.defer(ephemeral=False)

        # ✅ Restrict to specific channel
        if interaction.channel.id != allowed_channel_id:
            await interaction.followup.send(
                "❌ You can't use this command here.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        if not guild:
            await interaction.followup.send(
                "❌ This command must be used in a server.", ephemeral=True)
            return

        # Check permissions
        if not guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(
                "❌ I don't have permission to manage channels in this server.",
                ephemeral=True)
            return

        try:
            category = discord.utils.get(guild.categories,
                                         name=Config.LOBBY_CATEGORY_NAME)

            if not category:
                await interaction.followup.send(
                    f"❌ The `{Config.LOBBY_CATEGORY_NAME}` category doesn't exist.",
                    ephemeral=True)
                return

            # Clean up any active matches in these channels
            from bot.utils import matchmaking_dict

            channels_to_cleanup = []
            for channel in category.channels:
                if channel.id in matchmaking_dict:
                    channels_to_cleanup.append(channel.id)

            for channel_id in channels_to_cleanup:
                del matchmaking_dict[channel_id]
                logger.info(f"Cleaned up match data for channel {channel_id}")

            # Delete all channels in the category
            deleted_channels = 0
            for channel in category.channels:
                await channel.delete()
                deleted_channels += 1
                logger.info(f"Deleted channel: {channel.name}")

            # Delete the category
            await category.delete()
            logger.info(f"Deleted category: {Config.LOBBY_CATEGORY_NAME}")

            embed = discord.Embed(
                title="🗑️ Lobby Deletion Complete",
                description=
                f"Successfully deleted {deleted_channels} lobby channels and the category.",
                color=0xff6b6b,
                timestamp=discord.utils.utcnow())

            if channels_to_cleanup:
                embed.add_field(
                    name="🧹 Cleanup",
                    value=
                    f"Also cleaned up {len(channels_to_cleanup)} active matches",
                    inline=False)

            await interaction.followup.send(embed=embed)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to delete channels or categories.",
                ephemeral=True)
        except Exception as e:
            logger.error(f"Error deleting lobbies: {e}")
            await interaction.followup.send(
                "❌ An error occurred while deleting lobbies.", ephemeral=True)


async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(LobbyManager(bot))