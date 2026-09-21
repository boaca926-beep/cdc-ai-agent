#!/usr/bin/env bash
set -e

if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
  echo "GPU detected — using GPU override"
  docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d "$@"
else
  echo "No GPU — using CPU override"
  docker compose -f docker-compose.yml -f docker-compose.cpu.yml up -d "$@"
fi