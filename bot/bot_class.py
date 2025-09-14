import random
import math
from utils.gameplay_tag import God
from utils.game_test_on_discord import get_alive,get_dead,get_visible
import logging
logger = logging.getLogger(__name__)
# -------------------- BOT CONFIGS --------------------
bot_configs = {
    "random": {},
    "worst_bot": {"hp": -1, "dmg": -1,"reload":-0.3},
    "best_bot": {"hp": 0.3, "dmg": 1,"reload":0.3},
    "bot_overloard":{"hp": 0.3, "dmg": 1,"ability":1}
}

bot_choose_configs = {
    "random": {},
    "worst_bot": {"hp": -0.3, "dmg": -1,"reload":-0.3},
    "best_bot": {"hp": 0.3, "dmg": 1,"reload":0.3},
    "bot_overloard":{"hp": 0.3, "dmg": 1,"ability":1}
}

# -------------------- GOD ABILLITY --------------------
def poseidon(ally,ennemy,visible,reload):
    if not(visible):
        return 5/len(get_visible(ally))
    else:
        return 0 
def athena(ally,ennemy,visible,reload):
    if not(visible):
        return 4 * len(get_visible(ally)) + 2
    else:
        return 0 
def charon(ally,ennemy,visible,reload):
    if reload<1:
        return 6/len(get_visible(ally))+sum(1 for god in ally for e in god.effects if e in ["aphro_charm", "zeus_stun", "tisi_freeze_timer","alecto_get_more_dmg", "mega_do_less_dmg"])
    else:
        return 0
def megaera(ally,ennemy,visible,reload):
    if reload<1:
        return 8/len(get_alive(ennemy))
    else:
        return 0  
def tisiphone(ally,ennemy,visible,reload):
    if reload<1:
        ally_vis = len(get_alive(ally))
        if ally_vis>2 and len(get_alive(ennemy))>2:
            return 3
        if not(visible):
            return 2
        else:
            return 1
    else:
        return 0 
def zeus(ally,ennemy,visible,reload):
    if reload<1:
        if len(get_alive(ennemy))>2:
            return 6/(len(get_visible(ally))+1)
        else:
            return 2
    else:
        return 0
def cerberus(ally,ennemy,visible,reload):
    if reload<1:
        return 6/(5-len(get_visible(ally)))
    else:
        return 0 
def hera(ally,ennemy,visible,reload):
    return 0
def aphrodite(ally,ennemy,visible,reload):
    if reload<1:
        return 2
    else:
        return 0
def artemis(ally,ennemy,visible,reload):
    if reload<1:
        return len(get_visible(ennemy))
    else:
        return 0   
def hades_ow(ally,ennemy,visible,reload):
    if reload<1:
        return math.floor(0.5 + len(get_dead(ally))/2)*(len(get_visible(ally))+1)
    else:
        return 0  
def alecto(ally,ennemy,visible,reload):
    if reload<1:
        return 4
    else:
        return 0 
def hecate(ally,ennemy,visible,reload):
    if reload<1:
        return 4
    else:
        return 0 
def hephaestus(ally,ennemy,visible,reload):
    if reload<1:
        return 2*len(get_visible(ally))+2
    else:
        return 0
def ares(ally,ennemy,visible,reload):
    if not(visible):
        return len(get_visible(ally))+1
    else:
        return 0
def persephone(ally,ennemy,visible,reload):
    if reload<1:
        return 3
    else:
        return 0
def thanatos(ally,ennemy,visible,reload):
    if reload<1:
        return 4
    else:
        return 0
def apollo(ally,ennemy,visible,reload):
    if reload<1:
        return len(get_visible(ally))+1
    else:
        return 0
def hermes(ally,ennemy,visible,reload):
    if reload<1:
        al_lng = len(get_visible(ally))
        for g in ally:
            if g.name =="hermes" and g.visible:
                al_lng -=1
        if al_lng==1:
            return 4
        if al_lng>1:
            return 8
        else:
            return 0
    else:
        return 0
