import discord
from .god_menu_view import create_god_tutorial_embeds

class TutorialMainView(discord.ui.View):
    """Main tutorial menu view."""
    def __init__(self, user: discord.User, cog, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.user = user
        self.cog = cog
        self.message: discord.Message | None = None  # Will be set when sending

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the user who started the tutorial to interact."""
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        """Disable buttons when the view times out."""
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(
                embed=discord.Embed(title="✅ Tutorial ended"),
                view=None
            )

    @discord.ui.button(
        label="Gods Tutorial",
        style=discord.ButtonStyle.green,
        custom_id="god_tutorial"
    )
    async def god_tutorial(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """Opens the Gods Tutorial submenu."""
        await interaction.response.defer()
        view = self.cog.GodsMenuView(self.user, self.cog)
        await interaction.message.edit(
            embed=discord.Embed(title="📜 Select a God to learn more"),
            view=view
        )

    @discord.ui.button(
        label="Exit",
        style=discord.ButtonStyle.red,
        custom_id="exit_tutorial"
    )
    async def exit_tutorial(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        """Exits the tutorial."""
        await interaction.response.edit_message(
            embed=discord.Embed(title="✅ Tutorial ended"),
            view=None
        )
