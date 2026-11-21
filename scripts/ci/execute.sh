#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cuda-12.8/bin:/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda-12.8/lib64"
echo "=== make test: ejecutar C y kernels NVIDIA CUDA reales ==="
make --no-print-directory test
for folder in build/user-c build/user-cuda; do
  if [[ -d "$folder" ]]; then
    while IFS= read -r -d '' program; do
      echo "=== Ejecutando: $program ==="
      timeout --signal=TERM 120s "$program"
      echo "=== OK: $program ==="
    done < <(find "$folder" -maxdepth 1 -type f -executable -print0 | sort -z)
  fi
done
echo "Todos los programas ejecutados correctamente."
