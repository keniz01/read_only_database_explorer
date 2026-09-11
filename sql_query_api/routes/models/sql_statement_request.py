from pydantic import BaseModel


class SqlStatementRequest(BaseModel):
    """Request payload carrying the SQL statement to execute."""

    sql_statement: str = ""
