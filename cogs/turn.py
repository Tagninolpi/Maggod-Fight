import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from typing import Optional

from database.manager import db_manager
from utils.gameplay_tag import God
from bot.utils import update_lobby_status_embed
import asyncio
import re
import unicodedata
from bot.config import Config
from bot.bot_class import BotClass,TurnContext

logger = logging.getLogger(__name__)

def create_team_embeds(team1: list, team2: list, player1_name: str, player2_name: str,action_text: str,allowed) -> list[discord.Embed]:


    def visual_len(s: str) -> int:
        """Estimate visual width of a string."""
        width = 0
        for c in s:
            # Double-width for emojis and wide chars
            if unicodedata.east_asian_width(c) in "WF":
                width += 2
            else:
                width += 1
        return width

    def pad(s: str, width: int = 11) -> str:
        """Pad string visually to match width, accounting for emoji width."""
        vis_length = visual_len(s)
        padding = max(0, width - vis_length)
        return s + " " * padding

    def get_shield(god) -> str:
        icons = []
        if "posi_shield" in god.effects:
            icons.append(f"🔱{god.effects['posi_shield'].value}")
        if "hep_shield" in god.effects:
            icons.append(f"🛡️{god.effects['hep_shield'].value}")
        if "hades_uw_shield" in god.effects:
            icons.append(f"☠️{god.effects['hades_uw_shield'].value}")
        return " ".join(icons)


    def get_dmg_boost(god) -> str:
        icons = []
        if "ares_do_more_dmg" in god.effects:
            val = god.effects["ares_do_more_dmg"].value
            icons.append(f"+{val}🔥")
        if "hades_ow_do_more_dmg" in god.effects:
            val = god.effects["hades_ow_do_more_dmg"].value
            icons.append(f"+{val}💥")
        if "mega_do_less_dmg" in god.effects:
            val = god.effects["mega_do_less_dmg"].value
            icons.append(f"-{val}💚")
        return " ".join(icons)


    def get_hp_boost_icon(god) -> str:
        icons = []
        if "athena_more_max_hp" in god.effects:
            icons.append("📯")
        return " ".join(icons)


    def get_misc_effects_icons(god) -> str:
        icons = []
        if "zeus_stun" in god.effects:
            icons.append("💫")
        if "aphro_charm" in god.effects:
            icons.append("💘")
        if "charon_invisible_duration" in god.effects:
            icons.append("🧿")
        if "tisi_freeze_timer" in god.effects:
            icons.append("❄️")
        if "cerberus_more_max_hp_per_visible_ally" in god.effects:
            icons.append("🐶")
        if "alecto_get_more_dmg" in god.effects:
            icons.append("💢")
        if god.reload>0:
            icons.append(f"{god.reload}⏳")

        return " ".join(icons)

    def format_team(team: list) -> str:
        names = [pad(god.name[:10]) for god in team]

        def bold_digits(s: str) -> str:
            return s.translate(str.maketrans("0123456789", "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"))

        hp_numbers = []
        hp_icons = []

        dmg_numbers = []
        dmg_icons = []

        states = []
        visions = []

        for god in team:
            # HP line
            hp_str = f"{god.hp}/"
            is_hp_boosted = (
                "athena_more_max_hp" in god.effects or
                "cerberus_more_max_hp_per_visible_ally" in god.effects
            )
            raw_max_hp = str(god.max_hp)
            max_hp_str = bold_digits(raw_max_hp) if is_hp_boosted else raw_max_hp
            hp_numbers.append(pad(hp_str + max_hp_str))
            hp_icons.append(pad(get_hp_boost_icon(god) + get_shield(god)))

            # DMG line
            dmg_numbers.append(pad(str(god.dmg)))
            dmg_icons.append(pad(get_dmg_boost(god)))

            # Status lines
            states.append(pad("❤️" if god.alive else "💀", 11))
            visions.append(pad("👁️" if god.visible else "👻", 11))

        misc_effects_line = "".join(pad(get_misc_effects_icons(god)) for god in team)

        lines = [
            "".join(names),
            "".join(hp_numbers),
            "".join(hp_icons),
            "".join(dmg_numbers),
            "".join(dmg_icons),
            "".join(states),
            "".join(visions),
        ]

        if any(get_misc_effects_icons(god) for god in team):
            lines.append(misc_effects_line)

        return "```\n" + "\n".join(lines) + "\n```"
    
    if True:
        if not(action_text == "attack"):
            embed1 = discord.Embed(title=f"{player1_name}'s Team", color=discord.Color.green())
            embed1.description = format_team(team1)

            embed2 = discord.Embed(title=f"{player2_name}'s Team", color=discord.Color.red())
            embed2.description = format_team(team2)
        else:
            embed1 = discord.Embed(title=f"{player2_name}'s Team", color=discord.Color.red())
            embed1.description = format_team(team1)

            embed2 = discord.Embed(title=f"{player1_name}'s Team", color=discord.Color.green())
            embed2.description = format_team(team2)
        if True : # change allowed == match.player1_id
            action_embed = discord.Embed(
                title=f"🎯 Player select God to {action_text.title()}",
                color=0x00ff00
            )
        else:
            action_embed = discord.Embed(
                title=f"🎯 {player2_name} select God to {action_text.title()}",
                color=0x00ff00
            )
    return [action_embed, embed2, embed1]
    

