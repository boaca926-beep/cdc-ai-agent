#!/bin/bash
set -e

export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"

echo "=== Step 1: Starting infrastructure ==="
docker compose up -d
sleep 5

echo "=== Step 2: Checking Ollama model ==="
docker exec ollama-llm ollama list | awk '{print $1}' \
    | grep -qx "${OLLAMA_MODEL}" \
    || docker exec ollama-llm ollama pull "${OLLAMA_MODEL}"

echo "=== Step 3: Running pipeline ==="
#uv run python src/01_setup_postgres.py
#uv run python src/02_verify_source.py
#uv run python src/03_bronze_ingestion.py
#uv run python src/04_cdc_simulation.py
#uv run python src/03_bronze_ingestion.py
#uv run python src/05_silver_quality.py
#uv run python src/06_serving_layer.py
#uv run python src/07_feature_engineering.py
#uv run python src/08_agent_llm.py

echo "=== Pipeline complete ==="