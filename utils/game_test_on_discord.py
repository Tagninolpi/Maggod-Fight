from utils.gameplay_tag import God, Effect, EffectType
import utils.abilities_tag as abilities
import random as r
 
# God abilities mapping
abilities_ = {
    "poseidon": abilities.poseidon,
    "hephaestus": abilities.hephaestus,
    "aphrodite": abilities.aphrodite,
    "ares": abilities.ares,
    "hera": abilities.hera,
    "zeus": abilities.zeus,
    "athena": abilities.athena,
    "apollo": abilities.apollo,
    "artemis": abilities.artemis,
    "hermes": abilities.hermes,
    "hades_ow": abilities.hades_ow,
    "thanatos": abilities.thanatos,
    "cerebus": abilities.cerebus,
    "charon": abilities.charon,
    "persephone": abilities.persephone,
    "hades_uw": abilities.hades_uw,
    "tisiphone": abilities.tisiphone,
    "alecto": abilities.alecto,
    "megaera": abilities.megaera,
    "hecate": abilities.hecate,
}

# All available gods with their stats
gods = {
    "poseidon": God("poseidon", 10, 4, abilities_["poseidon"]),
    "hephaestus": God("hephaestus", 12, 2, abilities_["hephaestus"]),
    "aphrodite": God("aphrodite", 10, 3, abilities_["aphrodite"]),
    "ares": God("ares", 9, 5, abilities_["ares"]),
    "hera": God("hera", 8, 5, abilities_["hera"]),
    "zeus": God("zeus", 14, 2, abilities_["zeus"]),
    "athena": God("athena", 12, 3, abilities_["athena"]),
    "apollo": God("apollo", 9, 4, abilities_["apollo"]),
    "artemis": God("artemis", 7, 3, abilities_["artemis"]),
    "hermes": God("hermes", 7, 1, abilities_["hermes"]),
    "hades_ow": God("hades_ow", 8, 3, abilities_["hades_ow"]),
    "thanatos": God("thanatos", 11, 2, abilities_["thanatos"]),
    "cerebus": God("cerebus", 9, 3, abilities_["cerebus"]),
    "charon": God("charon", 10, 5, abilities_["charon"]),
    "persephone": God("persephone", 8, 3, abilities_["persephone"]),
    "hades_uw": God("hades_uw", 6, 3, abilities_["hades_uw"]),
    "tisiphone": God("tisiphone", 11, 3, abilities_["tisiphone"]),
    "alecto": God("alecto", 9, 3, abilities_["alecto"]),
    "megaera": God("megaera", 9, 3, abilities_["megaera"]),
    "hecate": God("hecate", 10, 4, abilities_["hecate"]),
}

# Default teams for testing (not used in actual matches)
team_1 = [
    gods["hades_ow"], gods["artemis"], gods["persephone"], gods["alecto"], gods["hephaestus"]
]
team_2 = [
    gods["charon"], gods["poseidon"], gods["zeus"], gods["hermes"], gods["apollo"]
]

def set_first_god_visible(team):
    """Make the first alive god visible if no gods are visible."""
    visible_gods = get_visible(team,True)
    if not visible_gods:
        for god in team:
            if god.alive:
                god.visible = True
                became_visible_gain_effect(team, god)
                break

def became_visible_gain_effect(team, target):
    """Apply passive effects when a god becomes visible."""
    for god in team:
        if god.alive and god.visible:
            try:
                if god.name == "poseidon":
                    god.ability({
                        "target": target,
                        "visible_gods": get_visible(team)
                    })
                elif god.name == "athena":
                    god.ability({
                        "target": target,
                        "visible_gods": get_visible(team)
                    })
                elif god.name == "cerebus":
                    god.ability({
                        "target": target,
                        "visible_gods": get_visible(team),
                        "self": god
                    })
                elif god.name == "ares":
                    god.ability({
                        "target": target,
                        "visible_gods": get_visible(team)
                    })
            except Exception as e:
                print(f"Error in passive ability for {god.name}: {e}")


def get_visible(team,stunned = False):
    if stunned:
        return [god for god in team if god.visible and god.alive and not any(e in god.effects for e in {"zeus_stun","tisi_freeze_timer"})]
    else:
        """Get all visible and alive gods from a team."""
        return [god for god in team if god.visible and god.alive]

def get_alive(team,stunned = False):
    if stunned:
        return [god for god in team if god.alive and not any(e in god.effects for e in {"zeus_stun","tisi_freeze_timer"})]
    else:
        """Get all alive gods from a team."""
        return [god for god in team if god.alive]

def get_dead(team):
    """Get all dead gods from a team."""
    return [god for god in team if not god.alive]

def delete_effect(team, effect_name):
    """Delete a specific effect from all gods in a team."""
    for god in team:
        if effect_name in god.effects:
            effect = god.effects[effect_name]
            effect.duration = 0

            # Handle special effect removals
            if effect_name == "athena_more_max_hp":
                god.max_hp -= effect.value
            elif effect_name == "cerebus_more_max_hp_per_visible_ally":
                # Find cerebus and reduce its max HP
                for cerebus in team:
                    if cerebus.name == "cerebus":
                        cerebus.max_hp -= effect.value
                        break
        
        # Ensure HP doesn't exceed max HP
        if god.max_hp < god.hp:
            god.hp = god.max_hp

def action_befor_delete_effect(attack_team, defend_team):
    """Handle effects before they are deleted when gods die."""
    for god in attack_team:
        if god.hp < 1 and god.alive:
            # Remove effects when gods die
            if god.name == "poseidon":
                delete_effect(attack_team, "posi_shield")
            elif god.name == "ares":
                delete_effect(attack_team, "ares_do_more_dmg")
            elif god.name == "athena":
                delete_effect(attack_team, "athena_more_max_hp")
            elif god.name == "cerebus":
                delete_effect(attack_team, "cerebus_more_max_hp_per_visible_ally")

def action_befor_die(defend_team, attack_team):
    """Handle actions before gods die."""
    # Process death effects for attacking team
    for god in attack_team:
        if god.hp < 1 and god.alive:
            god.alive = False
            
            # Handle death abilities
            if god.name == "hera":
                god.ability({
                    "ennemy_team": get_alive(defend_team),
                    "self": god
                })
    
    # Handle Charon's protective effect and death processing for defending team
    for god in defend_team:
        if "charon_invisible_duration" in god.effects:
            # Charon's protection restores HP
            god.hp = god.effects["charon_invisible_duration"].value
        
        if god.hp < 1 and god.alive:
            god.alive = False
            
            # Handle death abilities for defending team
            if god.name == "hera":
                god.ability({
                    "ennemy_team": get_alive(attack_team),
                    "self": god
                })

def reset_god_to_default(god_name):
    """Reset a god to its default state."""
    if god_name in gods:
        original_god = gods[god_name]
        original_god.hp = original_god.max_hp
        original_god.visible = False
        original_god.alive = True
        original_god.effects = {}
        return original_god
    return None