class GodSelectionView(discord.ui.View):
    def __init__(self, all_gods: list[God], selectable_gods: list[God], allowed_user: int, team_1):
        super().__init__(timeout=300)
        self.allowed_user = allowed_user
        self.selected_god = None

        for god in team_1:
            if god in selectable_gods:
                self.add_item(self.make_button(god))
            else:
                self.add_item(self.make_placeholder())

    def make_button(self, god: God):
        # Truncate and pad name to exactly 11 characters
        label = god.name[:11].ljust(11, " ")
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.allowed_user:
                await interaction.response.send_message("You're not allowed to select a god.", ephemeral=True)
                return

            self.selected_god = god

            # Disable all buttons in this view
            for item in self.children:
                item.disabled = True

            # Edit the original message to update buttons state
            await interaction.message.edit(view=self)

            self.stop()
        button.callback = callback
        return button

    def make_placeholder(self):
        # Create placeholder with same width as buttons
        label = "-" * 11
        return discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, disabled=True)


class Turn(commands.Cog):
    """Cog for handling battle turns in Maggod Fight."""
    
    def __init__(self, bot):
        self.bot = bot

    async def send_god_selection_prompt(
        self,
        channel: discord.TextChannel,
        team1: list,
        team2: list,
        selectable_gods: list,
        action_text: str,
        allowed_user: int
    ) -> Optional[God]:
        """Send a god selection prompt and return the selected god."""
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel.id)
        if not match:
            await channel.send("❌ No ongoing match.")
            return None


        # Auto-select if in solo mode and it's the bot's turn
        if match.solo_mode and  match.turn_state["current_player"] == 123:
           selected = BotClass(match.ai_bot_name).choose_god(
    TurnContext(selectable_gods, team1, team2, action_text)
)
           return selected
        
        # Create embeds showing team status
        embeds = create_team_embeds(team1, team2, match.player1_name, match.player2_name,action_text,allowed_user)
        
        # Create selection view
        view = GodSelectionView(all_gods= team1 + team2,selectable_gods=selectable_gods, allowed_user=allowed_user,team_1=team1)

        # Send the embed with the view
        msg = await channel.send(embeds=embeds, view=view)

        # Set whether to delete the UI after selection
        delete_UI = True

        try:
            # Wait for selection, timeout after 15 minutes (900s)
            await asyncio.wait_for(view.wait(), timeout=900)
        except asyncio.TimeoutError:
            # Handle timeout: no selection made
            view.selected_god = None

        # Optionally delete the message
        if delete_UI:
            try:
                await msg.delete()
            except discord.NotFound:
                pass


        if view.selected_god is None:
            # Timeout occurred
            await channel.send("⏱️ Selection timed out. Match has been reset.")
            match = matchmaking_dict[channel.id]
            match.game_phase = "Waiting for first player"
            #asyncio.create_task(update_lobby_status_embed(self.bot))
            # Reset the match
            if channel.id in matchmaking_dict:
                del matchmaking_dict[channel.id]
            return None

        return view.selected_god

    async def execute_turn(self, channel: discord.TextChannel, attack_team: list, defend_team: list, current_player: int):
        """Execute a complete turn for the attacking team."""
        from utils.game_test_on_discord import (
            get_visible, get_alive, get_dead, set_first_god_visible,
            became_visible_gain_effect, action_befor_delete_effect, action_befor_die,
        )

        # Ensure at least one god is visible on each team
        set_first_god_visible(attack_team)
        set_first_god_visible(defend_team)

        # Check if any gods are available to attack
        visible_attackers = get_visible(attack_team)
        alive_attackers = get_alive(attack_team,True)
        if not visible_attackers:
            await channel.send("❌ No gods available to attack with. This issue is not normal please repport it")
            return

        # Select attacker
        attacker = await self.send_god_selection_prompt(
            channel, attack_team, defend_team, alive_attackers, "attack with", current_player
        )
        
        if not attacker:
            return

        # Select target
        visible_defenders = get_visible(defend_team)
        
        # Check if any alive & visible ally has the special Cerberus effect
        buffed_ally = next(
            (god for god in defend_team
            if "cerberus_more_max_hp_per_visible_ally" in god.effects and god.alive),
            None
            )
        attacked = buffed_ally # add message to say it was auto selected
        if buffed_ally:
            from bot.utils import matchmaking_dict
            match = matchmaking_dict.get(channel.id)
            BotClass(match.ai_bot_name).choose_god(TurnContext(attack_cerbs=True))
        else:
            if not visible_defenders:
                await channel.send("❌ No visible targets available. Turn skipped.")
                return
            if attacker.name == "aphrodite":
                alive_ennemy = get_alive(defend_team)
                attacked = await self.send_god_selection_prompt(
                    channel,defend_team ,attack_team ,alive_ennemy , "attack", current_player
                    )
            else:
                attacked = await self.send_god_selection_prompt(
                    channel, defend_team, attack_team, visible_defenders, "attack", current_player
                    )
            
            if not attacked:
                return

        # Make attacker visible if not already
        if not attacker.visible:
            attacker.visible = True
            became_visible_gain_effect(attack_team, attacker)

        # Handle special abilities and targeting
        target = attacked
        attacker_1 = None
        attacker_2 = None

        # Handle god-specific ability targeting
        if attacker.name == "charon":
            visible_allies = get_visible(attack_team)
            if visible_allies:
                target = await self.send_god_selection_prompt(
                    channel, attack_team, defend_team, visible_allies, "protect", current_player
                )

        elif attacker.name == "persephone":
            team_gods = attack_team  # Can target dead or alive allies
            if team_gods:
                target = await self.send_god_selection_prompt(
                    channel, attack_team, defend_team, team_gods, "revive/heal", current_player
                )

        elif attacker.name == "hecate":
            visible_allies = get_visible(attack_team)
            if visible_allies:
                target = await self.send_god_selection_prompt(
                    channel, attack_team, defend_team, visible_allies, "make invisible", current_player
                )

        elif attacker.name == "cerberus":
            visible_allies = get_visible(attack_team)
            if visible_allies:
                target = await self.send_god_selection_prompt(
                    channel, attack_team, defend_team, visible_allies, "give attract⛑️", current_player
                )

        elif attacker.name == "hermes":
            visible_allies = get_visible(attack_team,True)
            if len(visible_allies) > 1:
                # Hermes can attack with other gods
                other_gods = [g for g in visible_allies if g.name != "hermes"]
                if other_gods:
                    attacker_1 = await self.send_god_selection_prompt(
                        channel, attack_team, defend_team, other_gods, "attack with (1st)", current_player
                    )
                    
                    if len(other_gods) > 1:
                        remaining_gods = [g for g in other_gods if g != attacker_1]
                        if remaining_gods:
                            attacker_2 = await self.send_god_selection_prompt(
                                channel, attack_team, defend_team, remaining_gods, "attack with (2nd)", current_player
                            )

        # Execute the ability
        try:
            # Store HP before attack
            attacked_hp_before = attacked.hp
            
            # Basic damage
            damage = attacker.do_damage()
            attacker.visible = True
            attacked.get_dmg(value=damage)
                
            # Execute god ability
            ability_params = {
                "visible_gods": get_visible(attack_team),
                "target": target,
                "ennemy_team": get_alive(defend_team),
                "visible_ennemy_team": get_visible(defend_team),
                "self": attacker,
                "ally_team": get_alive(attack_team),
                "attacker_1": attacker_1,
                "attacker_2": attacker_2,
                "dead_ally": get_dead(attack_team),
            }
            
            if attacker.check_abillity():
                ability_message = attacker.ability(ability_params)
            else:
                ability_message = f"{attacker.name.capitalize()} abillity is on cooldown you can use it in {attacker.reload} turns"
             
            from bot.utils import matchmaking_dict
            match = matchmaking_dict.get(channel.id)
            if match.solo_mode and  match.turn_state["current_player"] == 123:
                color = discord.Color.red()
            else:
                if current_player == match.player1_id:
                    color = discord.Color.green()
                else:
                    color = discord.Color.red()

            embed = discord.Embed(color=color)

            desc = ""
            # Case: Cerberus forces attacker
            if buffed_ally:
                desc += f"🐕 Cerberus Effect: **{buffed_ally.name.capitalize()}** forces **{attacker.name.capitalize()}** to target it!\n"
            # Damage info
            damage_dealt = attacked_hp_before - attacked.hp
            desc += f"💥 Attack: **{attacker.name.capitalize()}** deals {damage_dealt} damage to **{attacked.name.capitalize()}** (HP: {attacked.hp}/{attacked.max_hp})\n"

            # Ability effect
            if ability_message:
                desc += ability_message

            embed.description = desc

            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error executing ability for {attacker.name}: {e}")
            await channel.send(f"⚠️ Error executing {attacker.name}'s ability.")

        # Clean up effects and handle deaths
        action_befor_delete_effect(attack_team)
        action_befor_delete_effect(defend_team)
        msg = action_befor_die(defend_team, attack_team)
        if msg:
            await channel.send(msg)
        action_befor_delete_effect(defend_team)
        msg = action_befor_die(attack_team, defend_team)
        if msg:
            await channel.send(msg)
        

        # Update effects
        for god in attack_team + defend_team:
            god.update_effects()

        # Check for winner
        team1_alive = any(god.alive for god in attack_team)
        team2_alive = any(god.alive for god in defend_team)
        
        if not team1_alive or not team2_alive:
            await self.end_game(channel, team1_alive, team2_alive)
            return True  # Game ended

        return False  # Game continues

    async def end_game(self, channel: discord.TextChannel, team1_alive: bool, team2_alive: bool):
        """End the game and declare winner."""
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel.id)
        if not match:
            return None,True
 
        # Update bot stats
        if hasattr(self.bot, 'stats'):
            self.bot.stats.increment_match_completed()

        # Determine winner
        if team1_alive and not team2_alive:
            winner_id = match.player1_id
            winner_name = match.player1_name
        elif team2_alive and not team1_alive:
            if match.solo_mode:
                winner_id = 123
                winner_name = "bot"
            else:
                winner_id = match.player2_id
                winner_name = match.player2_name
        else:
            winner_id = None
            winner_name = "Nobody"

        # Get winner's display name
        if winner_id and match.solo_mode:
            winner = channel.guild.get_member(winner_id)
            winner_name = winner.display_name if winner else winner_name

        # Create victory embed
        embed = discord.Embed(
            title="🏆 Victory!",
            description=f"The battle has ended! **{winner_name}** emerges victorious!",
            color=discord.Color.gold()
        )
        
        if winner_id:
            if match.solo_mode:
                embed.add_field(
                    name="🎉 Congratulations!",
                    value=f" The maggod bot has proven their tactical superiority in this epic battle of the gods!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🎉 Congratulations!",
                    value=f"<@{winner_id}> has proven their tactical superiority in this epic battle of the gods!",
                    inline=False
                )
        else:
            embed.add_field(
                name="🤝 Epic Draw!",
                value="Both armies have been completely eliminated! What a legendary battle!",
                inline=False
            )

        # Show final team status
        try:            
            team1_survivors = sum(1 for god in match.teams[match.player1_id] if god.alive)
            team2_survivors = sum(1 for god in match.teams[match.player2_id] if god.alive)
            
            embed.add_field(
                name="📊 Final Score",
                value=f"**{match.player1_name}:** {team1_survivors} gods remaining\n**{match.player2_name}:** {team2_survivors} gods remaining",
                inline=False
            )
        except Exception as e:
            logger.error(f"Error showing final scores: {e}")

        embed.add_field(
            name="🎮 Play Again?",
            value="Use `/join` in any lobby to start a new match!",
            inline=False
        )

        await channel.send(embed=embed)

        del matchmaking_dict[channel.id]
        #asyncio.create_task(update_lobby_status_embed(self.bot))


    @app_commands.command(name="do", description="Make your turn in the ongoing Maggod Fight battle.")

    async def do_turn_slash(self, interaction: discord.Interaction):
        """Execute a turn in the battle."""
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            )
            return

        if not channel.category or channel.category.id != Config.LOBBY_CATEGORY_ID:
            await interaction.response.send_message(
                f"❌ You must use this command in a `{Config.LOBBY_CATEGORY_NAME}` channel.",
                ephemeral=True
            )
            return

        if not channel.name.startswith("⚔️-maggod-lobby-"):
            await interaction.response.send_message(
                "❌ You must use this command in a Maggod lobby channel.",
                ephemeral=True
            )
            return
        
        from bot.utils import matchmaking_dict
        match = matchmaking_dict.get(interaction.channel.id)
        if not match or interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.response.send_message(
                "❌ You are not a participant in this match.",
                ephemeral=True
            )
            return

        if not match or match.game_phase != "playing":
            await interaction.response.send_message(
                f"❌ You can't use this command now (required phase: playing).",
                ephemeral=True
            )
            return
        
        if match and match.turn_in_progress:
            await interaction.response.send_message(
                "❌ A turn is already in progress. Please choose a god.",
                ephemeral=True
            )
            return
        
        # start
        # Check if it's the player's turn
        current_player_id = match.turn_state["current_player"]
        if interaction.user.id != current_player_id and not(match.solo_mode):
            await interaction.response.send_message(
                "⏳ It is not your turn yet. Please wait for your opponent.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        match.turn_in_progress = True
        while match.turn_in_progress and match:
            if not match:
                break
            match.next_picker = match.turn_state["current_player"]
            try:
                # Determine which team is attacking
                if match.turn_state["current_player"] == 123:
                    attack_team = match.teams[match.player2_id]
                    defend_team = match.teams[match.player1_id]
                elif match.next_picker == match.player1_id:
                    attack_team = match.teams[match.player1_id]
                    defend_team = match.teams[match.player2_id]
                else:
                    attack_team = match.teams[match.player2_id]
                    defend_team = match.teams[match.player1_id]

                # Execute the turn
                game_ended = await self.execute_turn(channel, attack_team, defend_team, match.next_picker)

                if not game_ended:
                    # Switch turns
                    match.turn_state["current_player"] = (
                        match.player2_id if match.turn_state["current_player"] == match.player1_id else match.player1_id
                    )
                    match.turn_state["turn_number"] += 1
                    match.next_picker = match.player1_id if match.next_picker == match.player2_id else match.player2_id

                    # Update game save after each turn
                    await db_manager.update_game_save(channel, match) #database
                    await asyncio.sleep(5)
                else:
                    # Delete game save after match is over
                    pass #database
                    await db_manager.delete_game_save(channel, match)
                    match.turn_in_progress = False
                    break
                
            except Exception as e:
                logger.error(f"Error in do_turn: {e}")
                await interaction.followup.send(
                    "❌ An error occurred during your turn. Please try again.",
                    ephemeral=True
                )
                break
                match.turn_in_progress = False
                

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Turn(bot))
