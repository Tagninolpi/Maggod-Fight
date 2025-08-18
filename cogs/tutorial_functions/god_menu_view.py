import discord
from .create_god_tutorial_embeds import create_god_tutorial_embeds

# ---------------- God Functions ----------------
class GodTutorials:
    """All god tutorial functions, each returning its embed(s)."""
    def __init__(self, cog):
        self.cog = cog

    def poseidon(self):
        return create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True
        )

    def hephaestus(self):
        return create_god_tutorial_embeds(
            ["hephaestus", "poseidon", "athena", "apollo", "ares"], success=True
        )

    def aphrodite(self):
        return create_god_tutorial_embeds(
            ["aphrodite", "zeus", "hera", "athena", "apollo"], success=True
        )

    def ares(self):
        return create_god_tutorial_embeds(
            ["ares", "athena", "hephaestus", "aphrodite", "poseidon"], success=True
        )

    def hera(self):
        return create_god_tutorial_embeds(
            ["hera", "zeus", "athena", "aphrodite", "charon"], success=True
        )

    def zeus(self):
        return create_god_tutorial_embeds(
            ["zeus", "poseidon", "aphrodite", "ares", "athena"], success=True
        )

    def athena(self):
        return create_god_tutorial_embeds(
            ["athena", "ares", "hera", "hephaestus", "apollo"], success=True
        )

    def apollo(self):
        return create_god_tutorial_embeds(
            ["apollo", "artemis", "athena", "zeus", "hermes"], success=True
        )

    def artemis(self):
        return create_god_tutorial_embeds(
            ["artemis", "apollo", "athena", "aphrodite", "hermes"], success=True
        )

    def hermes(self):
        return create_god_tutorial_embeds(
            ["hermes", "apollo", "athena", "ares", "artemis"], success=True
        )

    def hades_ow(self):
        return create_god_tutorial_embeds(
            ["hades_ow", "thanatos", "cerberus", "charon", "persephone"], success=True
        )

    def thanatos(self):
        return create_god_tutorial_embeds(
            ["thanatos", "hades_ow", "cerberus", "tisiphone", "alecto"], success=True
        )

    def cerberus(self):
        return create_god_tutorial_embeds(
            ["cerberus", "charon", "thanatos", "hades_uw", "tisiphone"], success=True
        )

    def charon(self):
        return create_god_tutorial_embeds(
            ["charon", "cerberus", "persephone", "alecto", "hades_uw"], success=True
        )

    def persephone(self):
        return create_god_tutorial_embeds(
            ["persephone", "tisiphone", "alecto", "charon", "megaera"], success=True
        )

    def hades_uw(self):
        return create_god_tutorial_embeds(
            ["hades_uw", "tisiphone", "alecto", "megaera", "cerberus"], success=True
        )

    def tisiphone(self):
        return create_god_tutorial_embeds(
            ["tisiphone", "alecto", "megaera", "hades_uw", "persephone"], success=True
        )

    def alecto(self):
        return create_god_tutorial_embeds(
            ["alecto", "tisiphone", "megaera", "hades_uw", "cerberus"], success=True
        )

    def megaera(self):
        return create_god_tutorial_embeds(
            ["megaera", "hecate", "alecto", "tisiphone", "hades_uw"], success=True
        )

    def hecate(self):
        return create_god_tutorial_embeds(
            ["hecate", "megaera", "tisiphone", "alecto", "hades_uw"], success=True
        )

# ---------------- Gods Menu View ----------------
class GodsMenuView(discord.ui.View):
    GODS = [
        "poseidon", "hephaestus", "aphrodite", "ares", "hera",
        "zeus", "athena", "apollo", "artemis", "hermes",
        "hades_ow", "thanatos", "cerberus", "charon", "persephone",
        "hades_uw", "tisiphone", "alecto", "megaera", "hecate"
    ]

    def __init__(self, user: discord.User, cog, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.user = user
        self.cog = cog
        self.god_tutorials = GodTutorials(cog)

        for i, god_name in enumerate(self.GODS):
            self.add_item(discord.ui.Button(
                label=god_name.title(),
                style=discord.ButtonStyle.blurple,
                custom_id=f"god_{god_name}",
                row=i // 5
            ))

        self.add_item(discord.ui.Button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_gods"))
        self.add_item(discord.ui.Button(label="Return to Menu", style=discord.ButtonStyle.grey, custom_id="return_menu"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message"):
            await self.message.edit(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

    async def on_button_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("This is not your tutorial!", ephemeral=True)

        god_name = interaction.data["custom_id"].replace("god_", "")
        god_func = getattr(self.god_tutorials, god_name, None)
        if god_func:
            embeds = god_func()
            view = GodsMenuView(self.user, self.cog)
            await interaction.response.edit_message(embed=embeds[0], view=view)

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
