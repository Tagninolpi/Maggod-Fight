import discord
from .create_god_tutorial_embeds import create_god_tutorial_embeds, simple_embed

# ---------------- God Functions ----------------
class GodTutorials:
    """All god tutorial functions, each returning its embed(s)."""

    def poseidon(self):
        msg1 = simple_embed("Poseidon has no ability when he attacks")
        msg2 = simple_embed("He does nothing when he is hiden👻")
        msg3 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True
        )
        msg4 = simple_embed("Poseidon gives shield🔱 to random ally when alive❤️ and visible👁️")
        msg5 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True},
                "hephaestus":{
                "visible": True,"effects": {"posi_shield": 5}
                }}
        )
        msg6 = simple_embed("When Poseidon dies💀 the shield 🔱is lost")
        msg7 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"alive": False,"hp": 0},
                "hephaestus":{
                "visible": True
                }}
        )
        msg8 = simple_embed("Poseidon shield🔱 value go down when attaked, when shield value = 0 god takes dmg")
        msg9 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True},
                "hephaestus":{
                "visible": True,"effects": {"posi_shield": 0},"hp":10},
                }
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7,msg8,msg9]

    def hephaestus(self):
        msg1 = simple_embed("Hepaestus gives a 2 turn shield🛡️ to all visible when he attacks")
        msg2 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"effects": {"hep_shield": 2}},
                "hephaestus":{
                "visible": True,"effects": {"hep_shield": 2},"reload":6},
                "ares":{
                "visible": True,"effects": {"hep_shield": 2}
                }}
        )
        msg3 = simple_embed("Hepaestus gives a 1 turn shield🛡️ to all visible👁️ when he attacks with hermes")
        msg4 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"effects": {"hep_shield": 1}},
                "hephaestus":{
                "visible": True,"effects": {"hep_shield": 1},"reload":6},
                "hermes":{
                "visible": True,"effects": {"hep_shield": 1}
                }}
        )
        msg5 = simple_embed("Hepaestus shield🛡️ value go down when attaked, when shield value = 0 god takes dmg")
        msg6 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"effects": {"hep_shield": 0},"hp":7},
                "hephaestus":{
                "visible": True,"effects": {"hep_shield": 1},"reload":6},
                "hermes":{
                "visible": True,"effects": {"hep_shield": 1},"reload":8
                }}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6]

    def aphrodite(self):
        msg1 = simple_embed("Aphrodite ability is activated when she attacks alone (visible or invisible) or with hermes")
        msg2 = simple_embed("Aphrodite can attack visible and invisible ennemy.\n When attacking invisible she gives charm💘 for 3 turns to target\n charm makes it so that when the ennemy attaks it heals by 1hp it's target (your ally maggod) ")
        msg3 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{
                "hp":5,"effects":{"aphro_charm":0}}
                }
        )
        msg4 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "aphrodite":{
                "visible": True,"reload":4}
                }
        )
        msg5 = simple_embed("When attacking with hermes or alone (visible ennemy) she gains 1 hp and does 1 additional dmg")
        return [msg1,msg2,msg3,msg4,msg5]

    def ares(self):
        msg1 = simple_embed("Ares has no ability when he attacks")
        msg2 = simple_embed("He does nothing when he is hiden👻")
        msg3 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True
        )
        msg4 = simple_embed("Ares gives dmg boost🔥 to all allies when alive❤️ and visible👁️")
        msg5 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"effects": {"ares_do_more_dmg": 1}},
                "hephaestus":{
                "visible": True,"effects": {"ares_do_more_dmg": 1}},
                "ares":{
                "visible": True,"effects": {"ares_do_more_dmg": 1}}
                }
        )
        msg6 = simple_embed("When ares dies💀 or becomes invisible👻 the dmg boost is lost")
        msg7 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True},
                "hephaestus":{
                "visible": True},
                "ares":{
                "visible": True,"alive":False,"hp": 0
                }}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7]

    def hera(self):
        msg1 = simple_embed("Hera has no ability when she attacks")
        msg2 = simple_embed("She does nothing until she dies")
        msg3 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={"hera":{"visible": True}}
        )
        msg4 = simple_embed("When Hera dies💀 she does 3 dmg to all visible ennemies")
        msg5 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{
                "hp":5,"visible":True},
                "thanotos":{
                "hp":8,"visible":True},
                "athena":{
                "hp":7,"visible":True}
                }
        )
        msg6 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "hera":{
                "alive": False,"hp":0}
                }
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6]

    def zeus(self):
        msg1 = simple_embed("Zeus can stun💫 an ennemy for 3 turn when attacking alone, but he does 1 dmg to all visible allies")
        msg2 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{
                "hp":6,"effects":{"zeus_stun":0},"visible":True},
                "thanotos":{"visible":True},
                "athena":{"visible":True}
                }
        )
        msg3 = create_god_tutorial_embeds(
            ["zeus", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "zeus":{
                "visible": True,"hp":13,"reload":4},
                "hera":{
                "visible": True,"hp":5}
                }
        )
        msg4 = simple_embed("Zeus can stun💫 an ennemy for 1 turn when attacking with hermes, but he does 1 dmg to all visible allies")
        msg5 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{
                "hp":4,"effects":{"zeus_stun":0},"visible":True},
                "thanotos":{"visible":True},
                "athena":{"visible":True}
                }
        )
        msg6 = create_god_tutorial_embeds(
            ["zeus", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "zeus":{
                "visible": True,"hp":13,"reload":4},
                "hera":{
                "visible": True,"hp":5},
                "hermes":{
                "visible": True,"hp":7,"reload":8}
                }
        )
        msg7 = simple_embed("When there are 2 or less ennemies alive he does 2 dmg to all ennemy and takes 2 dmg")
        msg8 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{
                "hp":0,"alive":False,"visible":True},
                "thanatos":{
                "hp":0,"alive":False,"visible":True},
                "athena":{
                "hp":0,"alive":False,"visible":True},
                "persephone":{"visible":True,"hp":4},
                "alecto":{"visible":True,"hp":7},
                }
        )
        msg9 = create_god_tutorial_embeds(
            ["zeus", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "zeus":{
                "visible": True,"hp":12},
                "hera":{
                "visible": True,},
                "hermes":{
                "visible": True,}
                }
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7,msg8,msg9]

    def athena(self):
        msg1 = simple_embed("Athena has no ability when she attacks")
        msg2 = simple_embed("She does nothing when she is hiden👻")
        msg3 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "athena", "ares", "hera"], success=True
        )
        msg4 = simple_embed("Athena gives hp boost📯 to all allies when alive❤️ and visible👁️")
        msg5 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "athena", "ares", "hera"], success=True,
            overrides={
                "athena":{
                "visible": True,"effects": {"athena_more_max_hp": 0},"max_hp":12,"hp":12},
                "hephaestus":{
                "visible": True,"effects": {"athena_more_max_hp": 0},"max_hp":14,"hp":14}
                }
        )
        msg6 = simple_embed("When Athena dies💀 the hp boost📯 is lost")
        msg7 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "athena", "ares", "hera"], success=True,
            overrides={
                "athena":{
                "visible": True,"alive": False,"hp": 0},
                "hephaestus":{
                "visible": True
                }}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7]

    def apollo(self):
        msg1 = simple_embed("Apollo heal him self by 2 hp and every visible ally by 1hp (can attack with hermes)")
        msg2 = create_god_tutorial_embeds(
            ["athena", "apollo", "ares", "alecto", "persephone"], success=True,
            overrides={
                "ares":{"hp":2,"visible":True},
                "apollo":{"hp":5,"visible":True},
                "alecto":{"hp":6,"visible":True},
                }
        )
        msg3 = create_god_tutorial_embeds(
            ["athena", "apollo", "ares", "alecto", "persephone"], success=True,
            overrides={
                "ares":{"hp":3,"visible":True},"reload":2,
                "apollo":{"hp":7,"visible":True},
                "alecto":{"hp":7,"visible":True},
                }
        )
        return [msg1,msg2,msg3]
    
    def artemis(self):
        msg1 = simple_embed("Artemis does 1 dmg to all visible ennemies (can attack with hermes)")
        msg2 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=False,
            overrides={
                "ares":{"hp":5,"visible":True},
                "thanatos":{"hp":10,"visible":True},
                "athena":{"hp":9,"visible":True}}
                )
        msg3 = create_god_tutorial_embeds(
            ["artemis", "apollo", "ares", "alecto", "persephone"], success=True,
            overrides={"artemis":{"reload":2,"visible":True},})
        return [msg1,msg2,msg3]

    def hermes(self):
        msg1 = simple_embed("Hermes can make max 2 visible and alive allies attack with him and use there ability if allowed")
        return [msg1]

    def hades_ow(self):
        msg1 = simple_embed("Hades overworld (Hades_ow) gives dmg boost💥 to all allies for 2 turns")
        msg2 = simple_embed("dmg boost💥 amount depends on the nb of dead💀 ally")
        msg3 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hades_ow"], success=True,
            overrides={
                "poseidon":{"visible": True,"effects": {"hades_ow_do_more_dmg": 0}},
                "hephaestus":{"visible": True,"effects": {"hades_ow_do_more_dmg": 0}},
                "ares":{"visible": True,"effects": {"hades_ow_do_more_dmg": 0}},
                "aphrodite":{"visible": True,"effects": {"hades_ow_do_more_dmg": 0}},
                "hades_ow":{"visible": True,"effects": {"hades_ow_do_more_dmg": 0},"reload":4}
                }
        )
        msg4 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hades_ow"], success=True,
            overrides={
                "poseidon":{"visible": True,"alive": False,"hp":0},
                "hephaestus":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1}},
                "ares":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1}},
                "aphrodite":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1}},
                "hades_ow":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1},"reload":4}
                }
        )
        msg5 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hades_ow"], success=True,
            overrides={
                "poseidon":{"visible": True,"alive": False,"hp":0},
                "hephaestus":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1}},
                "ares":{"visible": True,"alive": False,"hp":0},
                "aphrodite":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1}},
                "hades_ow":{"visible": True,"effects": {"hades_ow_do_more_dmg": 1},"reload":4}
                }
        )
        msg6 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hades_ow"], success=True,
            overrides={
                "poseidon":{"visible": True,"alive": False,"hp":0},
                "hephaestus":{"visible": True,"alive": False,"hp":0},
                "ares":{"visible": True,"alive": False,"hp":0},
                "aphrodite":{"visible": True,"effects": {"hades_ow_do_more_dmg": 2}},
                "hades_ow":{"visible": True,"effects": {"hades_ow_do_more_dmg": 2},"reload":4}
                }
        )
        msg7 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hades_ow"], success=True,
            overrides={
                "poseidon":{"visible": True,"alive": False,"hp":0},
                "hephaestus":{"visible": True,"alive": False,"hp":0},
                "ares":{"visible": True,"alive": False,"hp":0},
                "aphrodite":{"visible": True,"alive": False,"hp":0},
                "hades_ow":{"visible": True,"effects": {"hades_ow_do_more_dmg": 2},"reload":4}
                }
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7]

    def thanatos(self):
        msg1 = simple_embed("Thanatos has a 50% chance to instakill ennemy,if succesfull takes 5 dmg (can attakc with hermes)")
        msg2 = create_god_tutorial_embeds(
            ["athena","hephaestus" , "ares", "alecto", "persephone"], success=False,
            overrides={"ares":{"hp":0,"visible":True,"alive":False}}
        )
        msg3 = create_god_tutorial_embeds(
            ["zeus","thanatos" , "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "thanatos":{"visible": True,"hp":6,"reload":2}}
        )
        return [msg1,msg2,msg3]

    def cerberus(self):
        msg1 = simple_embed("Cerberus can give attract⛑️ to an ally for 2 turns (can't attack with hermes)")
        msg2 = simple_embed("Attract⛑️ forces ennemy to attack this maggod, when given Cerberus looses 1hp and gives it to recipient")
        msg3 = create_god_tutorial_embeds(
            ["athena","cerberus" , "ares", "alecto", "persephone"], success=True,
            overrides={"ares":{"hp":8,"visible":True,"effects":{"cerberus_more_max_hp_per_visible_ally":0}},
                       "cerberus":{"visible":True,"hp":9,"reload":6}}
        )
        return [msg1,msg2,msg3]

    def charon(self):
        msg1 = simple_embed("Charon gives protect 🧿 to an ally for 2 turns (can't attack with hermes)")
        msg2 = simple_embed("Charon heals by 2 - the number of dead allies if - it is dmg ex : 4 dead = -2hp")
        msg3 = simple_embed("Charon protect 🧿 fixes the hp status of target (ally), this means the ally can't take damage or heal")
        msg4 = simple_embed("Charon also removes all negative effects from visible allies")
        msg5 = create_god_tutorial_embeds(
            ["athena","charon" , "ares", "apollo", "persephone"], success=True,
            overrides={"ares":{"visible":True,"effects":{"tisi_freeze_timer":0,"alecto_get_more_dmg":2,"mega_do_less_dmg":-4}},
                       "apollo":{"visible":True,"alive":False,"hp":0,"effects":{"zeus_stun":0}},
                       "charon":{"visible":True,"hp":8,"reload":6,"effects":{"aphro_charm":0}},
                       "athena":{"visible":True,"alive":False,"hp":0},
                       "persephone":{"visible":False,"effects":{"aphro_charm":0}}}
        )
        msg6 = create_god_tutorial_embeds(
            ["athena","charon" , "ares", "apollo", "persephone"], success=True,
            overrides={"ares":{"visible":True,"effects":{"charon_invisible_duration":0}},
                       "apollo":{"visible":True,"alive":False,"hp":0},
                       "charon":{"visible":True,"hp":7,"reload":6},
                       "athena":{"visible":True,"alive":False,"hp":0},
                       "persephone":{"visible":False,"effects":{"aphro_charm":0}}}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6]

    def persephone(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def hades_uw(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def tisiphone(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def alecto(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def megaera(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def hecate(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

