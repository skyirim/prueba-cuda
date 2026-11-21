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
