class CheckFailureException(Exception):
    """Base exception for check failures."""

class NotInLobbyChannel(CheckFailureException):
    pass

class NotMatchParticipant(CheckFailureException):
    pass

class NotAllowedChannel(CheckFailureException):
    pass

class WrongMatchPhase(CheckFailureException):
    pass

class TurnInProgress(CheckFailureException):
    pass
