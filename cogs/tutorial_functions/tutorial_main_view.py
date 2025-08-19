import discord
from .god_embeds import GodTutorials

# ---------------- Embeds ----------------

# Embed 1: Introduction
embed1 = discord.Embed(
    title="🏟️ Welcome to the Maggod Fight Arena!",
    description=(
        "This is a **turn-based combat game** where you can battle against "
        "other players or bots to **win rewards** and prove your strength!"
    ),
    color=discord.Color.gold()
)

# Embed 2: Channels overview
embed2 = discord.Embed(
    title="📜 Channels Overview",
    color=discord.Color.blue()
)
embed2.add_field(
    name="📜 tutorial",
    value=(
        "The **main multipurpose text channel** for anything related to the game:\n"
        "• Chat with other players\n"
        "• Use `/tutorial`\n"
        "• Get updates and announcements\n"
        "• Report bugs and give feedback"
    ),
    inline=False
)
embed2.add_field(
    name="⚔️-maggod-lobby-1 / 2",
    value=(
        "Dedicated **battle arenas** where you fight players or bots.\n"
        "To join a match use `/join`.\n"
        "If you want to fight a bot, use `/join` again.\n\n"
        "Once you join, you’ll receive instructions on how to use other `/commands`."
    ),
    inline=False
)

# Embed 3: Placeholder for future content
embed3 = discord.Embed(
    title="📝 Coming Soon",
    description="This section will be expanded in future updates!",
    color=discord.Color.purple()
)

# ---------------- Exports ----------------
embeds: list[discord.Embed] = [embed1, embed2, embed3]


# ---------------- Helper ----------------
async def switch_view(
    interaction: discord.Interaction,
    new_view: discord.ui.View | None,
    embeds: discord.Embed | list[discord.Embed]
) -> discord.Message:
    if not isinstance(embeds, list):
        embeds = [embeds]

    if interaction.response.is_done():
        # Already responded, edit via followup
        msg = await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embeds=embeds,
            view=new_view
        )
    else:
        msg = await interaction.response.edit_message(
            embeds=embeds,
            view=new_view
        )
    return msg

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
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))


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
        self.god_tutorials = GodTutorials()
        self.message: discord.Message | None = None  # must always be a Message

        # Dynamically add god buttons (5 per row, 4 rows total)
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
                return await interaction.response.send_message("❌ This is not your tutorial!", ephemeral=True)

            god_func = getattr(self.god_tutorials, god_name, None)
            if god_func:
                embeds = god_func()
                new_view = GodsMenuView(self.user)

                # save actual message reference
                msg = await switch_view(interaction, new_view, embeds)
                new_view.message = msg
        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message and isinstance(self.message, discord.Message):
            try:
                await self.message.edit(embed=discord.Embed(title="✅ Tutorial ended"), view=None)
            except discord.NotFound:
                pass  # message deleted, safe to ignore

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, row=4, custom_id="exit_gods")
    async def exit_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))

    @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.grey, row=4, custom_id="return_menu")
    async def return_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user)
        msg = await switch_view(interaction, view, [embed1, embed2])
        view.message = msg
