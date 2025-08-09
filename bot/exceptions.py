from discord.app_commands import CheckFailure

class NotInLobbyChannel(CheckFailure):
    pass

class NotMatchParticipant(CheckFailure):
    pass

class NotAllowedChannel(CheckFailure):
    pass

class WrongMatchPhase(CheckFailure):
    pass

class TurnInProgress(CheckFailure):
    pass
