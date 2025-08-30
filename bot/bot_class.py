import random
from utils.gameplay_tag import God
import logging
logger = logging.getLogger(__name__)
# -------------------- BOT CONFIGS --------------------
bot_configs = {
    "random": {},
    "worst_bot": {"hp": -1, "dmg": -1,"reload":-0.3},
    "best_bot": {"hp": 0.3, "dmg": 2,"reload":0.3}
}

bot_choose_configs = {
    "random": {},
    "worst_bot": {"hp": -0.3, "dmg": -1,"reload":-0.3},
    "best_bot": {"hp": 0.3, "dmg": 1,"reload":0.3}
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
        # compute dmg for all selectable gods
        dmg_values = {g: g.do_damage() for g in self.ctx.select}
        dmg_multiplier = self.choose_config.get("dmg", None)
        if dmg_values:
            if dmg_multiplier is not None and dmg_multiplier < 0:
                # pick gods with minimum damage
                target_value = min(dmg_values.values())
            else:
                # pick gods with maximum damage
                target_value = max(dmg_values.values())
            
            best_gods = [g for g, dmg in dmg_values.items() if dmg == target_value]
        else:
            best_gods = []
            target_value = 0
        # filter based on reload
        best_gods = self.filter_by_reload(best_gods)
        chosen = random.choice(best_gods) if best_gods else None
        self.true_dmg_list = [target_value] if target_value else []
        logger.info("Dmg values: %s", {g.name: g.do_damage() for g in self.ctx.select})
        logger.info("Best gods: %s", [g.name for g in best_gods])
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

    def instakill_god(self):
        best_gods = []
        scores = {}

        # Check which gods can be instakilled
        for g in self.ctx.select:
            total_received = sum([g.get_dmg(d, False) for d in self.true_dmg_list])
            if g.hp <= total_received:
                best_gods.append(g)

        if best_gods:
            # Calculate scores for instakill candidates
            for g in best_gods:
                score = 0
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
                scores[g] = score

            # Pick god(s) with the highest score
            max_score = max(scores.values())
            top_gods = [g for g, score in scores.items() if score == max_score]

            chosen = random.choice(top_gods)
        else:
            # --- NEW BEHAVIOR: no instakill possible ---
            hp_after_dmg = {
                g: g.hp - sum([g.get_dmg(d, False) for d in self.true_dmg_list])
                for g in self.ctx.select
            }
            min_hp = min(hp_after_dmg.values())
            weakest = [g for g, hp in hp_after_dmg.items() if hp == min_hp]
            chosen = random.choice(weakest)

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
            if dmg_multiplier is not None and dmg_multiplier < 0:
                # pick god using minimize_damage_god
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
