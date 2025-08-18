import discord
from .god_menu_view import create_god_tutorial_embeds
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
