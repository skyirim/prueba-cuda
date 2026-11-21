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


## Baseline UCAM recibido

La fuente técnica ya existe: [docs/hardware-base.md](../../../docs/hardware-base.md), hash SHA-256 documentado. Los mínimos verificables son 12 cores físicos CPU, 4.352 CUDA cores de 1 GPU NVIDIA completa, 31 GiB RAM y 11.264 MiB VRAM. Los 68 SM Turing no son un mínimo separado. El estado sigue DRAFT hasta ejecutar los programas C y CUDA en el servidor y certificar una AMI AWS y la portabilidad de fuentes para sm_75. Antes de cada nueva EC2 GPU es obligatoria selección de precio Spot en tiempo real: [docs/precio-en-arranque.md](../../../docs/precio-en-arranque.md).


## Revisiones Codex

Aplicar la Skill codex-review-loop antes de completar cambios CUDA. El Makefile debe incluir sm_75 UCAM y PTX forward-compatible, no únicamente cubins sm_75/sm_89; comprobar nuevas observaciones y ejecutarlas en GPU real cuando exista instancia validada.
