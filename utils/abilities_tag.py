from utils.gameplay_tag import God, Effect, EffectType
import random as r
import math
 
def poseidon(kwargs):
    """Poseidon's shield ability - Provides protective shields to allies."""
    visible_gods = kwargs.get("visible_gods", [])
    alive_ally = kwargs.get("ally_team")
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    
    if attacking_with_hermes:
        # Weaker shields when used with Hermes
        for god in visible_gods:
            god.add_effect("posi_shield", value=2, duration=1)
    else:
        # Strong permanent shield if no shields exist
        
        if not any("posi_shield" in god.effects for god in alive_ally):
            eligible = [g for g in visible_gods if g.name.lower() != "poseidon" and "posi_shield" not in g.effects]
            if eligible:
                target = r.choice(eligible)
                target.add_effect("posi_shield", value=5, duration=100)
    return ""
    

def hephaestus(kwargs):
    """Hephaestus's forge shields - Provides temporary shields to all visible allies."""
    visible_gods = kwargs["visible_gods"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 1 if attacking_with_hermes else 2
    duration = 1 if attacking_with_hermes else 2
    msg = f"🛡️ Hephaestus gives {value} HP {duration}-turn shield to:\n ✨gods : "
    for god in visible_gods:
        god.add_effect("hep_shield", value=value, duration=duration)
        msg += f",{god.name.capitalize()} "
    return msg
 
def aphrodite(kwargs):
    """Aphrodite's charm - Damages visible enemies or charms hidden ones."""
    target = kwargs["target"]
    self = kwargs["self"]
    msg = "Aphrodite "
    if target.visible:
        # Direct damage if target is visible
        target.hp -= 1
        self.heal(1)
        msg += f"does 1 dmg to {target.name.capitalize()} and heal herself by 1"
    else:
        msg += f"gives charm 💘 to {target.name.capitalize()} for 3 turns"
        target.add_effect("aphro_charm", value=0, duration=3) #under charm heal opponent by 1
    return msg

def ares(kwargs):
    """Ares's battle fury - Provides permanent damage boosts to allies."""
    visible_gods = kwargs["visible_gods"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    if attacking_with_hermes:
        # Temporary boost when used with Hermes
        for god in visible_gods:
            god.add_effect("ares_do_more_dmg", value=1, duration=1)
    else:
        # Permanent boost if not already active
        for god in visible_gods:
            god.add_effect("ares_do_more_dmg", value=1, duration=100)
    return ""

def hera(kwargs):
    """Hera's death curse - Damages all enemies when she dies."""
    if not kwargs["self"].alive:
        msg = "Hera died, she does 3 dmg to : "
        for god in kwargs["visible_ennemy_team"]:
            god.hp -= 3
            msg += f"{god.name.capitalize()}, "
        return msg
    return ""

def zeus(kwargs):
    """Zeus's lightning - Stuns target and damages all visible allies."""
    self = kwargs["self"]
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    visible_gods = kwargs["visible_gods"]
    alive_ennemy = kwargs["ennemy_team"]
    duration = 2 if attacking_with_hermes else 3
    msg = "Zeus "
    if len(alive_ennemy) > 2:
        target.add_effect("zeus_stun", value=0, duration=duration)
        msg += f"stuns 💫 {target.name.capitalize()} for {duration} turns,"
            # Lightning damages all visible allies
        msg += "and does 1 dmg (friendly dmg) to ✨gods : "
        for god in visible_gods:
            god.hp -= 1
            msg += f"{god.name.capitalize()}, "
    else:
        msg += "takes 2 dmg and does 2 dmg to ✨gods : "
        for god in alive_ennemy:
            god.hp -= 2
            msg += f"{god.name.capitalize()}, "
            self.hp -= 1 
    return msg


def athena(kwargs):
    """Athena's wisdom - Increases max HP of visible allies."""
    visible_gods = kwargs["visible_gods"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    if attacking_with_hermes:
        # Temporary HP boost when used with Hermes
        for god in visible_gods:
            if "athena_more_max_hp" not in god.effects:
                god.add_effect("athena_more_max_hp", value=1, duration=1)
                god.max_hp += 1
                god.hp += 1
    else:
        # Permanent HP boost if not already active
        for god in visible_gods:
            if "athena_more_max_hp" not in god.effects:
                god.add_effect("athena_more_max_hp", value=2, duration=100)
                god.max_hp += 2
                god.hp += 2
    return ""

def apollo(kwargs):
    """Apollo's healing light - Heals self and all allies."""
    ally_team = kwargs["ally_team"]
    self = kwargs["self"]
    msg = "Apollo heals by 1 hp ✨gods : "
    # Heal self
    self.heal(1)
    msg += "Apollo, "
    
    # Heal all allies
    for god in ally_team:
        god.heal(1)
        msg += f"{god.name.capitalize()}, "
    return msg

def artemis(kwargs):
    """Artemis's hunting arrows - Damages all enemies."""
    ennemy_team = kwargs["visible_ennemy_team"]
    msg = "Artemis does 1 dmg to ✨gods : "
    for god in ennemy_team:
        god.hp -= 1
        msg += f"{god.name.capitalize()}, "
    return msg

def hermes(kwargs):
    """Hermes's speed - Allows other gods to attack multiple times."""
    target = kwargs["target"]
    self = kwargs["self"]
    attacker_1 = kwargs.get("attacker_1")
    attacker_2 = kwargs.get("attacker_2")
    msg = "attaking with Hermes :\n"
    if attacker_1:
        if attacker_1.check_abillity():
            msg += attacker_1.ability({
                **kwargs,
                "attacking_with_hermes": True,
                "self": attacker_1
                })
        dmg = attacker_1.do_damage()
        msg+= f"\n{attacker_1.name.capitalize()} does {dmg} dmg to {target.name.capitalize()}\n"
        target.get_dmg(value=dmg)
    
    if attacker_2:
        if attacker_2.check_abillity():
            msg += attacker_2.ability({
                **kwargs,
                "attacking_with_hermes": True,
                "self": attacker_2
            })
        dmg = attacker_2.do_damage()
        msg+= f"\n{attacker_2.name.capitalize()} does {dmg} dmg to {target.name.capitalize()}"
        target.get_dmg(value=dmg)
    return msg


def hades_ow(kwargs):
    """Hades (Overworld) - Gains power from dead allies."""
    if not kwargs.get("attacking_with_hermes", False):
        dead_ally_nb = len(kwargs["dead_ally"])
        target = kwargs["target"]
        self = kwargs["self"]
        visible_gods = kwargs["visible_gods"]
        dmg = math.floor(0.5 + dead_ally_nb/2)
        msg = f"Hades_ow gives +{dmg}💥 dmg boost for 2 turns to ✨gods : "
        for god in visible_gods:
            god.add_effect("hades_ow_do_more_dmg", value= dmg, duration=2)
            msg += f"{god.name.capitalize()}, "
        return msg
    return ""
 
def thanatos(kwargs):
    """Thanatos's death touch - 50% chance to instantly kill target."""
    target = kwargs["target"]
    if r.randint(0, 1):
        target.hp = 0
        self = kwargs["self"]
        self.hp -= 5  # High cost for instant kill
        self.reload = self.reload_max
        return (f"Thanatos instakills {target.name.capitalize()}, but takes 5 dmg.")
        
    else:
        return(f"Thanatos failed to instakill {target.name.capitalize()}")
 
def cerberus(kwargs):
    """Cerberus's guard - Gains HP for each visible ally."""
    target = kwargs["target"]
    self = kwargs["self"]
    if not kwargs.get("attacking_with_hermes", False):
        msg = f"cerberus gives attract⛑️ to {target.name.capitalize()}, but looses 1 hp and gives it to {target.name.capitalize()}"
        target.add_effect("cerberus_more_max_hp_per_visible_ally", value=1, duration=2)
        self.hp -= 1
        target.heal(1)
        return msg
    return ""

def charon(kwargs):
    """Charon's protection - Protects allies and removes debuffs."""
    if not kwargs.get("attacking_with_hermes", False):
        target = kwargs["target"]
        heal = 2-len(kwargs["dead_ally"])
        kwargs["self"].heal(heal)
        msg = f"Charon protect 🧿 {target.name.capitalize()} from ennemy base dmg for 2 turn and remove all negative effects from all visible gods,"
        if heal > 0:
            msg += f"and gains {heal} hp"
        elif heal < 0:
            msg += f"but losses {heal} hp"
        target.add_effect("charon_invisible_duration", value=target.hp, duration=2)
        bad_effects = ["aphro_charm", "zeus_stun", "tisi_freeze_timer","alecto_get_more_dmg", "mega_do_less_dmg"]
        # Remove negative effects from visible gods
        for god in kwargs["visible_gods"]:
            for effect in bad_effects:
                if effect in god.effects:
                    del god.effects[effect]
        return msg
    return ""

def persephone(kwargs):
    """Persephone's revival - Revives dead allies or heals living ones."""
    if not kwargs.get("attacking_with_hermes", False):
        target = kwargs["target"]
        
        if not target.alive:
            # 50% chance to revive dead allies
            if r.randint(0, 1):
                target.alive = True
                target.hp = target.max_hp
                kwargs["self"].hp -= 3
                msg = f"Persephone revives {target.name.capitalize()} to max hp but losses 3 hp"
            else:
                msg = "Persephone revive failed!!!"
        else:
            # Heal living allies
            target.heal(2)
            msg = f"Persephone healed {target.name.capitalize()} by 2 hp"
        return msg

def hades_uw(kwargs):
    """Hades (Underworld) - Provides shields based on dead allies."""
    if not kwargs.get("attacking_with_hermes", False):
        dead_ally_nb = len(kwargs["dead_ally"])
        visible_gods = kwargs["visible_gods"]
        duration = 1 + math.floor((4 - dead_ally_nb) / 2)
        msg = f"Hades_uw gives {dead_ally_nb}☠️ shield for {duration} turn to ✨gods : "
        for god in visible_gods:
            msg += f"{god.name.capitalize()}, "
            god.add_effect("hades_uw_shield", value=dead_ally_nb,duration = duration)
        return msg
    return ""

def tisiphone(kwargs):
    """Tisiphone's fury - Freezes enemies with a chance."""
    target = kwargs["target"]
    self = kwargs["self"]
    if len(kwargs["ennemy_team"]) > 2 and len(kwargs["ally_team"]) > 2:
        target.add_effect("tisi_freeze_timer", value=1, duration=2)
        self.add_effect("tisi_freeze_timer", value=1, duration=2)
        msg = f"Tisiphone froze ❄️ {target.name.capitalize()} and herself for 2 turns"
    else:
        if self.hp == self.max_hp:
            target.hp -= 2
            msg = f"Tisiphone does 2 dmg to {target.name.capitalize()}"
        else: 
            self.hp += 1
            msg = "Tisiphone heals herself by 1 hp"
    return msg

def alecto(kwargs):
    """Alecto's curse - Makes target take more damage."""
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 2
    duration = 2 if attacking_with_hermes else 3
    msg = f"Alecto gives {target.name.capitalize()} take more dmg 💢 for {duration} turns"
    target.add_effect("alecto_get_more_dmg", value=value, duration=duration)
    return msg

def megaera(kwargs):
    """Megaera's weakness - Makes target deal less damage."""
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 4
    duration = 1 if attacking_with_hermes else 2
    msg = f"Megaera gives {target.name.capitalize()} dmg reduction 💚 for {duration} turns"
    target.add_effect("mega_do_less_dmg", value=value, duration=duration)
    return msg

def hecate(kwargs):
    """Hecate's magic - Makes self and target invisible."""
    from utils.game_test_on_discord import delete_passive_effect_when_hiding
    if not kwargs.get("attacking_with_hermes", False):
        target = kwargs["target"]
        self = kwargs["self"]
        self.heal(1)
        target.heal(1)
        msg = f"Hacate heals herself and {target.name.capitalize()} by 1 hp\n"
        delete_passive_effect_when_hiding(kwargs["visible_gods"],target)
        target.visible = False
        if target.name == "hecate":
            msg += "Hecate goes into hiding"
        else:
            msg += f"Hecate forces {target.name.capitalize()} into hiding"
        return msg
    return ""
