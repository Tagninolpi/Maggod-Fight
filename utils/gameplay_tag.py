from enum import Enum

class EffectType(Enum):
    """All effect names used in the game."""
    POSI_SHIELD = "posi_shield"
    HEP_SHIELD = "hep_shield"
    ARES_MORE_DMG = "ares_do_more_dmg"
    APHRO_CHARM = "aphro_charm"
    ZEUS_STUN = "zeus_stun"
    ATHENA_MORE_HP = "athena_more_max_hp"
    HADES_OW_MORE_DMG = "hades_ow_do_more_dmg"
    CERBERUS_MORE_MAX_HP = "cerberus_more_max_hp_per_visible_ally"
    CHARON_INVISIBLE = "charon_invisible_duration"
    HADES_UW_MORE_HP = "hades_uw_shield"
    TISI_FREEZE = "tisi_freeze_timer"
    ALECTO_MORE_DMG = "alecto_get_more_dmg"
    MEGA_LESS_DMG = "mega_do_less_dmg"

class Effect:
    """Represents a temporary effect on a god."""
    
    def __init__(self, value: int, duration: int):
        self.value = value
        self.duration = duration

    def update(self):
        """Decrease duration by 1."""
        self.duration -= 1

    def is_expired(self):
        """Check if the effect has expired."""
        return self.duration <= 0
    
#used ?
    def __str__(self):
        """String representation of the effect."""
        return f"Effect(value={self.value}, duration={self.duration})"

class God:
    """Represents a god in the game."""
    
    def __init__(self, name: str, hp: int, dmg: int, ability_func,reload_time):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.ability = ability_func
        self.effects = {}
        self.visible = False
        self.alive = True
        self.reload = 0
        self.reload_max = reload_time

    def add_effect(self, effect_name: str, value: int, duration: int):
        """Add an effect only if it doesn't already exist."""
        if effect_name not in self.effects:
            self.effects[effect_name] = Effect(value, duration * 2)


    def update_effects(self):
        """Update all effects, removing expired ones."""
        self.reload -= 1
        to_remove = []
        for name, effect in self.effects.items():
            effect.update()
            if effect.is_expired():
                to_remove.append(name)
        for name in to_remove:
            del self.effects[name]
    
    def check_abillity(self):
        if self.reload <= 0:
            if not(self.name == "thanatos"):
                self.reload = self.reload_max * 2 + 1
            return True
        else:
            return False

    def heal(self,value):
        if self.hp + value > self.max_hp:
            self.hp = self.max_hp
        else:
            self.hp += value

    def get_dmg(self, value: int):
        """Apply damage to this god, prioritizing shield effects with the lowest duration left."""

        # Apply damage boosts to incoming damage
        if "alecto_get_more_dmg" in self.effects:
            value += self.effects["alecto_get_more_dmg"].value

        # Gather all active shields
        shield_types = ["posi_shield", "hep_shield", "hades_uw_shield"]
        shields = [
            (shield_type, self.effects[shield_type])
            for shield_type in shield_types
            if shield_type in self.effects
        ]

        # Sort shields by duration (ascending)
        shields.sort(key=lambda pair: pair[1].duration)

        # Apply shields in that order
        for _, shield in shields:
            if value <= 0:
                return  # All damage blocked

            if shield.value >= value:
                shield.value -= value
                return  # All damage absorbed
            else:
                value -= shield.value
                shield.value = 0

        # Apply remaining damage to HP
        self.hp -= value
        if self.hp < 0:
            self.hp = 0


    def do_damage(self):
        """Calculate and return damage output."""
        dmg = self.dmg

        # Apply damage boosts
        if "ares_do_more_dmg" in self.effects:
            dmg += self.effects["ares_do_more_dmg"].value

        if "hades_ow_do_more_dmg" in self.effects:
            dmg += self.effects["hades_ow_do_more_dmg"].value

        # Apply damage reductions
        if "mega_do_less_dmg" in self.effects:
            dmg -= self.effects["mega_do_less_dmg"].value
            
        if "aphro_charm" in self.effects:
            dmg = -1

        # Make god visible when attacking
        self.visible = True

        return dmg

#used ?
    def __str__(self):
        """String representation of the god."""
        status = "💀" if not self.alive else "👁️" if self.visible else "👻"
        return f"{status} {self.name} ({self.hp}/{self.max_hp} HP, {self.dmg} DMG)"

    def __repr__(self):
        """Detailed representation for debugging."""
        return f"God(name='{self.name}', hp={self.hp}/{self.max_hp}, dmg={self.dmg}, visible={self.visible}, alive={self.alive})"
