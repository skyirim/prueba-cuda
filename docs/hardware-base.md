# Máquina de referencia — transcripción, procedencia y criterios

**Estado 2026-11-21: PENDIENTE POR AUSENCIA DEL ARCHIVO.** El mensaje del usuario se refiere a un archivo adjunto; el listado de adjuntos de esta conversación estaba vacío. Una búsqueda en la biblioteca no identificó inequívocamente ese archivo. No utilizar diapositivas genéricas de la asignatura como sustituto de la especificación de un equipo real.

## 1. Incorporación obligatoria del documento original

1. Registrar nombre exacto, tamaño, SHA-256, fecha y origen del archivo. Guardar el fichero en docs/fuentes/ si su licencia y confidencialidad lo permiten; si no, guardar una referencia auditable y transcribir sus características técnicas permitidas.
2. Incluir a continuación **todo** el contenido técnico relevante: CPU, sockets, modelo, núcleos físicos, hilos, GHz, ISA, RAM, GPU NVIDIA modelo, cantidad de GPUs, SM, CUDA cores, VRAM, compute capability, controlador, CUDA, sistema operativo, herramientas/compiladores, restricciones de ejercicios, bibliotecas y requisitos de ejecución.
3. Para cada dato, anotar texto exacto del documento, página/sección y si es valor medido, especificación del fabricante o inferencia pendiente. Si hay ambigüedad (ej., "cores"), resolverla con evidencia, no por suposición.
4. Rellenar config/hardware-base.json (inicialmente contiene null) y verificar con scripts/check_baseline.py. Las propiedades no informadas en el documento deben quedar desconocidas, no se introducen mínimos arbitrarios.
5. Medir la referencia real cuando sea posible y adjuntar evidencia de lscpu, nvidia-smi, cudaDeviceProp, gcc, nvcc y resultados de pruebas. Si no está disponible la referencia, no prometer ejecución idéntica ni equivalencia de comportamiento.

## 2. Ficha de dimensiones

| Campo | Equipo base | Evidencia requerida |
| --- | --- | --- |
| Modelo y arquitectura CPU | PENDIENTE | Documento original + lscpu |
| CPUs/sockets | PENDIENTE | Documento + inventario |
| Núcleos físicos CPU | PENDIENTE | No confundir vCPU/hilos |
| Hilos lógicos / SMT | PENDIENTE | topología medible |
| Memoria RAM / ISA | PENDIENTE | captura/medición |
| GPU(s) NVIDIA y tipo físico/virtual | PENDIENTE | proveedor + nvidia-smi |
| Multiprocesadores SM | PENDIENTE | CUDA Runtime |
| Núcleos CUDA FP32 efectivos | PENDIENTE | ficha NVIDIA de chip + topología validada y evidencia de virtualización |
| Tensor/RT cores, si relevantes | PENDIENTE | ficha NVIDIA |
| VRAM accesible por proceso | PENDIENTE | cudaMemGetInfo y dispositivo |
| Compute capability | PENDIENTE | cudaDeviceProp / NVIDIA |
| Máximo threads/bloque/SM y shared memory | PENDIENTE | CUDA properties |
| SO, kernel, GCC, CUDA, driver y bibliotecas | PENDIENTE | versiones y requisitos |
| Plataforma ejecutora real de prácticas | PENDIENTE | demostración sobre el equipo |

## 3. Significado de "equivalente"

- **Misma o mayor capacidad declarada:** CPU cores físicos y CUDA cores solo si su medición/atribución son comparables; comprobar además SM, RAM y VRAM.
- **Mismo software:** ABI de CPU y entorno CUDA adecuados; si arquitecturas difieren, recompilación explícita o binarios específicos por plataforma.
- **Misma funcionalidad:** tests reproducibles con respuestas validadas en la referencia y en el destino; resultados numéricos con tolerancia definida.
- **Mismo rendimiento:** no se puede deducir solo de cores; requerir benchmarking representativo si se exige.

Una GPU fraccionada G6f, por barata que sea, **no tiene certificada una cantidad igual de CUDA cores disponibles a una GPU física**. Mantenerla como candidata hasta demostrarlo.

## 4. Transcripción del archivo base

**[PENDIENTE: no se ha recibido el documento en esta conversación]**

No se ha añadido contenido de un supuesto archivo. Este encabezado se sustituirá por su transcripción fiel y evidencia cuando llegue.
