import discord
from .god_embeds import GodTutorials

# ---------------- Embeds ----------------

### Embed 1: Introduction
embed1 = discord.Embed(
    title="🏟️ Welcome to the Maggod Fight Arena!",
    description=(
        "This is a **turn-based combat game** where you can battle against "
        "other players or bots to **win rewards** and prove your strength!"
    ),
    color=discord.Color.gold()
)


### Embed 2: Channels overview
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

### Merged Embed: Example of Battle View
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
battle_view_embed = discord.Embed(title="🎯 Example of Battle View",color=discord.Color.green())
# Step 3 description
battle_view_embed.add_field(name="Action Prompt",value="Select one of your gods to perform an action.",inline=False)
# Enemy team
battle_view_embed.add_field(name="🔥 Enemy Team: Player2",value=f"```\n{enemy_team_example}```",inline=False)
# Player team
battle_view_embed.add_field(name="🛡️ Your Team: Player1",value=f"```\n{player_team_example}```",inline=False)


tutorial_embed = discord.Embed(title="📖 Battle Rewards Tutorial",description="Here’s how money gains and losses work after a match:",color=discord.Color.green())

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

# ---------------- Global main_embeds ----------------
main_embeds = [embed1, embed2, battle_view_embed, tutorial_embed]

# ---------------- Helper ----------------
async def switch_view(interaction: discord.Interaction, new_view: discord.ui.View | None, embeds: discord.Embed | list[discord.Embed]):
    if not isinstance(embeds, list):
        embeds = [embeds]

    if interaction.response.is_done():
        return await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embeds=embeds,
            view=new_view
        )
    else:
        await interaction.response.edit_message(
            embeds=embeds,
            view=new_view
        )
        return await interaction.original_response()
# ---------------- Tutorial Views ----------------
# ---------------- Tutorial Views ----------------
class TutorialEmbedView(discord.ui.View):
    def __init__(self, user: discord.User, embed: discord.Embed, god_tutorials, timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.embed = embed
        self.god_tutorials = god_tutorials
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embeds=[discord.Embed(title="✅ Tutorial ended")], view=None)
            except discord.NotFound:
                pass

    @discord.ui.button(label="Return to Menu", style=discord.ButtonStyle.grey)
    async def return_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user, self.god_tutorials)
        # Show full main menu (all steps)
        msg = await switch_view(interaction, view, main_embeds[1:])  # skip welcome embed
        view.message = msg

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))


# ---------------- Tutorial Main Menu ----------------
class TutorialMainView(discord.ui.View):
    def __init__(self, user: discord.User, god_tutorials, timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.god_tutorials = god_tutorials
        self.message: discord.Message | None = None

        # Add buttons for each main embed (skip welcome embed)
        for i, embed in enumerate(main_embeds[1:], start=2):
            self.add_item(self.make_embed_button(i, embed))

        # Add the God Tutorials button
        god_button = discord.ui.Button(label="God Tutorials", style=discord.ButtonStyle.blurple)
        god_button.callback = self.open_god_tutorials
        self.add_item(god_button)

    def make_embed_button(self, index: int, embed: discord.Embed) -> discord.ui.Button:
        button = discord.ui.Button(label=f"Step {index}: {embed.title}", style=discord.ButtonStyle.blurple)

        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ This is not your tutorial!", ephemeral=True)
            view = TutorialEmbedView(self.user, embed, self.god_tutorials)
            msg = await switch_view(interaction, view, embed)
            view.message = msg

        button.callback = callback
        return button

    async def open_god_tutorials(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ This is not your tutorial!", ephemeral=True)

        view = GodsMenuView(self.user, self.god_tutorials)
        menu_embed = discord.Embed(
            title="🧙 God Tutorials Menu",
            description="Select a god to view their tutorial.",
            color=discord.Color.blurple()
        )
        msg = await switch_view(interaction, view, menu_embed)
        view.message = msg

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embeds=[discord.Embed(title="✅ Tutorial ended")], view=None)
            except discord.NotFound:
                pass

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit_tutorial(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))


# ---------------- Gods Views ----------------
class GodsMenuView(discord.ui.View):
    GODS = [
        "poseidon", "hephaestus", "aphrodite", "ares", "hera",
        "zeus", "athena", "apollo", "artemis", "hermes",
        "hades_ow", "thanatos", "cerberus", "charon", "persephone",
        "hades_uw", "tisiphone", "alecto", "megaera", "hecate"
    ]

    def __init__(self, user: discord.User, god_tutorials, timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.god_tutorials = god_tutorials
        self.message: discord.Message | None = None

        # Add god buttons dynamically (5 per row)
        for i, god_name in enumerate(self.GODS):
            button = discord.ui.Button(label=god_name.title(), style=discord.ButtonStyle.blurple, row=i//5)
            button.callback = self.make_god_callback(god_name)
            self.add_item(button)

    def make_god_callback(self, god_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ This is not your tutorial!", ephemeral=True)

            god_func = getattr(self.god_tutorials, god_name, None)
            if god_func:
                embeds = god_func()
                view = GodDetailView(self.user, self.god_tutorials)
                msg = await switch_view(interaction, view, embeds)
                view.message = msg
        return callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embeds=[discord.Embed(title="✅ Tutorial ended")], view=None)
            except discord.NotFound:
                pass

    # Return buttons
    @discord.ui.button(label="Return to Main Menu", style=discord.ButtonStyle.grey, row=4)
    async def return_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user, self.god_tutorials)
        msg = await switch_view(interaction, view, main_embeds[1:])  # show main menu
        view.message = msg

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, row=4)
    async def exit_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))


# ---------------- God Detail View ----------------
class GodDetailView(discord.ui.View):
    def __init__(self, user: discord.User, god_tutorials, timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.god_tutorials = god_tutorials
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embeds=[discord.Embed(title="✅ Tutorial ended")], view=None)
            except discord.NotFound:
                pass

    @discord.ui.button(label="Return to Gods Menu", style=discord.ButtonStyle.grey)
    async def return_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GodsMenuView(self.user, self.god_tutorials)
        menu_embed = discord.Embed(
            title="🧙 God Tutorials Menu",
            description="Select a god to view their tutorial.",
            color=discord.Color.blurple()
        )
        msg = await switch_view(interaction, view, menu_embed)  # correct embed for gods menu
        view.message = msg

    @discord.ui.button(label="Return to Main Menu", style=discord.ButtonStyle.grey)
    async def return_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user, self.god_tutorials)
        msg = await switch_view(interaction, view, main_embeds[1:])  # show main menu
        view.message = msg

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))



# ---------------- God Detail View ----------------
class GodDetailView(discord.ui.View):
    def __init__(self, user: discord.User, god_tutorials, timeout: int = 900):
        super().__init__(timeout=timeout)
        self.user = user
        self.god_tutorials = god_tutorials
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(embeds=[discord.Embed(title="✅ Tutorial ended")], view=None)
            except discord.NotFound:
                pass

    @discord.ui.button(label="Return to Gods Menu", style=discord.ButtonStyle.grey)
    async def return_gods(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = GodsMenuView(self.user, self.god_tutorials)
        msg = await switch_view(interaction, view, main_embeds[0])
        view.message = msg

    @discord.ui.button(label="Return to Main Menu", style=discord.ButtonStyle.grey)
    async def return_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TutorialMainView(self.user, self.god_tutorials)
        msg = await switch_view(interaction, view, main_embeds[0])
        view.message = msg

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red)
    async def exit_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        await switch_view(interaction, None, discord.Embed(title="✅ Tutorial ended"))