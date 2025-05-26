#!/usr/bin/env bash
set -euo pipefail

# This script starts telemetry services and runs two example containers

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Start SigNoz + Collector exposing 4317/4318 on host
echo "Starting telemetry services (SigNoz + Collector)..."
export PROJECT_ROOT="$ROOT_DIR"
docker compose -f "$ROOT_DIR/telemetry_services/telemetry/signoz/docker/docker-compose.yaml" up -d

# Build example image
echo "Building example image..."
docker compose -f "$ROOT_DIR/docker/docker-compose.yml" build

# Run two instances of example (same compose project), collector reachable via host.docker.internal
echo "Starting two example containers..."
docker compose -f "$ROOT_DIR/docker/docker-compose.yml" up -d --scale example=2

echo "Done. SigNoz UI should be at http://localhost:8181"

