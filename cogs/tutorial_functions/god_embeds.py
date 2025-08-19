import discord
from .create_god_tutorial_embeds import create_god_tutorial_embeds, simple_embed

# ---------------- God Functions ----------------
class GodTutorials:
    """All god tutorial functions, each returning its embed(s)."""

    def poseidon(self):
        return create_god_tutorial_embeds(
            ["poseidon", "hephaestus", "aphrodite", "ares", "hera"], success=True
        )

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

