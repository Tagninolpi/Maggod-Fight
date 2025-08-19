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
                "visible": True,"alive": False},
                "hephaestus":{
                "visible": True
                }}
        )
        return [msg1,msg2,msg3,msg4,msg5,msg6,msg7]

    def hephaestus(self):
        return create_god_tutorial_embeds(
            ["hephaestus", "poseidon", "athena", "apollo", "ares"], success=True
        )

    def aphrodite(self):
        return create_god_tutorial_embeds(
            ["aphrodite", "zeus", "hera", "athena", "apollo"], success=True
        )

    def ares(self):
        return create_god_tutorial_embeds(
            ["ares", "athena", "hephaestus", "aphrodite", "poseidon"], success=True
        )

    def hera(self):
        return create_god_tutorial_embeds(
            ["hera", "zeus", "athena", "aphrodite", "charon"], success=True
        )

    def zeus(self):
        return create_god_tutorial_embeds(
            ["zeus", "poseidon", "aphrodite", "ares", "athena"], success=True
        )

    def athena(self):
        return create_god_tutorial_embeds(
            ["athena", "ares", "hera", "hephaestus", "apollo"], success=True
        )

    def apollo(self):
        return create_god_tutorial_embeds(
            ["apollo", "artemis", "athena", "zeus", "hermes"], success=True
        )

    def artemis(self):
        return create_god_tutorial_embeds(
            ["artemis", "apollo", "athena", "aphrodite", "hermes"], success=True
        )

    def hermes(self):
        return create_god_tutorial_embeds(
            ["hermes", "apollo", "athena", "ares", "artemis"], success=True
        )

    def hades_ow(self):
        return create_god_tutorial_embeds(
            ["hades_ow", "thanatos", "cerberus", "charon", "persephone"], success=True
        )

    def thanatos(self):
        return create_god_tutorial_embeds(
            ["thanatos", "hades_ow", "cerberus", "tisiphone", "alecto"], success=True
        )

    def cerberus(self):
        return create_god_tutorial_embeds(
            ["cerberus", "charon", "thanatos", "hades_uw", "tisiphone"], success=True
        )

    def charon(self):
        return create_god_tutorial_embeds(
            ["charon", "cerberus", "persephone", "alecto", "hades_uw"], success=True
        )

    def persephone(self):
        return create_god_tutorial_embeds(
            ["persephone", "tisiphone", "alecto", "charon", "megaera"], success=True
        )

    def hades_uw(self):
        return create_god_tutorial_embeds(
            ["hades_uw", "tisiphone", "alecto", "megaera", "cerberus"], success=True
        )

    def tisiphone(self):
        return create_god_tutorial_embeds(
            ["tisiphone", "alecto", "megaera", "hades_uw", "persephone"], success=True
        )

    def alecto(self):
        return create_god_tutorial_embeds(
            ["alecto", "tisiphone", "megaera", "hades_uw", "cerberus"], success=True
        )

    def megaera(self):
        return create_god_tutorial_embeds(
            ["megaera", "hecate", "alecto", "tisiphone", "hades_uw"], success=True
        )

    def hecate(self):
        return create_god_tutorial_embeds(
            ["hecate", "megaera", "tisiphone", "alecto", "hades_uw"], success=True
        )