def hades_uw(ally,ennemy,visible,reload):
    if reload<1:
        return len(get_dead(ally))*len(get_visible(ally))
    else:
        return 0


GOD_ABILITIES = {
    "poseidon": poseidon,
    "athena": athena,
    "charon": charon,
    "megaera": megaera,
    "tisiphone": tisiphone,
    "zeus": zeus,
    "cerberus": cerberus,
    "hera": hera,
    "aphrodite": aphrodite,
    "artemis": artemis,
    "hades_ow": hades_ow,
    "alecto": alecto,
    "hecate": hecate,
    "hephaestus": hephaestus,
    "ares": ares,
    "persephone": persephone,
    "thanatos": thanatos,
    "apollo": apollo,
    "hermes": hermes,
    "hades_uw": hades_uw,
}
# -------------------- TURN CONTEXT --------------------
class TurnContext:
    def __init__(self, select=None, my_team=None, opp_team=None, action_text=None, attack_cerbs: bool = False):
        self.action_text = action_text
        self.attack_cerbs = attack_cerbs
        if action_text == "attack":
            self.my_team = opp_team or []
            self.opp_team = my_team or []
            self.select = select or []
        else:
            self.my_team = my_team or []
            self.opp_team = opp_team or []
            self.select = select or []

# -------------------- BOT CLASS --------------------
class BotClass:
    def __init__(self, name: str):
        self.name = name
        self.config = bot_configs[name]
        self.choose_config = bot_choose_configs[name]
        self.true_dmg_list = []
        self.ctx: TurnContext | None = None

    def set_ctx(self, ctx: TurnContext):
        self.ctx = ctx

