"""AST-based SQL analysis and object extraction using sqlglot."""

from __future__ import annotations

import sqlglot
from sqlglot import exp

FORBIDDEN_FUNCTIONS = frozenset({
    "pg_read_file",
    "pg_read_binary_file",
    "pg_write_file",
    "pg_write_binary_file",
    "pg_file_write",
    "pg_file_rename",
    "pg_file_unlink",
    "dblink",
    "dblink_exec",
    "dblink_connect",
    "dblink_open",
    "dblink_fetch",
    "dblink_close",
    "dblink_disconnect",
    "lo_import",
    "lo_export",
    "query_to_xml",
    "table_to_xml",
    "cursor_to_xml",
    "copy",
})

MUTATION_EXPRESSION_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.TruncateTable,
    exp.Merge,
)


class AstSqlAnalyzer:
    """Analyze and validate SQL statements using a concrete AST parser (sqlglot)."""

    def __init__(self, dialect: str = "postgres") -> None:
        self.dialect = dialect

    def parse_statements(self, sql: str) -> list[exp.Expression]:
        """Parse SQL into a list of AST expressions."""
        if not sql or not sql.strip():
            return []
        try:
            return [stmt for stmt in sqlglot.parse(sql, read=self.dialect) if stmt is not None]
        except Exception:
            try:
                return [stmt for stmt in sqlglot.parse(sql) if stmt is not None]
            except Exception:
                return []

    def is_single_statement(self, sql: str) -> bool:
        """Return whether the SQL parses to exactly one statement."""
        stmts = self.parse_statements(sql)
        return len(stmts) == 1

    def is_strictly_read_only(self, sql: str) -> bool:
        """Verify the statement is a pure SELECT/Query with zero mutations or dangerous functions."""
        stmts = self.parse_statements(sql)
        if len(stmts) != 1:
            return False

        root = stmts[0]
        # Must be a Query node (Select, Union, Intersect, Except)
        if not isinstance(root, exp.Query):
            return False

        # Traverse entire AST to ensure no mutating nodes are present anywhere
        for node in root.walk():
            if isinstance(node, MUTATION_EXPRESSION_TYPES):
                return False

            # Disallow dangerous administrative or side-effect functions
            if isinstance(node, (exp.Anonymous, exp.Func)):
                func_name = (node.name or "").lower()
                if func_name in FORBIDDEN_FUNCTIONS:
                    return False

        return True

    def extract_tables(self, sql: str) -> list[str]:
        """Extract all physical table identifiers, ignoring CTE aliases."""
        stmts = self.parse_statements(sql)
        if not stmts:
            return []

        root = stmts[0]
        cte_names = {cte.alias_or_name.lower() for cte in root.find_all(exp.CTE)}
        tables: list[str] = []
        for table_node in root.find_all(exp.Table):
            tname = (table_node.name or "").lower()
            if tname and tname not in cte_names and tname not in tables:
                tables.append(tname)
        return tables

    def extract_referenced_columns(self, sql: str) -> set[str]:
        """Extract all referenced columns from projections, predicates, joins, and aggregates."""
        stmts = self.parse_statements(sql)
        if not stmts:
            return set()

        root = stmts[0]
        # Check for top-level wildcard star in root select
        if isinstance(root, exp.Select):
            for select in root.selects:
                if isinstance(select, exp.Star):
                    return {"*"}

        columns: set[str] = set()
        for col_node in root.find_all(exp.Column):
            cname = (col_node.name or "").lower()
            if cname:
                columns.add(cname)
        return columns

    def extract_selected_columns_by_table(self, sql: str) -> dict[str, set[str]]:
        """Extract projected columns grouped by table or alias qualifier."""
        stmts = self.parse_statements(sql)
        if not stmts:
            return {}

        root = stmts[0]
        if not isinstance(root, exp.Select):
            return {}

        res: dict[str, set[str]] = {}
        for select in root.selects:
            if isinstance(select, exp.Star):
                res.setdefault("*", set()).add("*")
            elif isinstance(select, exp.Column):
                table_qualifier = (select.table or "*").lower()
                res.setdefault(table_qualifier, set()).add((select.name or "").lower())
            elif isinstance(select, exp.Alias):
                inner = select.this
                for col in inner.find_all(exp.Column):
                    table_qualifier = (col.table or "*").lower()
                    res.setdefault(table_qualifier, set()).add((col.name or "").lower())
            else:
                for col in select.find_all(exp.Column):
                    table_qualifier = (col.table or "*").lower()
                    res.setdefault(table_qualifier, set()).add((col.name or "").lower())
        return res
