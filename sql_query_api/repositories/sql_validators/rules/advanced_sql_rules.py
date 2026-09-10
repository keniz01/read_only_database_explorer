"""Advanced SQL safety rules for production hardening.

These rules complement the existing simple keyword‑based checks by using
`sqlglot` to inspect the parsed abstract syntax tree (AST) of a query. They
provide deterministic guarantees that only allowed constructs are present.
"""

import sqlglot
from sqlglot import exp


class AllowedNodeTypesRule:
    """Allow only a whitelist of sqlglot AST node types.

    The rule parses the raw SQL with sqlglot (PostgreSQL dialect) and walks the
    expression tree. If any node class name is not present in ``allowed`` the
    query is rejected. This provides a strong guarantee that no unexpected
    constructs (e.g. COPY, CALL, procedural statements) can slip through.
    """

    def __init__(self, allowed: set[str]):
        # Normalise to class names without the ``Expression`` suffix.
        self.allowed = {name.lower() for name in allowed}

    def check(self, stmt, raw: str) -> bool:  # noqa: D401
        """Return ``True`` if every AST node is in the allowed whitelist.

        Args:
            stmt: Ignored – we re‑parse ``raw`` with sqlglot for a reliable AST.
            raw: The original query string.
        """
        try:
            parsed = sqlglot.parse_one(raw, read="postgres")
        except Exception:
            return False
        for node in parsed.walk():
            node_name = type(node).__name__.replace("Expression", "").lower()
            if node_name not in self.allowed:
                return False
        return True


class ForbiddenFunctionsRule:
    """Reject queries that reference disallowed functions.

    The rule looks for ``sqlglot.exp.Function`` nodes and checks the function
    name against a user‑provided ``forbidden`` set (case‑insensitive).
    """

    def __init__(self, forbidden: set[str]):
        self.forbidden = {name.lower() for name in forbidden}

    def check(self, stmt, raw: str) -> bool:
        try:
            parsed = sqlglot.parse_one(raw, read="postgres")
        except Exception:
            return False
        for node in parsed.walk():
            if isinstance(node, exp.Function):
                func_name = node.name.lower()
                if func_name in self.forbidden:
                    return False
        return True


class ForbiddenTableRule:
    """Block reads from system/catalog tables unless explicitly allowed.

    Any table name that starts with ``pg_`` or matches ``information_schema``
    (or a sub‑schema thereof) causes the rule to reject.
    """

    def __init__(self, forbidden_prefixes: set[str] | None = None):
        self.forbidden_prefixes = {p.lower() for p in (forbidden_prefixes or {"pg_", "information_schema"})}

    def check(self, stmt, raw: str) -> bool:
        try:
            parsed = sqlglot.parse_one(raw, read="postgres")
        except Exception:
            return False
        for node in parsed.walk():
            if isinstance(node, exp.Table):
                tbl = str(node.this).lower() if hasattr(node, "this") else str(node.name).lower()
                for prefix in self.forbidden_prefixes:
                    if tbl.startswith(prefix):
                        return False
        return True
