# ADR-0001: equivalencia CPU/GPU basada en UCAM

Fecha: 2026-11-21
Estado: Política vigente, baseline documentado, pruebas cruzadas pendientes.

## Fuente y mínimos

Recibido el archivo `Informacion_servidor_Programacion_Paralela_UCAM-2026.txt` con hash SHA-256 `07a5105d27c18ffd3caa464054885187d93a65b0240d4804d0efae910c349f8f`. La referencia es Ubuntu 22.04.5 LTS/x86-64 con **dos Intel Xeon E5-2603 v4, 6 cores físicos cada uno = 12 cores**; 12 procesadores lógicos, 31 GiB RAM y **NVIDIA GeForce RTX 2080 Ti** con 11.264 MiB VRAM. NVIDIA acredita **4.352 núcleos CUDA, 68 SM y compute capability 7.5**. El `CUDA Version: 12.2` mostrado por `nvidia-smi` **NO** acredita la versión de `nvcc`.

## Decisión

El filtro de capacidad excluye instancias con **menos de 12 cores CPU físicos** o **menos de 4.352 CUDA cores FP32 por GPU completa**, menor RAM/VRAM o soporte insuficiente de CUDA/Turing. Una GPU fraccionada no puede acreditarse mediante la división teórica de cores sin evidencia de capacidad dedicada. Se exige **>= 1 GPU**; no sumar dos GPUs débiles para justificar que un kernel monodispositivo cumple el mínimo.

Los 68 SM del hardware UCAM son informativos; no imponer >=68 SM a un L4 de 58 SM que ofrece 7.424 CUDA cores. El requisito exige **número de CUDA cores**, no identidad de microarquitectura ni el mismo número de SM.

El código se compilará y probará para NVIDIA `sm_75` en el servidor UCAM y para la arquitectura de la GPU escogida en AWS; no suponer compatibilidad binaria entre GPU/CPU diferentes. Sin pruebas en ambas máquinas no existe garantía certificada.

## Opciones conocidas (instantánea 2026-11-21 Oregón)

- **gr6.8xlarge:** 16 cores CPU físicos (32 vCPU), NVIDIA L4 completa con 7.424 CUDA cores, 58 SM y ~22.888 MiB VRAM, 256 GiB RAM; Spot observado **0,4929 USD/h** en us-west-2c.
- **g7.4xlarge:** 16 cores físicos (16 vCPU), RTX PRO 4500 completa con 10.496 CUDA cores, 32 GiB VRAM, 64 GiB RAM; Spot 0,7658 USD/h en us-west-2c.
- **g6.8xlarge:** 16 cores físicos (32 vCPU), L4 completa; Spot 0,8391 USD/h en us-west-2a.
- **g5.8xlarge:** 16 cores físicos (32 vCPU), A10G completa con 9.216 CUDA cores; Spot 0,8438 USD/h en us-west-2a.
- **g6e.8xlarge:** 16 cores físicos (32 vCPU), L40S completa; Spot 1,9896 USD/h en us-west-2a.

Otras regiones pueden ser más baratas, pero en la cuenta consultada las cuotas Spot G/VT comprobadas eran cero fuera de Oregón. Las tarifas anteriores **NO se usarán para elegir instancias futuras**. Decisión de precio solo a la hora de lanzar, con consulta directa a AWS, cuotas actuales y pools probados.

No elegir `g6f.large`, `g6f.xlarge`, `g5g.xlarge` u otras máquinas anteriores: incumplen cores de CPU, GPU o ambos. **GR6.8 es candidata, no instancia ya certificada**, hasta demostrar compatibilidad CUDA real.

## Consecuencias

Se admite Ubuntu u otro Linux compatible. Un controlador obligatorio de precio en tiempo real debe seleccionar la oferta Spot más barata **entre tipos/AZ/regiones que cumplan requisitos y tengan AMI certificada, cuota y permisos**, justo antes de RunInstances; repetir si el tiempo excede TTL; no bajar requisitos ni activar On-Demand de forma oculta. La disponibilidad Spot no está garantizada.
