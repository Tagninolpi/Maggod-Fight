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

import discord

# Embed 3: Action prompt
embed3 = discord.Embed(
    title="🎯 Player1: Choose a God to Attack",
    description="Select one of your gods to perform an action.",
    color=discord.Color.green()
)

# Example formatted enemy team (manually written)
enemy_team_example = (
"| Poseidon Hephaestus Aphrodite Hera Hermes| Names\n"
"| 9/9      12/12      9/9       6/6  8/8   | HP\n"
"| 🔱5       🛡️2        ⛑️                 |/HP boosts\n"
"| 5        2          3         4    2     | DMG\n"
"|          +1🔥                            | DMG boosts\n"
"| ❤️      ❤️        ❤️        ❤️   ❤️    Alive status\n"
"| 👁️      👁️        👁️        👻   👻    | Visibility\n"
"| 💫      3⏳                   | Other effects/Reload \n"
)

# Example formatted player team (manually written)
player_team_example = (
"| Zeus  Athena Ares Apollo Artemis | Names\n"
"| 14/14 10/12  8/8  0/10  9/9     | HP\n"
"|        📯                       | Shields/HP boosts\n"
"| 2     4       3   2      3       | DMG\n"
"| +2💥  +0🔥                      | DMG boosts\n"
"| ❤️    ❤️     ❤️  💀    ❤️     | Alive status\n"
"| 👁️    👁️    👻   👁️     👻    | Visibility\n"
"| 💫    2⏳                     | Other effects/Reload\n"
)

# Embed 4: Enemy team
embed4 = discord.Embed(
    title="🔥 Enemy Team: Player2",
    color=discord.Color.red()
)
embed4.description = f"```\n{enemy_team_example}```"

# Embed 5: Player team
embed5 = discord.Embed(
    title="🛡️ Your Team: Player1",
    color=discord.Color.green()
)
embed5.description = f"```\n{player_team_example}```"

tutorial_embed = discord.Embed(
    title="📖 Battle Rewards Tutorial",
    description="Here’s how money gains and losses work after a match:",
    color=discord.Color.green()
)

# Against the Bot
tutorial_embed.add_field(
    name="🤖 Playing Against the Bot",
    value=(
        "- **If you lose to the bot:** You pay **1000 coins**.\n"
        "- **For each enemy god defeated:** You earn **+500 coins**.\n"
        "- **If you win against the bot:**\n"
        "   • Base reward: **+2500 coins**\n"
        "   • Extra for each enemy god defeated: **+750 coins**\n"
        "   • Bonus for each surviving god on your team: **+1250 coins**"
    ),
    inline=False
)

# Against Another Player
tutorial_embed.add_field(
    name="⚔️ Playing Against Another Player",
    value=(
        "- **Winner’s Rewards:**\n"
        "   • Base reward: **+5000 coins**\n"
        "   • Bonus for each surviving god: **+1000 coins**\n\n"
        "- **Loser’s Penalties:**\n"
        "   • Base penalty: **-2500 coins**\n"
        "   • Bonus for each enemy god defeated: **+850 coins**"
    ),
    inline=False
)

# ---------------- Exports ----------------
embeds: list[discord.Embed] = [embed1, embed2, embed3, embed4, embed5,tutorial_embed]


# ---------------- Helper ----------------
async def switch_view(
    interaction: discord.Interaction,
    new_view: discord.ui.View | None,
    embeds: discord.Embed | list[discord.Embed]
) -> discord.Message:
    if not isinstance(embeds, list):
        embeds = [embeds]

    if interaction.response.is_done():
        msg = await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embeds=embeds,
            view=new_view
        )
        return msg
    else:
        await interaction.response.edit_message(
            embeds=embeds,
            view=new_view
        )
        msg = await interaction.original_response()
        return msg

# ---------------- Tutorial Embed Views ----------------
class TutorialEmbedView(discord.ui.View):
    """View shown when a specific tutorial embed is selected."""
    def __init__(self, user: discord.User, embed: discord.Embed, main_embeds: list[discord.Embed], timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.embed = embed
        self.main_embeds = main_embeds
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    embeds=[discord.Embed(title="✅ Tutorial ended")],
                    view=None
                )
            except discord.NotFound:
                pass

    @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.grey)
    async def return_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user, self.main_embeds)
        msg = await switch_view(interaction, view, self.main_embeds[0])
        view.message = msg

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))

# ---------------- Main Tutorial View ----------------
class TutorialMainView(discord.ui.View):
    """Main tutorial menu with buttons for each embed."""
    def __init__(self, user: discord.User, main_embeds: list[discord.Embed], timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.main_embeds = main_embeds
        self.message: discord.Message | None = None

        # Add a button for each embed except the first (welcome embed1)
        for i, embed in enumerate(main_embeds[1:], start=2):
            self.add_item(self.make_embed_button(i, embed))

    def make_embed_button(self, index: int, embed: discord.Embed) -> discord.ui.Button:
        button = discord.ui.Button(
            label=f"Step {index}: {embed.title}",
            style=discord.ButtonStyle.blurple
        )

        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ This is not your tutorial!", ephemeral=True)
            view = TutorialEmbedView(self.user, embed, self.main_embeds)
            msg = await switch_view(interaction, view, embed)
            view.message = msg

        button.callback = callback
        return button

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    embeds=[discord.Embed(title="✅ Tutorial ended")],
                    view=None
                )
            except discord.NotFound:
                pass

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
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

    def __init__(self, user: discord.User, timeout: int = 900):
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
                new_view = GodDetailView(self.user)

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
                await self.message.edit(
                    embeds=[discord.Embed(title="✅ Tutorial ended")],
                    view=None
                )
            except discord.NotFound:
                pass  # message deleted, safe to ignore

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, row=4, custom_id="exit_gods")
    async def exit_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))

    @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.grey, row=4, custom_id="return_menu")
    async def return_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user)
        msg = await switch_view(interaction, view, embeds)
        view.message = msg   # <-- add this


class GodDetailView(discord.ui.View):
    """View shown when looking at a single god tutorial."""
    def __init__(self, user: discord.User, timeout: int =900):
        super().__init__(timeout=timeout)
        self.user = user
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        if self.message and isinstance(self.message, discord.Message):
            try:
                await self.message.edit(
                    embeds=[discord.Embed(title="✅ Tutorial ended")],
                    view=None
                )
            except discord.NotFound:
                pass  # message deleted, safe to ignore

    @discord.ui.button(label="Return to Gods Menu", style=discord.ButtonStyle.grey, custom_id="return_gods")
    async def return_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GodsMenuView(self.user)
        msg = await switch_view(interaction, view, discord.Embed(title="📜 Select a God to learn more"))
        view.message = msg   # <-- add this


    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, custom_id="exit_god_detail")
    async def exit_detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))
