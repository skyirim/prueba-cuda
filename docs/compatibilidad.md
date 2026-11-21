# Compatibilidad y equivalencia comprobable — C / CUDA / Linux

## 1. Niveles distintos de compatibilidad

A. **Compilación fuente C**: GCC, estándar C elegido, headers, bibliotecas, compilación con advertencias y pruebas. La arquitectura del ejecutable resultante depende de CPU.
B. **Compilación fuente CUDA**: nvcc, toolchain host, target de GPU (-gencode / CMAKE_CUDA_ARCHITECTURES), libraries y toolkits disponibles.
C. **Ejecución CUDA**: GPU y controlador real, CUDA runtime, compute capability apropiada, VRAM y recursos por kernel; pruebas lanzadas y sincronizadas. nvcc --version por sí solo **no** verifica ejecución GPU.
D. **Binarios transportables**: x86-64 y AArch64 no ejecutan sus binarios nativos mutuamente; recompilar. GPU cubin requiere compatibilidad de compute capability; incluir PTX para compatibilidad futura si procede y revisar excepciones de arquitecturas.
E. **Resultados comparables**: datos, precisión numérica/tolerancias, orden de reducciones, atomicidad, sincronización, límites y rendimiento. No prometer identidad bit a bit de cálculos paralelos.

## 2. Criterios de aceptación mínimos

- [ ] Documento base identificado, íntegro y hash registrado.
- [ ] CPU: cores físicos disponibles >= referencia, hilos suficientes, ISA/ABI y memoria suficientes.
- [ ] GPU: número de dispositivos requerido; asignación real de SM y núcleos CUDA >= referencia **con evidencia aprobada**.
- [ ] Capacidad de VRAM accesible >= referencia; compute capability y funciones CUDA suficientes.
- [ ] Toolkit/driver/compiler/libc compatibles y fijados.
- [ ] Compilación real: C, CUDA, librerías y targets de la referencia.
- [ ] Ejecución real en GPU de pruebas del repositorio; comparar contra equipo base.
- [ ] Tests de tamaños máximos, ocupación, concurrencia y memoria; diferencias documentadas.
- [ ] Logs de GitHub y/o CloudWatch, artefactos y trazabilidad SHA/AMI/commit.
- [ ] Coste y permisos revisados; terminación automática probada.

**Cualquier casilla incumplida mantiene estado NO DEMOSTRADO.**

## 3. Inventario de GPU

El número de CUDA cores no se devuelve directamente en una propiedad portátil de CUDA Runtime. cudaDeviceProp.multiProcessorCount informa SM visibles; para obtener CUDA cores se necesita correspondencia cores/SM de la microarquitectura publicada por NVIDIA y justificar recursos accesibles con virtualización. Una fracción vGPU no equivale necesariamente a una fracción lineal de CUDA cores y puede tener límites diferentes de scheduler, memoria y funciones; si no se demuestra, falla equivalencia.

La GPU del equipo base debe identificarse por modelo, compute capability, SM, VRAM y, si aplica, instrucciones y Tensor cores. A igualdad de número de cores puede diferir el throughput, precisión, cache, ancho de banda y compatibilidad.

Comandos de inventario: lscpu; nproc; free -h; uname -m; gcc --version; nvcc --version; nvidia-smi -q; ejecutar src/cuda_smoke.cu para leer cudaDeviceProp, asignar buffers y verificar resultados. Registrar salida, fecha y hash del ejecutable.

## 4. Política de builds

- C: -std=c11 -Wall -Wextra -Wpedantic -Werror cuando el código lo permita, sanitizers CPU en CI no GPU; no mezclar resultados.
- CUDA: fijar versión NVCC y target de destino; no asumir que sm_75 (T4g) es idéntico a sm_89 (L4). Usar target concreto con evidencia de GPU y compatibilidad PTX cuando proceda.
- Para ARM64, cross-compilation no reemplaza ejecución; ejecutar en ARM64 nativo.
- Fijar entradas y tolerancias en cada test; errores CUDA, cudaGetLastError y cudaDeviceSynchronize obligatorios.
- Prohibido aceptar pruebas solo de compilación si el requisito es ejecutar en GPU.
- El script check_baseline.py nunca certifica por sí solo equivalencia: solo compara números documentados cuando tienen evidencia; exige pruebas de ejecución separadas.

## 5. Criterio de portabilidad

Garantizar que **fuentes** C/CUDA correctamente portadas compilan y pasan pruebas en las dos plataformas solo después de ejecutar y comprobarlas. No garantizar que cualquier programa arbitrario vaya a ser portable; uso de ensamblador específico, intrínsecos, APIs/flags no compatibles, límites de recursos o comportamiento indefinido pueden impedirlo. Ante una incompatibilidad, modificar la fuente con solución portátil y test de regresión sin falsear la referencia.

Referencias: https://docs.nvidia.com/cuda/cuda-programming-guide/ ; https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html ; https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html
