---
name: cuda-equivalencia
description: Verifica y dimensiona hardware CPU/GPU Linux CUDA respecto a una máquina de referencia, comprueba cores y pruebas de compilación y ejecución. Úsala al cambiar hardware, CUDA, drivers, arquitectura o tests.
---

# Procedimiento de equivalencia CUDA

1. Leer README.md, AGENTS.md, docs/hardware-base.md y docs/compatibilidad.md.
2. Localizar documento original y registrar nombre/hash, secciones exactas y especificaciones. Si falta, detener certificación y anotar BLOQUEADO.
3. Diferenciar cores físicos CPU, hilos/vCPU, SM GPU, CUDA cores FP32, CUDA Tensor cores y VRAM efectiva. NVIDIA vGPU: no asumir cores físicos por factor de partición.
4. Completar config/hardware-base.json y ejecutar python3 scripts/check_baseline.py --baseline config/hardware-base.json --inventory INVENTARIO.json cuando esté disponible.
5. En destino real, ejecutar lscpu, nvidia-smi, nvcc, prueba src/cuda_smoke.cu y pruebas de proyecto. Confirmar que CUDA Runtime encuentra GPU.
6. Si cambia arquitectura CPU, recompilar binarios; si cambia compute capability, validar targets/driver y PTX con la guía NVIDIA.
7. Contrastar logs y resultados con equipo base, medir tolerancias/rendimiento, documentar cualquier incompatibilidad; no afirmar garantía universal.
8. Publicar informe de criterios cumplidos/incumplidos, evidencias y PR.