### Helper functions :

    def filter_by_reload(self, gods):
        """Return gods based on reload and the reload multiplier in config."""
        if not gods:
            return []
        reload_multiplier = self.choose_config.get("reload", None)
        # If reload multiplier exists and is negative, pick gods with reload > 0
        if reload_multiplier is not None and reload_multiplier < 0:
            with_reload = [g for g in gods if g.reload > 0]
            return with_reload if with_reload else gods
        # Normal behavior: pick gods ready to act (reload <= 0)
        ready = [g for g in gods if g.reload <= 0]
        return ready if ready else gods
        # all have timer, return original list
    
    def max_damage_god(self):
        # list true dmg of all
        dmg_values = {g: g.do_damage() for g in self.ctx.select}
        # set to bot config ammount
        dmg_multiplier = self.choose_config.get("dmg", None)

        # add ability values if configured
        ability_mult = self.choose_config.get("ability", None)
        if ability_mult is not None:
            for god in self.ctx.my_team:
                if god in dmg_values and god.name in GOD_ABILITIES:
                    dmg_values[god] += (
                        GOD_ABILITIES[god.name](
                            self.ctx.my_team, 
                            self.ctx.opp_team, 
                            god.visible, 
                            god.reload
                        ) * ability_mult
                    )
        # bot config choose max or min
        if dmg_multiplier is not None and dmg_multiplier < 0:
            target_value = min(dmg_values.values())
        else:
            target_value = max(dmg_values.values())
        # add all if tie
        best_gods = [g for g, dmg in dmg_values.items() if dmg == target_value]
        # select lowest reload
        best_gods = self.filter_by_reload(best_gods)
        chosen = random.choice(best_gods) if best_gods else None
        # list of dmg done
        self.true_dmg_list = [target_value] if target_value else []
        return chosen

    def minimize_damage_god(self):
        """
        Picks a god for 'attack' that minimizes damage taken and factors in hp lost,
        true damage, and reload multipliers from config.
        """
        if not self.ctx.select:
            return None

        scores = {}
        hp_multiplier = self.choose_config.get("hp", None)
        dmg_multiplier = self.choose_config.get("dmg", None)
        reload_multiplier = self.choose_config.get("reload", None)

        for g in self.ctx.select:
            # hp lost: assume self.true_dmg_list contains expected damage to this god
            total_received = sum([g.get_dmg(d, False) for d in self.true_dmg_list])
            hp_lost = max(g.hp - total_received, 0)  # cannot be negative

            score = 0
            if hp_multiplier is not None:
                score += hp_lost * hp_multiplier
            if dmg_multiplier is not None:
                score += g.do_damage() * dmg_multiplier
            if reload_multiplier is not None:
                reload = getattr(g, "reload", 0)
                if reload_multiplier < 0:
                    # negative multiplier: pick gods with reload > 0
                    score += (reload if reload > 0 else 0) * reload_multiplier
                else:
                    # positive multiplier: pick gods ready to act
                    score += ((10 if reload <= 0 else (10 - reload)) * reload_multiplier)
            scores[g] = score
        self.true_dmg_list.clear()
        if not scores:
            return random.choice(self.ctx.select)

        max_score = max(scores.values())
        top_gods = [g for g, score in scores.items() if score == max_score]
        return random.choice(top_gods)

    def get_score(self,gods,hp=False):
        scores = {}
        for g in gods: # calculate 
                score = 0
                if hp:
                    hp_left = g.hp - sum(g.get_dmg(d, False) for d in self.true_dmg_list)
                    score +=7-round(((hp_left*100)/g.max_hp)/14.3)
                else:
                    if "hp" in self.choose_config:
                        score += g.hp * self.choose_config["hp"]
                if "dmg" in self.choose_config:
                    score += g.do_damage() * self.choose_config["dmg"]
                if "reload" in self.choose_config:
                    reload = getattr(g, "reload", 0)
                    if reload <= 0:
                        score += 10 * self.choose_config["reload"]
                    else:
                        score += (10 - reload) * self.choose_config["reload"]

                ability_mult = self.choose_config.get("ability", None)
                if ability_mult is not None:
                    # get ability value for god and aplly it to score
                    score += (
                        GOD_ABILITIES[g.name](
                            self.ctx.my_team, 
                            self.ctx.opp_team, 
                            g.visible, 
                            g.reload
                        ) * ability_mult
                    )
                scores[g] = score
        return scores


    def instakill_god(self):
        best_gods = []
        all_gods = []
        # Check which gods can be instakilled
        for g in self.ctx.select:
            if "charon_invisible_duration" in g.effects:
                total_received = 0
            else:
                total_received = sum([g.get_dmg(d, False) for d in self.true_dmg_list])
            if g.hp <= total_received:
                best_gods.append(g)
            all_gods.append(g)
        if best_gods: # list of gods that can be instakilled
            scores = self.get_score(best_gods)
        else:
            scores = self.get_score(all_gods,hp=True)
        max_score = max(scores.values())
        top_gods = [g for g, score in scores.items() if score == max_score]
        chosen = random.choice(top_gods)
        # Clear true damage list after using it
        self.true_dmg_list.clear()

        return chosen
 

    # -------------------- MAIN BOT FUNCTION --------------------
    def choose_god(self, ctx: TurnContext):
        self.set_ctx(ctx)
        
        if getattr(ctx, "attack_cerbs", False):
            self.true_dmg_list = []
            return None
        
        if self.name == "random":
            return random.choice(ctx.select)

        # --- "attack with" logic ---
        if ctx.action_text and ctx.action_text.startswith("attack with"):
            return self.max_damage_god()

        # --- "attack" logic ---
        if ctx.action_text == "attack":
            dmg_multiplier = self.choose_config.get("dmg", None)
            # dmg *-x
            if dmg_multiplier is not None and dmg_multiplier < 0:
                return self.minimize_damage_god()
            
            god = self.instakill_god()
            if god:
                return god
            return random.choice(ctx.select)

        # --- fallback score-based system ---
        if self.choose_config:
            scores = {g: sum(getattr(g, atr, 0) * multi for atr, multi in self.choose_config.items())
                    for g in ctx.select}
            return max(scores, key=scores.get)

        return random.choice(ctx.select)
