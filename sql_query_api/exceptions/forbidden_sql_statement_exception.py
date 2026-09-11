class ForbiddenSqlStatementError(Exception):
    """Raised when a SQL statement is rejected by the safety validation layer."""

    def __init__(self, message: str):
        super().__init__(message)

    def __str__(self) -> str:
        """Return a human-readable description of the forbidden statement."""
        return f"Forbidden SQL statement: {self.args[0]}"

    def __repr__(self) -> str:
        """Return an unambiguous representation of the exception."""
        return f"{self.__class__.__name__}(message={self.args[0]!r})"
