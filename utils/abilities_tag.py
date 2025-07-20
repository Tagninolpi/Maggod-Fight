from utils.gameplay_tag import God, Effect, EffectType
import random as r
import math
 
def poseidon(kwargs):
    """Poseidon's shield ability - Provides protective shields to allies."""
    visible_gods = kwargs.get("visible_gods", [])
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    
    if attacking_with_hermes:
        # Weaker shields when used with Hermes
        for god in visible_gods:
            god.add_effect("posi_shield", value=2, duration=1)
    else:
        # Strong permanent shield if no shields exist
        if not any("posi_shield" in god.effects for god in visible_gods):
            target = kwargs["target"]
            if target.name != "poseidon":
                target.add_effect("posi_shield", value=5, duration=100)

def hephaestus(kwargs):
    """Hephaestus's forge shields - Provides temporary shields to all visible allies."""
    visible_gods = kwargs["visible_gods"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 2 if attacking_with_hermes else 3
    duration = 1 if attacking_with_hermes else 2
    
    for god in visible_gods:
        god.add_effect("hep_shield", value=value, duration=duration)

def aphrodite(kwargs):
    """Aphrodite's charm - Damages visible enemies or charms hidden ones."""
    self = kwargs["self"]
    target = kwargs["target"]
    
    if kwargs.get("attacking_with_hermes", False) or target.visible:
        # Direct damage if target is visible
        target.hp -= 2
    else:
        # Charm hidden enemies at a cost
        self.hp -= 1
        target.add_effect("aphro_charm", value=0, duration=2)

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

def hera(kwargs):
    """Hera's death curse - Damages all enemies when she dies."""
    if not kwargs["self"].alive:
        for god in kwargs["ennemy_team"]:
            god.hp -= 3

def zeus(kwargs):
    """Zeus's lightning - Stuns target and damages all visible allies."""
    self = kwargs["self"]
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    visible_gods = kwargs["visible_gods"]
    
    duration = 1 if attacking_with_hermes else 2
    self.hp -= 2  # Zeus damages himself
    target.add_effect("zeus_stun", value=0, duration=duration)
    
    # Lightning damages all visible allies
    for god in visible_gods:
        god.hp -= 1

def athena(kwargs):
    """Athena's wisdom - Increases max HP of visible allies."""
    visible_gods = kwargs["visible_gods"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    
    if attacking_with_hermes:
        # Temporary HP boost when used with Hermes
        for god in visible_gods:
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

def apollo(kwargs):
    """Apollo's healing light - Heals self and all allies."""
    ally_team = kwargs["ally_team"]
    self = kwargs["self"]
    
    # Heal self
    if self.hp + 1 > self.max_hp:
        self.hp = self.max_hp
    else:
        self.hp += 1
    
    # Heal all allies
    for god in ally_team:
        if god.hp + 1 > god.max_hp:
            god.hp = god.max_hp
        else:
            god.hp += 1

def artemis(kwargs):
    """Artemis's hunting arrows - Damages all enemies."""
    ennemy_team = kwargs["ennemy_team"]
    for god in ennemy_team:
        god.hp -= 1

def hermes(kwargs):
    """Hermes's speed - Allows other gods to attack multiple times."""
    target = kwargs["target"]
    attacker_1 = kwargs.get("attacker_1")
    attacker_2 = kwargs.get("attacker_2")
    
    if attacker_1:
        attacker_1.ability({
            **kwargs,
            "attacking_with_hermes": True,
            "self": attacker_1
        })
        if attacker_1.name != "hades_ow":
            target.get_dmg(value=attacker_1.do_damage())
    
    if attacker_2:
        attacker_2.ability({
            **kwargs,
            "attacking_with_hermes": True,
            "self": attacker_2
        })
        if attacker_2.name != "hades_ow":
            target.get_dmg(value=attacker_2.do_damage())

def hades_ow(kwargs):
    """Hades (Overworld) - Gains power from dead allies."""
    if not kwargs.get("attacking_with_hermes", False):
        dead_ally_nb = len(kwargs["dead_ally"])
        target = kwargs["target"]
        self = kwargs["self"]
        
        self.add_effect("hades_ow_do_more_dmg", value=dead_ally_nb, duration=1)
        target.get_dmg(value=self.do_damage() + dead_ally_nb)

def thanatos(kwargs):
    """Thanatos's death touch - 50% chance to instantly kill target."""
    if r.randint(0, 1):
        target = kwargs["target"]
        target.hp = 0
        self = kwargs["self"]
        self.hp -= 5  # High cost for instant kill

def cerebus(kwargs):
    """Cerberus's guard - Gains HP for each visible ally."""
    visible_gods = kwargs["visible_gods"]
    if not kwargs.get("attacking_with_hermes", False):
        for god in visible_gods:
            if "cerebus_more_max_hp_per_visible_ally" not in god.effects:
                self = kwargs["self"]
                self.add_effect("cerebus_more_max_hp_per_visible_ally", value=1, duration=100)
                self.max_hp += 1
                self.hp += 1

def charon(kwargs):
    """Charon's protection - Protects allies and removes debuffs."""
    if not kwargs.get("attacking_with_hermes", False):
        target = kwargs["target"]
        kwargs["self"].hp -= 2
        target.add_effect("charon_invisible_duration", value=target.hp, duration=2)
        
        # Remove negative effects from visible gods
        for god in kwargs["visible_gods"]:
            for bad_effect in ["aphro_charm", "zeus_stun", "tisi_freeze_timer", 
                             "alecto_get_more_dmg", "mega_do_less_dmg"]:
                if bad_effect in god.effects:
                    del god.effects[bad_effect]

def persephone(kwargs):
    """Persephone's revival - Revives dead allies or heals living ones."""
    if not kwargs.get("attacking_with_hermes", False):
        target = kwargs["target"]
        
        if not target.alive:
            # 50% chance to revive dead allies
            if r.randint(0, 1):
                target.alive = True
                target.hp = target.max_hp
                kwargs["self"].hp -= 2
        else:
            # Heal living allies
            target.hp += 2
            if target.hp > target.max_hp:
                target.hp = target.max_hp

def hades_uw(kwargs):
    """Hades (Underworld) - Provides shields based on dead allies."""
    if not kwargs.get("attacking_with_hermes", False):
        dead_ally_nb = len(kwargs["dead_ally"])
        visible_gods = kwargs["visible_gods"]
        
        for god in visible_gods:
            god.add_effect("hades_uw_shield", value=dead_ally_nb, 
                          duration=1 + math.floor((4 - dead_ally_nb) / 2))
        
        kwargs["self"].hp -= math.floor(dead_ally_nb / 2)

def tisiphone(kwargs):
    """Tisiphone's fury - Freezes enemies with a chance."""
    ennemy_team = kwargs["ennemy_team"]
    self = kwargs["self"]
    
    if kwargs.get("attacking_with_hermes", False):
        # Random freeze when used with Hermes
        for god in ennemy_team:
            if r.randint(0, 1) == 0:
                god.add_effect("tisi_freeze_timer", value=1, duration=1)
        self.add_effect("tisi_freeze_timer", value=1, duration=2)

def alecto(kwargs):
    """Alecto's curse - Makes target take more damage."""
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 2
    duration = 3 if attacking_with_hermes else 2
    
    target.add_effect("alecto_get_more_dmg", value=value, duration=duration)

def megaera(kwargs):
    """Megaera's weakness - Makes target deal less damage."""
    target = kwargs["target"]
    attacking_with_hermes = kwargs.get("attacking_with_hermes", False)
    value = 2
    duration = 3 if attacking_with_hermes else 2
    
    target.add_effect("mega_do_less_dmg", value=value, duration=duration)

def hecate(kwargs):
    """Hecate's magic - Makes self and target invisible."""
    kwargs["self"].visible = False
    if not kwargs.get("attacking_with_hermes", False):
        kwargs["target"].visible = False
