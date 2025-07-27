import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from typing import Optional
from utils.gameplay_tag import God
from bot.utils import update_lobby_status_embed
import asyncio


logger = logging.getLogger(__name__)

def create_team_embeds(team1: list, team2: list, player1_name: str, player2_name: str,action_text: str) -> list[discord.Embed]:
    def pad(value: str, width: int = 11) -> str:
        return value.ljust(width)

    def format_team(team: list) -> str:
        names = [pad(god.name[:10]) for god in team]
        hps = [pad(f"{god.hp}/{god.max_hp}") for god in team]
        dmgs = [pad(str(god.dmg)) for god in team]
        states = [pad("❤️" if god.alive else "💀",6) for god in team]
        visions = [pad("👁️" if god.visible else "👻",7) for god in team]

        lines = [
            " ".join(names),
            " ".join(hps),
            " ".join(dmgs),
            " ".join(states),
            "".join(visions),
        ]
        return "```\n" + "\n".join(lines) + "\n```"

    embed1 = discord.Embed(title=f"{player1_name}'s Team", color=discord.Color.green())
    embed1.description = format_team(team1)

    embed2 = discord.Embed(title=f"{player2_name}'s Team", color=discord.Color.red())
    embed2.description = format_team(team2)
    action_embed = discord.Embed(
        title=f"🎯 Select God to {action_text.title()}",
        color=0x00ff00
    )
    return [action_embed, embed2, embed1]

