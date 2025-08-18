import discord
from discord import app_commands
from discord.ext import commands

from bot.config import Config  # make sure this contains LOBBY_CATEGORY_NAME and allowed_channel_id

GODS = [
    "poseidon", "hephaestus", "aphrodite", "ares", "hera", "zeus", "athena",
    "apollo", "artemis", "hermes", "hades_ow", "thanatos", "cerberus",
    "charon", "persephone", "hades_uw", "tisiphone", "alecto", "megaera", "hecate"
]

class TutorialCog(commands.Cog):
    """Self-contained tutorial system for Maggod Fight Arena."""

    def __init__(self, bot):
        self.bot = bot

    # ---------------- Slash Command ----------------
    @app_commands.command(name="tutorial", description="Learn how the Maggod Fight Arena works.")
    async def tutorial(self, interaction: discord.Interaction):
        channel = interaction.channel

        # ---------- Checks ----------
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

        # ---------- Passed checks, show main tutorial ----------
        embed = discord.Embed(
            title="📚 Tutorial",
            description="Welcome! Press 'Gods Tutorial' to learn about gods or 'Exit' to close.",
            color=discord.Color.green()
        )
        view = self.TutorialMainView(interaction.user, self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ---------------- God Embeds ----------------
    def create_god_tutorial_embeds(self, god_name: str) -> list[discord.Embed]:
        """Create tutorial embeds for a specific god."""
        embeds = []

        god_info = {
            "poseidon": {
                "description": "God of the sea. Controls water and storms.",
                "abilities": ["Tidal Wave", "Ocean's Wrath", "Summon Kraken"]
            },
            "zeus": {
                "description": "King of the gods. Controls thunder and lightning.",
                "abilities": ["Thunderbolt", "Divine Wrath", "Storm Call"]
            },
            # Add all other gods here...
        }

        info = god_info.get(god_name, {"description": "No info available", "abilities": []})

        embed_intro = discord.Embed(
            title=f"📖 {god_name.title()} Tutorial",
            description=info["description"],
            color=discord.Color.blue()
        )
        embed_abilities = discord.Embed(
            title=f"{god_name.title()}'s Abilities",
            description="\n".join(f"• {ability}" for ability in info["abilities"]) or "No abilities listed.",
            color=discord.Color.dark_blue()
        )
        embeds.append(embed_intro)
        embeds.append(embed_abilities)
        return embeds

    # ---------------- Views ----------------
    class TutorialMainView(discord.ui.View):
        """Main tutorial menu view."""
        def __init__(self, user: discord.User, cog, timeout: int = 120):
            super().__init__(timeout=timeout)
            self.user = user
            self.cog = cog

            # Main buttons
            self.add_item(discord.ui.Button(label="Gods Tutorial", style=discord.ButtonStyle.green, custom_id="god_tutorial"))
            self.add_item(discord.ui.Button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_tutorial"))

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.user.id

        async def on_timeout(self) -> None:
            for child in self.children:
                child.disabled = True
            if hasattr(self, "message"):
                await self.message.edit(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

        @discord.ui.button(label="Gods Tutorial", style=discord.ButtonStyle.green, custom_id="god_tutorial")
        async def god_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.defer()
            view = self.cog.GodsMenuView(self.user, self.cog)
            await interaction.message.edit(embed=discord.Embed(title="📜 Select a God to learn more"), view=view)

        @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_tutorial")
        async def exit_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

    class GodsMenuView(discord.ui.View):
        """God selection menu."""
        def __init__(self, user: discord.User, cog, timeout: int = 120):
            super().__init__(timeout=timeout)
            self.user = user
            self.cog = cog

            # Add a button for each god
            for god_name in GODS:
                self.add_item(cog.GodButton(god_name, user, cog))

            # Exit & Return buttons
            self.add_item(discord.ui.Button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_gods"))
            self.add_item(discord.ui.Button(label="Return to Menu", style=discord.ButtonStyle.grey, custom_id="return_menu"))

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.user.id

        async def on_timeout(self) -> None:
            for child in self.children:
                child.disabled = True
            if hasattr(self, "message"):
                await self.message.edit(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

        @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_gods")
        async def exit_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

        @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.grey, custom_id="return_menu")
        async def return_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(
                title="📚 Tutorial",
                description="Welcome! Press 'Gods Tutorial' to learn about gods or 'Exit' to close.",
                color=discord.Color.green()
            )
            view = self.cog.TutorialMainView(self.user, self.cog)
            await interaction.response.edit_message(embed=embed, view=view)

    class GodButton(discord.ui.Button):
        """Button for a specific god."""
        def __init__(self, god_name: str, user: discord.User, cog):
            super().__init__(label=god_name.title(), style=discord.ButtonStyle.blurple)
            self.god_name = god_name
            self.user = user
            self.cog = cog

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("This is not your tutorial!", ephemeral=True)

            embeds = self.cog.create_god_tutorial_embeds(self.god_name)
            view = self.cog.GodsMenuView(self.user, self.cog)
            await interaction.response.edit_message(embeds=embeds, view=view)


async def setup(bot):
    await bot.add_cog(TutorialCog(bot))
