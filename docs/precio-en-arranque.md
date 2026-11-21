# Política permanente: consultar AWS al levantar CADA instancia

Fecha de política: 2026-11-21. Aplica a **cualquier** máquina EC2 para desarrollo remoto SSH, compilación, pruebas o GitHub Actions.

## Fuente de verdad y restricciones

Referencia UCAM: `config/hardware-base.json`; documento original `Informacion_servidor_Programacion_Paralela_UCAM-2026.txt`, SHA-256 `07a5105d27c18ffd3caa464054885187d93a65b0240d4804d0efae910c349f8f`. 12 núcleos físicos CPU, 4.352 cores CUDA en una GPU completa, 31 GiB RAM, 11.264 MiB VRAM, Ubuntu x86-64 + RTX 2080 Ti sm_75. Los 68 SM son informativos y NO mínimo separado. `nvidia-smi CUDA Version:12.2` no acredita versión nvcc instalada.

## Contrato de selección justo antes de RunInstances

1. Controlador recibe solicitud *para una sola instancia* y catálogo de pools con **AMI Linux, CUDA, driver, prueba GPU AWS y prueba de portabilidad UCAM** aprobados. Si no hay evidencias, bloquear (config/approved-gpu-pools.json empieza vacío).
2. Mediante SDK AWS consulta de nuevo `DescribeInstanceTypes` por región, sin inferir cores físicos de vCPU; descarta CPU <12, GPU con menos de 4.352 CUDA cores acreditados, fracción o VRAM <11.264 MiB, RAM <31 GiB, arquitectura/driver o CUDA incompatibles.
3. Consulta **en ese instante** `ServiceQuotas.GetServiceQuota` (Spot G/VT) por región; descarta aquellas sin cuota suficiente. En producción debe **descontar además otros Spot G/VT en uso**, evitar carreras con un bloqueo de concurrencia y verificar habilitación de región y perfiles de AMI/subred.
4. Para todas las (tipo, AZ) de pools técnicamente válidos, consulta en directo `DescribeSpotPriceHistory` paginado: última cotización por (tipo, AZ), no mínimo histórico. Precio histórico de README/CSV/JSON JAMÁS decide el lanzamiento.
5. Ordena por **precio Spot más costes adicionales estimados** (EBS, IP, registros, tiempo de arranque); calcula coste por job con duración real. Opcionalmente pondera eficiencia por tiempo medido, pero nunca toma un tipo incompatible por ahorrar.
6. Devuelve un plan **válido menos de 60 segundos**. El controlador tiene que verificar `assert_fresh(plan)` y preferentemente volver a llamar `select()` inmediatamente antes de `ec2:RunInstances`. Si el plan expiró, la API falla o cuota no basta, **fallo cerrado**: ninguna instancia.
7. Spot no garantiza capacidad. Si AWS rechaza solicitud por capacidad/precio/limitación, log y nueva consulta, seleccionar siguiente oferta **compatible**. Prohibido bajar recursos, usar otro sistema sin validar o activar On-Demand sin aprobación y límite de coste explícito.
8. Guardar hora UTC, región/AZ, imagen, SKU/tipo, CPU/GPU, precios actualizados, alternativas, cuotas, CID de control y acciones de limpieza. Nunca guardar secretos/identificadores privados en el repo.
9. **Cada nuevo push o nueva sesión SSH repite TODO el proceso desde el principio**. No conservar selección entre trabajos ni usar resultados de auditoría mensual.
10. Terminar la VM y EBS efímero al finalizar, con watchdog independiente y alertas; registrar consumo real.

El código Python [select_gpu_spot.py](../infrastructure/select_gpu_spot.py) implementa el filtrado de tipo, recursos, cuota G/VT y lectura fresca de Spot para pools ya certificados. **Es un selector de solo lectura**, NO un creador de máquinas, y actualmente los pools están vacíos. Para despliegue habrá que integrar el motor en el controlador real, comprobar cuotas ya consumidas, acceso a AMI por AZ, concurrencia, resiliencia ante Spot unavailable y test de principio a fin de `RunInstances` y terminación. No declarar que el sistema esté automatizado todavía.

## Comprobación y pruebas

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_repo.py
python3 infrastructure/select_gpu_spot.py \
  --baseline config/hardware-base.json \
  --pools config/approved-gpu-pools.json
```

El tercer comando **debe fallar** mientras el baseline esté en DRAFT o no haya pools certificados. Ese error es intencionado y protege ante facturación o ejecución no compatible.

Los tests unitarios comprueban el selector puro sin lanzar AWS, verificando cuotas, orden de precios, rechazo de GPU fraccionada, CPU insuficiente y caducidad. Hasta validar una AMI y ejecutar código CUDA en ambos equipos, **no hay equivalencia demostrada**.

Fuentes AWS:
- https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSpotPriceHistory.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-best-practices.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-optimize-cpu.html

## Fotografía del 21-11-2026 — NO UTILIZAR PARA LANZAMIENTO

Oregón, con cuota Spot G/VT 126 vCPU en la consulta: gr6.8xlarge (16 cores CPU, L4 completa, 7.424 CUDA cores) **0,4929 USD/h** en us-west-2c; g7.4xlarge 0,7658; g6.8xlarge 0,8391; g5.8xlarge 0,8438. Es un resultado histórico del análisis; al arrancar se debe volver a preguntar AWS.
