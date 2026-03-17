import re


UNSAFE_PATTERNS = [
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bDELETE\b",
    r"\bDETACH\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bFOREACH\b",
    r"\bLOAD\s+CSV\b",
    r"\bCALL\s+dbms\b",
    r"\bCALL\s+apoc\.(?:load|periodic|export)\b",
]


class QueryValidationError(ValueError):
    """Raised when a generated Cypher query is unsafe to execute."""


def validate_read_only_cypher(query: str) -> str:
    normalized = query.strip()
    if not normalized:
        raise QueryValidationError("Cypher is empty.")

    normalized = re.sub(r";+\s*$", "", normalized)
    if ";" in normalized:
        raise QueryValidationError("Only a single Cypher statement is allowed.")

    if not re.search(r"\bRETURN\b", normalized, flags=re.IGNORECASE):
        raise QueryValidationError("Cypher must include a RETURN clause.")

    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            raise QueryValidationError(f"Cypher contains a blocked keyword or procedure: {pattern}")

    return normalized
