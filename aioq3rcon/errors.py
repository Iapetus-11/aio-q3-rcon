class RCONError(Exception):
    pass


class IncorrectPasswordError(RCONError):
    """Raised when the RCON  password is incorrect."""

    def __init__(self) -> None:
        super().__init__(
            "The password provided to the client was incorrect according to the server."
        )