class GodSelectionView(discord.ui.View):
    def __init__(self, all_gods: list[God], selectable_gods: list[God], allowed_user: discord.Member):
        super().__init__(timeout=300)
        self.allowed_user = allowed_user
        self.selected_god = None

        for god in all_gods:
            if god in selectable_gods:
                self.add_item(self.make_button(god))
            else:
                self.add_item(self.make_placeholder())

    def make_button(self, god: God):
        label = god.name[:10].center(11)  # Centered name
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)

        async def callback(interaction: discord.Interaction):
            if interaction.user != self.allowed_user:
                await interaction.response.send_message("You're not allowed to select this god.", ephemeral=True)
                return
            self.selected_god = god
            self.stop()
            await interaction.response.send_message(f"You selected {god.name}", ephemeral=True)

        button.callback = callback
        return button

    def make_placeholder(self):
        # A blank label that still takes up space
        return discord.ui.Button(label=" " * 11, style=discord.ButtonStyle.secondary, disabled=True)

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
        allowed_user: discord.Member
    ) -> Optional[God]:
        """Send a god selection prompt and return the selected god."""
        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel.id)
        if not match:
            await channel.send("❌ No ongoing match.")
            return None 

        # Get player names
        player1 = channel.guild.get_member(match.player1_id)
        player2 = channel.guild.get_member(match.player2_id)
        
        player1_name = player1.display_name if player1 else "Player 1"
        player2_name = player2.display_name if player2 else "Player 2"

        # Create embeds showing team status
        embeds = create_team_embeds(team1, team2, player1_name, player2_name,action_text)
        
        # Create selection view
        view = GodSelectionView(selectable_gods=selectable_gods, allowed_user=allowed_user)

        msg = await channel.send(
            f"{allowed_user.mention}, select a god to {action_text}:",
            embeds=embeds,
            view=view
        )

        # Wait for selection
        await view.wait()
        
        # Clean up the message
        try:
            await msg.delete()
        except discord.NotFound:
            pass

        if view.selected_god is None:
            # Timeout occurred
            await channel.send("⏱️ Selection timed out. Match has been reset.")
            match = matchmaking_dict[channel.id]
            match.game_phase = "Waiting for first player"
            asyncio.create_task(update_lobby_status_embed(self.bot))
            # Reset the match
            if channel.id in matchmaking_dict:
                del matchmaking_dict[channel.id]
            
            
            return None

        return view.selected_god

    async def execute_turn(self, channel: discord.TextChannel, attack_team: list, defend_team: list, current_player: discord.Member):
        """Execute a complete turn for the attacking team."""
        from utils.game_test_on_discord import (
            get_visible, get_alive, get_dead, set_first_god_visible,
            became_visible_gain_effect, action_befor_delete_effect, action_befor_die
        )

        # Ensure at least one god is visible on each team
        set_first_god_visible(attack_team)
        set_first_god_visible(defend_team)

        # Check if any gods are available to attack
        visible_attackers = get_visible(attack_team)
        alive_attackers = get_alive(attack_team)
        if not visible_attackers:
            await channel.send("❌ No gods available to attack with. Turn skipped.")
            return

        # Select attacker
        attacker = await self.send_god_selection_prompt(
            channel, attack_team, defend_team, alive_attackers, "attack with", current_player
        )
        
        if not attacker:
            return

        # Select target
        visible_defenders = get_visible(defend_team)
        
        # Check for Cerberus special targeting
        cerebus_present = any(god.name == "cerebus" and god.visible for god in defend_team)
        if cerebus_present:
            # Cerberus forces all attacks to target it
            attacked = next(god for god in defend_team if god.name == "cerebus")
            await channel.send(f"🐕 **Cerberus** forces the attack to target it!")
        else:
            if not visible_defenders:
                await channel.send("❌ No visible targets available. Turn skipped.")
                return
            
            attacked = await self.send_god_selection_prompt(
                channel, defend_team, attack_team, visible_defenders, "attack", current_player
            )
            
            if not attacked:
                return

        # Make attacker visible if not already
        if not attacker.visible:
            attacker.visible = True
            became_visible_gain_effect(attack_team, attacker)

        # Execute the attack
        embed = discord.Embed(
            title="⚔️ Battle Action!",
            description=f"**{attacker.name}** attacks **{attacked.name}**!",
            color=0xff6b6b
        )
        
        embed.add_field(
            name="🗡️ Attacker",
            value=f"**{attacker.name}** (HP: {attacker.hp}/{attacker.max_hp}, DMG: {attacker.dmg})",
            inline=True
        )
        
        embed.add_field(
            name="🛡️ Defender",
            value=f"**{attacked.name}** (HP: {attacked.hp}/{attacked.max_hp})",
            inline=True
        )

        await channel.send(embed=embed)

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

        elif attacker.name == "hermes":
            visible_allies = get_visible(attack_team)
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
            
            # Basic damage if not Hades (Overworld)
            if attacker.name != "hades_ow":
                damage = attacker.do_damage()
                attacked.get_dmg(value=damage)
                
                damage_dealt = attacked_hp_before - attacked.hp
                await channel.send(f"💥 **{attacker.name}** deals {damage_dealt} damage to **{attacked.name}**! (HP: {attacked.hp}/{attacked.max_hp})")

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
            
            attacker.ability(ability_params)
            
            # Show ability effect
            await channel.send(f"✨ **{attacker.name}** uses their special ability!")
            
        except Exception as e:
            logger.error(f"Error executing ability for {attacker.name}: {e}")
            await channel.send(f"⚠️ Error executing {attacker.name}'s ability.")

        # Clean up effects and handle deaths
        action_befor_delete_effect(attack_team, defend_team)
        action_befor_delete_effect(defend_team, attack_team)
        action_befor_die(defend_team, attack_team)

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
        from main import matchmaking_dict

        match = matchmaking_dict.get(channel.id)
        if not match:
            return

        # Update bot stats
        if hasattr(self.bot, 'stats'):
            self.bot.stats.increment_match_completed()

        # Determine winner
        if team1_alive and not team2_alive:
            winner_id = match.player1_id
            winner_name = "Player 1"
        elif team2_alive and not team1_alive:
            winner_id = match.player2_id
            winner_name = "Player 2"
        else:
            winner_id = None
            winner_name = "Nobody"

        # Get winner's display name
        if winner_id:
            winner = channel.guild.get_member(winner_id)
            winner_name = winner.display_name if winner else winner_name

        # Create victory embed
        embed = discord.Embed(
            title="🏆 Victory!",
            description=f"The battle has ended! **{winner_name}** emerges victorious!",
            color=discord.Color.gold()
        )
        
        if winner_id:
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
            player1 = channel.guild.get_member(match.player1_id)
            player2 = channel.guild.get_member(match.player2_id)
            
            player1_name = player1.display_name if player1 else "Player 1"
            player2_name = player2.display_name if player2 else "Player 2"
            
            team1_survivors = sum(1 for god in match.teams[match.player1_id] if god.alive)
            team2_survivors = sum(1 for god in match.teams[match.player2_id] if god.alive)
            
            embed.add_field(
                name="📊 Final Score",
                value=f"**{player1_name}:** {team1_survivors} gods remaining\n**{player2_name}:** {team2_survivors} gods remaining",
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

        # Clean up
        match.game_phase = "finished"
        asyncio.create_task(update_lobby_status_embed(self.bot))


    @app_commands.command(name="do_turn", description="Make your turn in the ongoing Maggod Fight battle.")
    async def do_turn_slash(self, interaction: discord.Interaction):
        """Execute a turn in the battle."""
        channel = interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ This command must be used in a text channel.",
                ephemeral=True
            ) 
            return

        from bot.utils import matchmaking_dict

        match = matchmaking_dict.get(channel.id)
        if not match:
            await interaction.response.send_message(
                "❌ No match found in this channel.",
                ephemeral=True
            )
            return

        if match.game_phase != "playing":
            await interaction.response.send_message(
                "❌ The battle hasn't started yet. Use `/start` to begin team building.",
                ephemeral=True
            )
            return

        if interaction.user.id not in [match.player1_id, match.player2_id]:
            await interaction.response.send_message(
                "🚫 You are not a participant in this match.",
                ephemeral=True
            )
            return

        # Check if it's the player's turn
        current_player_id = match.turn_state["current_player"]
        if interaction.user.id != current_player_id:
            await interaction.response.send_message(
                "⏳ It is not your turn yet. Please wait for your opponent.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # Determine which team is attacking
            if interaction.user.id == match.player1_id:
                attack_team = match.teams[match.player1_id]
                defend_team = match.teams[match.player2_id]
            else:
                attack_team = match.teams[match.player2_id]
                defend_team = match.teams[match.player1_id]

            # Execute the turn
            game_ended = await self.execute_turn(channel, attack_team, defend_team, interaction.user)

            if not game_ended:
                # Switch turns
                match.turn_state["current_player"] = (
                    match.player2_id if interaction.user.id == match.player1_id else match.player1_id
                )
                match.turn_state["turn_number"] += 1
                
                # Announce next turn
                next_player = channel.guild.get_member(match.turn_state["current_player"])
                next_player_name = next_player.display_name if next_player else "Next Player"
                
                embed = discord.Embed(
                    title="🔄 Next Turn",
                    description=f"Turn {match.turn_state['turn_number']}: **{next_player_name}**'s turn!",
                    color=0x00bfff
                )
                embed.add_field(
                    name="🎯 Action Required",
                    value=f"<@{match.turn_state['current_player']}>, use `/do_turn` to make your move!",
                    inline=False
                )
                
                await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in do_turn: {e}")
            await interaction.followup.send(
                "❌ An error occurred during your turn. Please try again.",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for the cog."""
    await bot.add_cog(Turn(bot))
