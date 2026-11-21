#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/cuda-12.8/bin:/usr/local/cuda/bin:$PATH"
echo "=== Fecha UTC ==="
date -u --iso-8601=seconds
echo "=== Arquitectura y kernel ==="
uname -a
echo "=== CPU ==="
lscpu
echo "=== RAM ==="
free -h
echo "=== NVIDIA GPU y controlador ==="
nvidia-smi -q
echo "=== Versiones de compiladores ==="
gcc --version
nvcc --version
python3 - <<'PY'
import subprocess
from pathlib import Path
cpu = set()
for row in subprocess.check_output(["lscpu","-p=socket,core"], text=True).splitlines():
    if row.startswith("#"):
        continue
    cpu.add(tuple(row.split(",")[:2]))
count = len(cpu)
print(f"Nucleos fisicos CPU visibles: {count}", flush=True)
if count < 12:
    raise SystemExit("ERROR: menos de 12 nucleos CPU fisicos")
memtotal = int(next(x.split()[1] for x in Path("/proc/meminfo").read_text().splitlines()
                    if x.startswith("MemTotal:")))
print(f"RAM total: {memtotal} KiB", flush=True)
if memtotal < 31 * 1024 * 1024:
    raise SystemExit("ERROR: RAM inferior a 31 GiB")
rows = subprocess.check_output(
    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
    text=True).strip().splitlines()
cores_by_name = {"L4": 7424, "A10G": 9216, "L40S": 18176,
                 "RTX PRO 4500": 10496, "RTX PRO Server 6000": 24064}
qualified = False
for row in rows:
    name, mem = [part.strip() for part in row.rsplit(",", 1)]
    count_cuda = next((cores for namepart, cores in cores_by_name.items()
                       if namepart.lower() in name.lower()), 0)
    print(f"GPU {name}; VRAM {mem} MiB; CUDA cores de ficha {count_cuda}", flush=True)
    if count_cuda >= 4352 and int(mem) >= 11264:
        qualified = True
if not qualified:
    raise SystemExit("ERROR: ninguna GPU cumple los minimos UCAM de CUDA cores y VRAM")
PY
