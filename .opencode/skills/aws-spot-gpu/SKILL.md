---
name: aws-spot-gpu
description: Investiga costes y disponibilidad AWS de instancias NVIDIA GPU para C/CUDA, con precios Spot y On-Demand, cuotas, arquitectura, VRAM y seguridad.
---

# Investigación de tarifas AWS GPU

1. Leer README.md, AGENTS.md, docs/aws-investigacion.md, docs/hardware-base.md y ADR-0001.
2. Consultar fecha UTC, account/region solo en consola (no publicar IDs), AWS EC2 DescribeInstanceTypes, DescribeSpotPriceHistory (paginado y último dato por AZ/tipo), Service Quotas y Price List AmazonEC2.
3. Excluir GPU AMD G4ad para CUDA NVIDIA; separar CPU arm64/x86-64, NVIDIA GPU completa/fraccionada y requisitos de la ficha base.
4. No permitir comparar coste de máquinas que no demuestran recursos CPU/GPU suficientes.
5. Comprobar cuota regional y habilitación de región; no confundir precio publicado con capacidad real.
6. Calcular coste total por job incluyendo overhead, EBS, IPv4, logs, controller y reintentos; comparar contra duración medida.
7. Registrar evidencia (tipo, región, AZ, UTC, API, importe), fallos, fuentes oficiales y presupuesto.
8. Proponer PR con recomendación y excepciones, sin lanzar AWS ni compromisos financieros sin autorización.


## PRICE-LAUNCH-11 — obligatorio por instancia (21-11-2026)

1. Antes de **cada** RunInstances, releer [docs/hardware-base.md](../../../docs/hardware-base.md) y ejecutar consulta actual AWS con selector [infrastructure/select_gpu_spot.py](../../../infrastructure/select_gpu_spot.py), nunca precios documentados previamente.
2. CPU>=12 núcleos físicos, UNA GPU completa con CUDA cores>=4.352, RAM>=31 GiB, VRAM>=11.264 MiB; sm_75 para el código de UCAM, GPU destino propia compatible.
3. Verificar AMI/driver/CUDA certificada, regiones/AZ permitidas, cuota Spot y coste total; precio por AZ tipo con última cotización. Plan caduca <=60 segundos; si demora, reconsultar.
4. Si no hay cuota, precio, GPU compatible o AMI certificada, no arrancar. Spot unavailable: reconsulta y próxima oferta que cumpla todos los requisitos; nunca degradar.
5. Registrar todas las alternativas/cotizaciones/descartes y evidencia UTC en el PR y logs de job. Repetir por cada nuevo push, no usar la auditoría mensual como selección.
