import random
from utils.gameplay_tag import God

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

bot_choose_configs = {
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
        # bot identity
        self.config = bot_configs[name]
        self.choose_config = bot_choose_configs[name]
        # selectable gods (value)
        self.select_team_gods = {}
        # needed ? 
        self.opp_team_dmg = {}
        self.my_team_dmg = {}
        self.opp_team_dmg_recived = {}
        self.my_team_dmg_recived = {}

### init functions
# populate dict (kwargs) with names in list and set to 0
    def init_dicts(self, list,kwargs):
        for g in list:
            kwargs[g] = 0

### Helper functions
# add score to a team based on attribut value and mult
    def add_score(self, atr, multi):
        for god in self.select_team_gods:
            value = getattr(god, atr, 0)
            self.select_team_gods[god] += value * multi

# set value of key in dict to true dmg input and output
    def set_true_dmg_done(self,team,kwargs):
        for g in team:
            kwargs[g] = g.do_damage()
    def set_true_dmg_received(self,team,kwargs,init_dmg):
        for g in team:
            kwargs[g] = g.get_dmg(init_dmg,False)

# get the biggest/smalest value and its key from any dict
    def get_biggest_value(self,dict):
        key = max(dict, key=dict.get)
        value = dict[key]
        return key, value
    def get_smallest_value(self,dict):
        key = min(dict, key=dict.get)
        value = dict[key]
        return key, value



### Bot functions
#can i instakill?
#get my biggest dmg, see the true dmg i can do, see if true dmg is bigger than hp left


### Main function
    def choose_god(self, select,pre_game_choose = True,opp_team = None,my_team = None):
        # initialize scores
        self.init_dicts(select,self.select_team_gods)
        #self.set_true_dmg_done(select,self.my_team_dmg)
        #self.set_true_dmg_done(opp_team,self.opp_team_dmg)
        #self.set_true_dmg_received(select,self.my_team_dmg,9)
        #self.set_true_dmg_received(opp_team,self.opp_team_dmg,9)


        # random bot just picks one
        if self.name == "random":
            return random.choice(select)
        if pre_game_choose:
            # score-based bots
            for atr, multi in self.choose_config.items():
                self.add_score(atr, multi)
        else:
                    # score-based bots
            for atr, multi in self.config.items():
                self.add_score(atr, multi)

        return max(self.select_team_gods, key=self.select_team_gods.get)

