#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cuda-12.8/bin:/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda-12.8/lib64"
echo "=== make all: compilar las aplicaciones C y CUDA del repositorio ==="
make --no-print-directory all
mkdir -p build/user-c build/user-cuda
if [[ -d programs/c ]]; then
  while IFS= read -r -d '' file; do
    name="$(basename "$file" .c)"
    printf 'Compilando C: %s\n' "$file"
    gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror "$file" -o "build/user-c/$name"
  done < <(find programs/c -maxdepth 1 -type f -name '*.c' -print0 | sort -z)
fi
if [[ -d programs/cuda ]]; then
  while IFS= read -r -d '' file; do
    name="$(basename "$file" .cu)"
    printf 'Compilando CUDA: %s\n' "$file"
    nvcc -O2 -lineinfo \
      -gencode arch=compute_75,code=sm_75 \
      -gencode arch=compute_75,code=compute_75 \
      "$file" -o "build/user-cuda/$name"
  done < <(find programs/cuda -maxdepth 1 -type f -name '*.cu' -print0 | sort -z)
fi
echo "Compilacion completa."
