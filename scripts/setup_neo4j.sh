#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-wafergraph123}"

cd "$ROOT_DIR"

echo "Starting Neo4j..."
docker compose -f "$COMPOSE_FILE" up -d neo4j

echo "Waiting for Neo4j to accept Cypher connections..."
until docker compose -f "$COMPOSE_FILE" exec -T neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1;" >/dev/null 2>&1; do
  sleep 2
done

echo "Seeding wafer / recipe / metrology demo graph..."
docker compose -f "$COMPOSE_FILE" exec -T neo4j \
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -f /seed/wafer_graph.cypher

echo
echo "Neo4j is ready."
echo "Browser: http://localhost:7474"
echo "Bolt: bolt://localhost:7687"
echo "Username: neo4j"
echo "Password: $NEO4J_PASSWORD"
