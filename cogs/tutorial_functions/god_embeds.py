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
        msg4 = simple_embed("Poseidon gives shield to random ally when alive❤️ and visible👁️")
        msg5 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True},
                "hephaestus":{
                "visible": True,"effects": {"posi_shield": 5}
                }}
        )
        msg6 = simple_embed("When Poseidon dies the shield is lost")
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
                "visible": True,"effects": {"hep_shield": 2},"reload":3},
                "ares":{
                "visible": True,"effects": {"hep_shield": 2}
                }}
        )
        msg3 = simple_embed("Hepaestus gives a 1 turn shield🛡️ to all visible when he attacks with hermes")
        msg4 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "poseidon":{
                "visible": True,"effects": {"hep_shield": 1}},
                "hephaestus":{
                "visible": True,"effects": {"hep_shield": 1},"reload":3},
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
                "visible": True,"effects": {"hep_shield": 1},"reload":3},
                "hermes":{
                "visible": True,"effects": {"hep_shield": 1},"reload":6
                }}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6]

    def aphrodite(self):
        msg1 = simple_embed("Aphrodite ability is activated when she attacks alone (visible or invisible) or with hermes")
        msg2 = simple_embed("Aphrodite can attack visible and invisible ennemy.\n When attacking invisible she gives charm💘 for 3 turns to target\n charm makes t so that when the ennemy attaks it heals by 1hp it's target (your ally maggod) ")
        msg3 = create_god_tutorial_embeds(
            ["athena", "thanatos", "ares", "alecto", "persephone"], success=True,
            overrides={
                "ares":{
                "hp":5,"effects":{"aphro_charm":0}}
                }
        )
        msg4 = create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "hermes", "hera"], success=True,
            overrides={
                "aphrodite":{
                "visible": True}
                }
        )
        return [msg1,msg2,msg3,msg4]

    def ares(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def hera(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def zeus(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def athena(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def apollo(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def artemis(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def hermes(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def hades_ow(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def thanatos(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def cerberus(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

    def charon(self):
        msg1 = simple_embed("Ability description coming soon...")
        return [msg1]

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

