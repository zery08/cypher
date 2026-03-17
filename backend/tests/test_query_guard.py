import pytest

from app.services.query_guard import QueryValidationError, validate_read_only_cypher


def test_validate_read_only_cypher_accepts_safe_query():
    query = "MATCH (n:Person) RETURN n LIMIT 10;"
    assert validate_read_only_cypher(query) == "MATCH (n:Person) RETURN n LIMIT 10"


@pytest.mark.parametrize(
    "query",
    [
        "",
        "MATCH (n:Person)",
        "MATCH (n) RETURN n; MATCH (m) RETURN m",
        "CREATE (n:Person {name: 'x'}) RETURN n",
        "CALL dbms.components() YIELD name RETURN name",
    ],
)
def test_validate_read_only_cypher_rejects_unsafe_query(query):
    with pytest.raises(QueryValidationError):
        validate_read_only_cypher(query)
