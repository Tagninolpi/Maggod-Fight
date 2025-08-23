import random

bot_configs = {
    "random": {},
    "best_hp_dmg": {
        "hp": 0.3,
        "dmg": 1
    },
    "worst_hp_dmg": {
        "hp": -0.3,
        "dmg": -1
    }
}

class BotClass:
    def __init__(self, name: str):
        self.name = name
        self.config = bot_configs[name]
        self.select_team_gods = {}

    def choose_god(self, select):
        # initialize scores
        self.create_att_def_valuedict(select)

        # random bot just picks one
        if self.name == "random":
            return random.choice(select)

        # score-based bots
        for atr, multi in self.config.items():
            self.add_score(atr, multi)

        return max(self.select_team_gods, key=self.select_team_gods.get)

    def create_att_def_valuedict(self, select):
        for g in select:
            self.select_team_gods[g] = 0

    def add_score(self, atr, multi):
        for god in self.select_team_gods:
            value = getattr(god, atr, 0)
            self.select_team_gods[god] += value * multi
