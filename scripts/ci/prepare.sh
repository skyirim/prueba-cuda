#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# El Security Group solo permite TCP/443; repositorios Ubuntu por HTTPS.
for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
    [[ ! -f "$f" ]] || sed -i 's|http://|https://|g' "$f"
done
export PATH="/usr/local/cuda-12.8/bin:/usr/local/cuda/bin:$PATH"
if ! command -v gcc >/dev/null || ! command -v make >/dev/null; then
    apt-get update -qq
    apt-get install -y --no-install-recommends build-essential make
fi
command -v nvidia-smi
command -v nvcc || { echo "ERROR: nvcc no instalado en la AMI"; exit 1; }
command -v gcc
command -v make
mkdir -p build artifacts
echo "Compiladores y directorios preparados."
