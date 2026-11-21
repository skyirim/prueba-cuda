# Hardware de referencia real: servidor de Programación Paralela UCAM (2026)

**Estado:** documento de origen recibido y analizado el 21-11-2026; mínimos documentados, **equivalencia y ejecución cruzada todavía NO demostradas**.

## Identificación, integridad y protección de datos

- Archivo aportado: `Informacion_servidor_Programacion_Paralela_UCAM-2026.txt`.
- SHA-256 del archivo original (26.012 bytes): `07a5105d27c18ffd3caa464054885187d93a65b0240d4804d0efae910c349f8f`.
- Captura del entorno: **10-11-2026, 16:51–16:52 UTC**, según datos de sesión y `nvidia-smi`.
- Fuente primaria: salida del propio servidor (`uname -a`, `/proc/cpuinfo`, `free -h`, `nvidia-smi`). 12 registros `processor` numerados del 0 al 11.
- **No publicar el TXT original íntegro en un repositorio público:** contiene usuario de acceso, nombre de host, IP interna, IP de conexión y detalles de red. Este documento conserva el inventario técnico relevante **sin esos identificadores**. El SHA-256 permite comprobar autenticidad al volver a disponer del TXT original.
- Valores no observados (por ejemplo `nvcc --version`, `gcc --version` y un test CUDA ejecutado): se registran expresamente como desconocidos.

## Tabla de hardware obtenida directamente del archivo

| Propiedad | Valor de referencia | Procedencia |
|---|---|---|
| Distribución | Ubuntu 22.04.5 LTS | cabecera SSH |
| Kernel | GNU/Linux 5.15.0-187-generic, x86_64 | `uname -a` |
| Arquitectura CPU | x86-64 | `uname` / `cpuinfo` |
| Sockets físicos | 2 | `physical id: 0` y `physical id: 1` |
| CPU por socket | Intel Xeon E5-2603 v4 @ 1.70GHz | `model name` |
| Cores físicos por socket | 6 | `cpu cores: 6`, `core id 0..5` |
| **CPU cores físicos totales** | **12** | 2 sockets × 6 |
| Procesadores lógicos enumerados | **12** | `processor: 0..11`; un hilo por core en la captura |
| Cache L3 informada | 15.360 KB por CPU | `cache size` |
| CPU ISA observada | SSE4.1/SSE4.2, AVX, AVX2, FMA, AES, BMI1/BMI2 | `flags` |
| RAM visible | **31 GiB** | `free -h` |
| Swap | 8,0 GiB | `free -h` |
| Memoria en /home | 116,81 GB de volumen según cabecera | indicador de sesión, no requisito normativo de disco |
| GPU NVIDIA | **GeForce RTX 2080 Ti, una unidad** | `nvidia-smi` |
| **VRAM GPU** | **11.264 MiB** | `nvidia-smi` |
| Driver NVIDIA | **535.288.01** | `nvidia-smi` |
| CUDA Version en NVIDIA-SMI | **12.2** | `nvidia-smi`: nivel máximo soportado por driver; NO versión demostrada de nvcc |
| CUDA toolkit / nvcc | **DESCONOCIDO** | el archivo NO incluye `nvcc --version` |
| GCC/Make | **DESCONOCIDO** | el archivo NO incluye `gcc --version` ni `make --version` |
| Estado SSH | Acceso SSH directo y X11 forwarding mediante cliente MobaXterm | cabecera, datos de red omitidos por privacidad |

## Datos de GPU completados con documentación NVIDIA (no impresos por nvidia-smi)

| Propiedad | RTX 2080 Ti | Fuente adicional |
|---|---:|---|
| Núcleos CUDA FP32 físicos | **4.352** | tabla oficial NVIDIA GeForce: https://www.nvidia.com/es-es/geforce/graphics-cards/compare/ |
| Multiprocesadores SM | **68** | documentación Turing: https://images.nvidia.com/aem-dam/en-zz/Solutions/geforce/turing/nvidia-turing-architecture-whitepaper.pdf |
| Núcleos CUDA por SM | 64 | 4.352 / 68 |
| Compute Capability | **7.5 (sm_75)** | https://developer.nvidia.com/cuda/gpus |

**Distinción crucial:** el usuario exige como mínimo **12 núcleos físicos CPU y 4.352 CUDA cores GPU**. Los 68 SM se conservan como información de referencia; **no** se exige como mínimo adicional el número de SM porque un SM Ada/Ampere/Blackwell puede agrupar más núcleos FP32 que un SM Turing. El campo `sm_min=68` es informativo mientras `require_sm_parity=false`. El candidato debe tener >= 11.264 MiB VRAM usable y al menos 31 GiB RAM, además de ejecutar código CUDA correctamente.

## Condiciones de software y compatibilidad

El servidor UCAM ejecuta **x86-64**. Aunque ya no se exige Debian, para probar de forma más directa se prefiere inicialmente Ubuntu 22.04 LTS en AWS con GCC, Make, nvcc y driver NVIDIA compatible, todos con versión fijada. No confundir controlador `535.288.01` con Toolkit 12.2 realmente instalado.

- `nvcc` en AWS debe generar un binario **para GPU AWS** (por ejemplo `sm_89` en NVIDIA L4).
- También debe poder generar código **para la RTX 2080 Ti de la UCAM (`sm_75`)**, usando un Toolkit compatible, y demostrar su ejecución en el servidor UCAM; solo generar el binario no demuestra la ejecución remota.
- La compatibilidad de **código fuente** C/CUDA se valida ejecutando los mismos tests en ambas máquinas; no se exige usar exactamente los mismos binarios CUDA, driver o número de SM.
- Programas con características exclusivas de GPU moderna deben tener una vía compatible con Turing o ser rechazados como no portables a la referencia.
- Los 12 cores de la UCAM son físicos; una EC2 con 12 vCPU que representa 6 cores físicos NO es equivalente.
- Si el usuario cambia requisitos, actualizar este archivo, config/hardware-base.json, selección de instancias, tests y reglas de pricing.

## Datos pendientes de medir y certificados por ejecución

1. En el servidor UCAM: `gcc --version`, `make --version`, `nvcc --version`, `nvidia-smi --query-gpu...` y `cudaDeviceProp`.
2. Pruebas de C y CUDA representativas ejecutadas en UCAM con logs y resultados.
3. En cada AMI AWS admitida: número real de cores CPU visibles (`lscpu`), CUDA cores atribuibles por modelo de GPU completa, VRAM usable, Toolkit/driver y test real CUDA.
4. Certificar la portabilidad y comparar resultados. Solo entonces marcar `status=VERIFIED` y aportar `evidence/validated-inventory.json`.

**No consta ninguna ejecución real del código CUDA del repositorio en el servidor UCAM ni en AWS a la fecha de este documento.**
