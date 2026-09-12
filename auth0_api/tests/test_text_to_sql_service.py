import pytest
from app.services.text_to_sql_service import TextToSqlService
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

@pytest.fixture
def text_to_sql_service(mock_ai_service):
    return TextToSqlService(mock_ai_service)

@pytest.mark.asyncio
async def test_generate_sql_from_text_success(text_to_sql_service, mock_ai_service):
    """Test successful SQL generation from text."""
    # Mock schema retrieval
    mock_schema = "CREATE TABLE users (id INT, name TEXT)"
    
    # Mock GraphQL response
    mock_gql_response = MagicMock()
    mock_gql_response.status_code = 200
    mock_gql_response.json.return_value = {
        "data": {
            "getTableSchema": {
                "schema": mock_schema
            }
        }
    }
    mock_gql_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", return_value=mock_gql_response):
        # Mock LLM SQL generation
        mock_ai_service.get_greeting.return_value = "SELECT * FROM users"
        
        result = await text_to_sql_service.generate_sql_from_text("get all users")
        
        assert result["sql"] == "SELECT * FROM users"
        assert result["schema"] == mock_schema
        mock_ai_service.generate_embeddings.assert_called_once_with("get all users")
        mock_ai_service.get_greeting.assert_called_once()

@pytest.mark.asyncio
async def test_generate_sql_with_execution(text_to_sql_service, mock_ai_service):
    """Test SQL generation and execution."""
    mock_schema = "TABLE schema"
    mock_sql = "SELECT 1"
    mock_results = [{"col": 1}]
    
    # Mock GraphQL responses for both schema and execution
    mock_schema_response = MagicMock()
    mock_schema_response.status_code = 200
    mock_schema_response.json.return_value = {"data": {"getTableSchema": {"schema": mock_schema}}}
    
    mock_exec_response = MagicMock()
    mock_exec_response.status_code = 200
    mock_exec_response.json.return_value = {"data": {"executeSqlStatement": mock_results}}
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = [mock_schema_response, mock_exec_response]
        mock_ai_service.get_greeting.return_value = mock_sql
        
        result = await text_to_sql_service.generate_sql_from_text("test query", execute=True)
        
        assert result["sql"] == mock_sql
        assert result["results"] == mock_results
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_generate_sql_graphql_error(text_to_sql_service, mock_ai_service):
    """Test SQL generation when GraphQL returns error."""
    mock_error_response = MagicMock()
    mock_error_response.status_code = 200
    mock_error_response.json.return_value = {"errors": [{"message": "GraphQL Error"}]}
    
    with patch("httpx.AsyncClient.post", return_value=mock_error_response):
        result = await text_to_sql_service.generate_sql_from_text("test query")
        
        assert "error" in result
        assert "GraphQL Error" in result["error"]

@pytest.mark.asyncio
async def test_generate_sql_http_error(text_to_sql_service, mock_ai_service):
    """Test SQL generation when HTTP request fails."""
    with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPError("Connection failed")):
        result = await text_to_sql_service.generate_sql_from_text("test query")

        assert "error" in result
        assert "Connection failed" in result["error"]


def test_precheck_sql_accepts_single_select():
    ok, feedback = TextToSqlService._precheck_sql("SELECT * FROM users")
    assert ok is True
    assert feedback == ""


def test_precheck_sql_accepts_trailing_semicolon():
    ok, _ = TextToSqlService._precheck_sql("SELECT * FROM users;")
    assert ok is True


def test_precheck_sql_accepts_semicolon_inside_string():
    ok, _ = TextToSqlService._precheck_sql("SELECT title FROM album WHERE title ILIKE 'Get; Up'")
    assert ok is True


def test_precheck_sql_rejects_multi_statement():
    ok, feedback = TextToSqlService._precheck_sql(
        "SELECT COUNT(*) FROM artist; SELECT title FROM album;"
    )
    assert ok is False
    assert "Multiple SQL statements" in feedback


def test_precheck_sql_strips_markdown_and_prefix():
    ok, _ = TextToSqlService._precheck_sql("```sql\nSELECT * FROM users\n```")
    assert ok is True
    ok, _ = TextToSqlService._precheck_sql("SQL: SELECT * FROM users")
    assert ok is True


def test_precheck_sql_rejects_non_select():
    ok, feedback = TextToSqlService._precheck_sql("DELETE FROM users")
    assert ok is False
    assert "SELECT" in feedback


@pytest.mark.asyncio
async def test_generate_sql_retries_on_multi_statement(text_to_sql_service, mock_ai_service):
    """Multi-statement output triggers a retry that produces a valid SELECT."""
    mock_schema = "TABLE schema"
    mock_gql_response = MagicMock()
    mock_gql_response.status_code = 200
    mock_gql_response.json.return_value = {"data": {"getTableSchema": {"schema": mock_schema}}}
    mock_gql_response.raise_for_status = MagicMock()

    mock_ai_service.get_greeting.side_effect = [
        "SELECT COUNT(*) FROM artist; SELECT title FROM album;",
        "SELECT (SELECT COUNT(*) FROM artist) AS count, (SELECT title FROM album LIMIT 1) AS title;",
    ]

    with patch("httpx.AsyncClient.post", return_value=mock_gql_response):
        result = await text_to_sql_service.generate_sql_from_text("multi part query")

    assert result["sql"] == (
        "SELECT (SELECT COUNT(*) FROM artist) AS count, (SELECT title FROM album LIMIT 1) AS title;"
    )
    assert mock_ai_service.get_greeting.call_count == 2


@pytest.mark.asyncio
async def test_generate_sql_retry_exhausted_returns_error(text_to_sql_service, mock_ai_service):
    """Persistently invalid output surfaces the pre-check feedback as an error."""
    mock_schema = "TABLE schema"
    mock_gql_response = MagicMock()
    mock_gql_response.status_code = 200
    mock_gql_response.json.return_value = {"data": {"getTableSchema": {"schema": mock_schema}}}
    mock_gql_response.raise_for_status = MagicMock()

    mock_ai_service.get_greeting.side_effect = [
        "SELECT COUNT(*) FROM artist; SELECT title FROM album;",
        "SELECT COUNT(*) FROM artist; SELECT title FROM album;",
    ]

    with patch("httpx.AsyncClient.post", return_value=mock_gql_response):
        result = await text_to_sql_service.generate_sql_from_text("multi part query")

    assert "error" in result
    assert "Multiple SQL statements" in result["error"]
    assert mock_ai_service.get_greeting.call_count == 2
