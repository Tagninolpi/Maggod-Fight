import discord
from discord.ext import commands
from discord import app_commands
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

class Tutorial(commands.Cog):
    """Cog for the Maggod Fight tutorial system."""

    GODS = [
        "poseidon", "hephaestus", "aphrodite", "ares", "hera",
        "zeus", "athena", "apollo", "artemis", "hermes",
        "hades_ow", "thanatos", "cerberus", "charon", "persephone",
        "hades_uw", "tisiphone", "alecto", "megaera", "hecate"
    ]

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tutorial", description="Learn how the Maggod Fight Arena works.")
    async def tutorial(self, interaction: discord.Interaction):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.name != Config.LOBBY_CATEGORY_NAME:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        if interaction.channel.id != Config.allowed_channel_id:
            await interaction.response.send_message(
                "❌ You can't use this command here.",
                ephemeral=True
            )
            return

        # --- Embeds ---
        embed_intro = discord.Embed(
            title="🏟️ Welcome to the Maggod Fight Arena!",
            description=(
                "This is a **turn-based combat game** where you can battle against "
                "other players or bots to **win rewards** and prove your strength!"
            ),
            color=discord.Color.gold()
        )

        embed_channels = discord.Embed(
            title="📜 Channels Overview",
            color=discord.Color.blue()
        )
        embed_channels.add_field(
            name="📊 lobby-status",
            value="A text channel where you can **see active fights** and check if someone is looking for an opponent.",
            inline=False
        )
        embed_channels.add_field(
            name="💬 information",
            value=(
                "The **main multipurpose text channel** for anything related to the game:\n"
                "• Chat with other players\n"
                "• Use `/tutorial`\n"
                "• Get updates and announcements\n"
                "• Report bugs and give feedback"
            ),
            inline=False
        )
        embed_channels.add_field(
            name="🔘・maggod-fight-lobby-01 / 02",
            value=(
                "Dedicated **battle arenas** where you fight players or bots.\n"
                "To join a match use `/join`.\n"
                "If you want to fight a bot, use `/join` again.\n\n"
                "Once you join, you’ll receive instructions on how to use other `/commands`."
            ),
            inline=False
        )

        # --- Views ---
        class TutorialView(discord.ui.View):
            def __init__(self, user_id: int):
                super().__init__(timeout=120)
                self.user_id = user_id
                self.message = None

            async def interaction_check(self, interaction_inner: discord.Interaction) -> bool:
                return interaction_inner.user.id == self.user_id

            async def on_timeout(self):
                if self.message:
                    try:
                        await self.message.edit(content="✅ Tutorial closed.", embeds=[], view=None)
                    except discord.NotFound:
                        pass

            @discord.ui.button(label="I got it", style=discord.ButtonStyle.danger)
            async def got_it(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                await interaction_button.response.edit_message(content="✅ Tutorial closed.", embeds=[], view=None)
                self.stop()

            @discord.ui.button(label="Gods Tutorial", style=discord.ButtonStyle.success)
            async def gods_tutorial(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                await self.show_gods_menu(interaction_button)

            async def show_gods_menu(self, interaction_button: discord.Interaction):
                """Display the gods selection menu."""
                class GodsView(discord.ui.View):
                    def __init__(self, user_id: int, message_ref):
                        super().__init__(timeout=120)
                        self.user_id = user_id
                        self.message_ref = message_ref

                        # Add god buttons
                        for god_name in Tutorial.GODS:
                            self.add_item(discord.ui.Button(
                                label=god_name.title(),
                                style=discord.ButtonStyle.primary,
                                custom_id=f"god_{god_name}"
                            ))

                        # Exit button
                        self.add_item(discord.ui.Button(
                            label="Exit",
                            style=discord.ButtonStyle.danger,
                            custom_id="exit_gods"
                        ))

                    async def interaction_check(self, interaction_inner: discord.Interaction) -> bool:
                        return interaction_inner.user.id == self.user_id

                    async def on_timeout(self):
                        try:
                            await self.message_ref.edit(content="✅ Tutorial closed.", embeds=[], view=None)
                        except discord.NotFound:
                            pass

                view_gods = GodsView(interaction_button.user.id, interaction_button.message)

                async def button_callback(interaction_inner: discord.Interaction):
                    cid = interaction_inner.data["custom_id"]

                    if cid == "exit_gods":
                        await interaction_inner.response.edit_message(content="✅ Tutorial closed.", embeds=[], view=None)
                        return

                    # God button pressed
                    god_embed = discord.Embed(
                        title=f"📖 {cid.replace('god_', '').title()} Tutorial",
                        description="Tutorial content coming soon!",
                        color=discord.Color.blue()
                    )

                    class GodDetailView(discord.ui.View):
                        def __init__(self, user_id: int, message_ref):
                            super().__init__(timeout=120)
                            self.user_id = user_id
                            self.message_ref = message_ref
                            # Return to menu
                            self.add_item(discord.ui.Button(
                                label="Return to Menu",
                                style=discord.ButtonStyle.secondary,
                                custom_id="return_menu"
                            ))
                            # Exit
                            self.add_item(discord.ui.Button(
                                label="Exit",
                                style=discord.ButtonStyle.danger,
                                custom_id="exit_detail"
                            ))

                        async def interaction_check(self, interaction_inner2: discord.Interaction) -> bool:
                            return interaction_inner2.user.id == self.user_id

                        async def on_timeout(self):
                            try:
                                await self.message_ref.edit(content="✅ Tutorial closed.", embeds=[], view=None)
                            except discord.NotFound:
                                pass

                    detail_view = GodDetailView(interaction_inner.user.id, interaction_inner.message)

                    async def detail_callback(interaction_inner2: discord.Interaction):
                        cid2 = interaction_inner2.data["custom_id"]
                        if cid2 == "exit_detail":
                            await interaction_inner2.response.edit_message(content="✅ Tutorial closed.", embeds=[], view=None)
                        elif cid2 == "return_menu":
                            await self.show_gods_menu(interaction_inner2)

                    for item in detail_view.children:
                        item.callback = detail_callback

                    await interaction_inner.response.edit_message(embed=god_embed, view=detail_view)

                for item in view_gods.children:
                    item.callback = button_callback

                await interaction_button.response.edit_message(content="📜 Select a god to learn more:", embeds=[], view=view_gods)

        # Send initial tutorial embeds
        view = TutorialView(interaction.user.id)
        view.message = await interaction.response.send_message(
            embeds=[embed_intro, embed_channels],
            view=view,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Tutorial(bot))
