class SqlStatementExecutionError(Exception):
    """Raised when a validated SQL statement fails to execute or times out."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __repr__(self) -> str:
        """Return an unambiguous representation of the exception."""
        return f"{self.__class__.__name__}: {self.message}"
