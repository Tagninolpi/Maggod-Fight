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
    CEREBUS_MORE_MAX_HP = "cerebus_more_max_hp_per_visible_ally"
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

    def __str__(self):
        """String representation of the effect."""
        return f"Effect(value={self.value}, duration={self.duration})"

class God:
    """Represents a god in the game."""
    
    def __init__(self, name: str, hp: int, dmg: int, ability_func):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.dmg = dmg
        self.ability = ability_func
        self.effects = {}
        self.visible = False
        self.alive = True

    def add_effect(self, effect_name: str, value: int, duration: int):
        """Add an effect to this god."""
        if effect_name not in self.effects:
            self.effects[effect_name] = []
        self.effects[effect_name].append(Effect(value, duration + 1))

    def update_effects(self):
        """Update all effects, removing expired ones."""
        for name in list(self.effects.keys()):
            updated_effects = []
            for effect in self.effects[name]:
                effect.update()
                if not effect.is_expired():
                    updated_effects.append(effect)
            
            if updated_effects:
                self.effects[name] = updated_effects
            else:
                del self.effects[name]

    def get_dmg(self, value: int):
        """Apply damage to this god, accounting for shields and damage boosts."""
        original_value = value
        
        # Apply damage boosts to incoming damage
        for dmg_boost in ["alecto_get_more_dmg"]:
            if dmg_boost in self.effects:
                for effect in self.effects[dmg_boost]:
                    value += effect.value

        # Apply shields
        for shield_type in ["posi_shield", "hep_shield", "hades_uw_shield"]:
            if shield_type in self.effects:
                for shield in self.effects[shield_type]:
                    if value <= 0:
                        return  # All damage blocked
                    
                    if shield.value >= value:
                        shield.value -= value
                        return  # All damage absorbed
                    else:
                        value -= shield.value
                        shield.value = 0
        
        # Apply remaining damage
        self.hp -= value
        
        # Ensure HP doesn't go below 0
        if self.hp < 0:
            self.hp = 0

    def do_damage(self):
        """Calculate and return damage output."""
        dmg = self.dmg
        
        # Apply damage boosts
        if "ares_do_more_dmg" in self.effects:
            for effect in self.effects["ares_do_more_dmg"]:
                dmg += effect.value
        
        if "hades_ow_do_more_dmg" in self.effects:
            for effect in self.effects["hades_ow_do_more_dmg"]:
                dmg += effect.value
        
        # Apply damage reductions
        if "mega_do_less_dmg" in self.effects:
            for effect in self.effects["mega_do_less_dmg"]:
                dmg -= effect.value
        
        # Make god visible when attacking
        self.visible = True
        
        return max(0, dmg)  # Prevent negative damage

    def __str__(self):
        """String representation of the god."""
        status = "💀" if not self.alive else "👁️" if self.visible else "👻"
        return f"{status} {self.name} ({self.hp}/{self.max_hp} HP, {self.dmg} DMG)"

    def __repr__(self):
        """Detailed representation for debugging."""
        return f"God(name='{self.name}', hp={self.hp}/{self.max_hp}, dmg={self.dmg}, visible={self.visible}, alive={self.alive})"
