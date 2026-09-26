#!/bin/bash
set -e

export OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3:8b}"

echo "=== Step 1: Starting infrastructure ==="
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
    echo "GPU detected — starting with GPU override"
    docker compose -f docker-compose.yml -f docker-compose.override.yml \
                   -f docker-compose.gpu.yml up -d
else
    echo "No GPU — starting with CPU override"
    docker compose -f docker-compose.yml -f docker-compose.override.yml \
                   -f docker-compose.cpu.yml up -d
fi
sleep 5

echo "=== Step 2: Checking Ollama model ==="
# tail -n + 2: prints start at line 2, go to the end
# awk splits
# -qx quiet and exact match
if docker exec ollama-llm ollama list | tail -n +2 | awk '{print $1}' | grep -qx "${OLLAMA_MODEL}"; then
    echo "Model ${OLLAMA_MODEL} already present"
else
    echo "Pulling ${OLLAMA_MODEL}..."
    docker exec ollama-llm ollama pull "${OLLAMA_MODEL}"
fi

echo "=== Step 3: Running pipeline ==="
uv run python src/01_setup_postgres.py
uv run python src/02_verify_source.py
uv run python src/03_bronze_ingestion.py
uv run python src/04_cdc_simulation.py
uv run python src/03_bronze_ingestion.py
uv run python src/05_silver_quality.py
#uv run python src/06_serving_layer.py
#uv run python src/07_feature_engineering.py
#uv run python src/08_agent_llm.py

echo "=== Pipeline complete ==="