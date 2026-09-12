# Prompt Changelog

Versioning follows semantic versioning (MAJOR.MINOR.PATCH). Version is implied by Git (commits and tags).

## text_to_sql

- **v1.0.0** (initial): System and user prompts for text-to-SQL generation (Postgres, table-augmented style). Stored in `prompts/text_to_sql/` with file-based registry.
- **v1.1.0**: Prompt v2 — explicitly require exactly one SELECT statement (aligns with the single-statement safety rule), allow scalar subqueries, add multi-part question example answered via scalar subquery.
