import discord
from .god_embeds import GodTutorials

# ---------------- Helper ----------------
async def switch_view(interaction: discord.Interaction, new_view: discord.ui.View, embed: discord.Embed):
    """Helper to swap view and embed."""
    await interaction.response.edit_message(embed=embed, view=new_view)


# ---------------- Main Tutorial View ----------------
class TutorialMainView(discord.ui.View):
    """Main tutorial menu view."""
    def __init__(self, user: discord.User, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.user = user
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(embed=discord.Embed(title="✅ Tutorial ended"), view=None)

    @discord.ui.button(label="Gods Tutorial", style=discord.ButtonStyle.green, custom_id="god_tutorial")
    async def god_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📜 Select a God to learn more")
        view = GodsMenuView(self.user)
        await switch_view(interaction, view, embed)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_tutorial")
    async def exit_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(title="✅ Tutorial ended"), view=None)


# ---------------- Gods Menu View ----------------
class GodsMenuView(discord.ui.View):
    GODS = [
        "poseidon", "hephaestus", "aphrodite", "ares", "hera",
        "zeus", "athena", "apollo", "artemis", "hermes",
        "hades_ow", "thanatos", "cerberus", "charon", "persephone",
        "hades_uw", "tisiphone", "alecto", "megaera", "hecate"
    ]

    def __init__(self, user: discord.User, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.user = user
        self.god_tutorials = GodTutorials()  # no cog needed
        self.message: discord.Message | None = None

        # Dynamically add god buttons
        for i, god_name in enumerate(self.GODS):
            button = discord.ui.Button(
                label=god_name.title(),
                style=discord.ButtonStyle.blurple,
                custom_id=f"god_{god_name}",
                row=i // 5
            )
            button.callback = self.make_god_callback(god_name)
            self.add_item(button)

    def make_god_callback(self, god_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("This is not your tutorial!", ephemeral=True)

            god_func = getattr(self.god_tutorials, god_name, None)
            if god_func:
                embeds = god_func()
                # Keep the GodsMenuView for navigation after showing a god embed
                new_view = GodsMenuView(self.user)
                await interaction.response.edit_message(embed=embeds[0], view=new_view)
        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
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
        view = TutorialMainView(self.user)
        await switch_view(interaction, view, embed)
