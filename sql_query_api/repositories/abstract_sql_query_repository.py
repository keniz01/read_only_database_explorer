from abc import ABC, abstractmethod
from typing import Any


class ISqlQueryRepository(ABC):
    """Contract for governed, read-only SQL query repositories."""

    @abstractmethod
    async def execute_sql_statement(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a SQL statement and return the results."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    async def get_table_schema(self, embeddings: list[float]) -> dict[str, Any]:
        """Get table schema information using vector embeddings."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    async def introspect_schema(self) -> dict[str, Any]:
        """Dynamically introspect database schema information."""
        raise NotImplementedError("This method should be overridden by subclasses.")
