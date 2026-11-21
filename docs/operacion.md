# Operación, diagnóstico, observabilidad y presupuesto

## Trazabilidad de cada job

Publicar commit SHA, run ID, job ID, perfil hardware de referencia hash, AMI ID, tipo EC2, AZ, clasificación GPU física/fraccionada, kernel/OS, gcc, nvcc, driver, GPU nvidia-smi, pruebas y artefactos. Redactar secretos, IPs privadas, credenciales y datos sensibles. Logs de GitHub son fuente principal de steps ejecutados; logs EC2 cloud-init, ssm y runner a CloudWatch explican fallos antes de que la máquina conecte.

## Diagnóstico por síntomas

| Síntoma | Verificación | Acción |
| --- | --- | --- |
| Job en cola sin runner | Webhook workflow_job, firma, controlador, cuota G/VT, capacidad Spot, región | Ver error; no ampliar coste automáticamente |
| Instancia pending o falla bootstrap | EC2 state reason, cloud-init, SG/egress, AMI architecture | Terminar si TTL; corregir receta |
| nvidia-smi falla | Kernel, GRID/Tesla correcto, Secure Boot y módulos | Reconstruir AMI, no parchear producción a ciegas |
| nvcc not found | PATH, versión toolkit, arquitectura binario | Reconstruir AMI reproducible |
| no CUDA device / invalid device function | driver, GPU visible, compute capability, -gencode | Ajustar build, reproducir y registrar |
| out of memory | VRAM disponible, memoria GPU requerida, fracciones G6f | GPU mayor o reducir datos sin romper requisitos |
| Tests diferentes respecto al base | ISA, precisión, concurrencia, límites | Investigar causa y test regresión |
| Logs GitHub incompletos | Falló antes de registro o Spot interruption | Recuperar CloudWatch desde boot |
| Instancia queda activa | TTL/tag, watchdog, eventos terminación | Terminar recursos marcados y abrir incidente |

## Comandos diagnósticos en máquina

~~~bash
date -u +%FT%TZ
uname -a
lscpu
free -h
gcc --version
nvcc --version
nvidia-smi -q
sudo journalctl -u cloud-init -u cloud-final --no-pager || true
~~~

Para recolectar inventario físico de vCPU/cores, confirmar con la topología de EC2 (vCPU no siempre equivalen a núcleos físicos dedicados). CloudWatch puede incurrir coste; definir retención corta y presupuestos.

## Gestión de coste y límites

- Alertar por presupuesto mensual, ejecución > tiempo máximo, instancias > límite y recursos sin etiqueta TTL.
- No eliminar logs críticos antes de depurar, pero fijar retención y no publicar datos secretos.
- Coste total = EC2 Spot/OnDemand (tiempo real) + EBS + snapshots/AMI + IPv4 + transferencia + controlador + registros + reintentos.
- Nunca contratar EC2 Reserved/Savings Plans solo para "ahorrar" en un runner efímero sin evaluación de horas comprometidas.
- Revisar precios/compatibilidad al cambiar infraestructura y en revisiones periódicas mediante PR; el workflow de docs no consulta APIs de pago.

## Incidentes

En pérdida de capacidad GPU: registrar Spot unavailable/insufficient capacity, deduplicar trabajo, reintentar con límite y fallback compatible previamente aprobado. Si no hay familia equivalente, fallar y notificar; no usar un GPU insuficiente para simular éxito.

## Revisión periódica

Mensualmente o con cambios de proveedor: cotizaciones Spot, cuotas por región, driver GRID, toolkit CUDA, versiones de acciones GitHub, AMI seguridad y eficiencia. Crear PR con datos fechados, comparar con último estado y evidencias; no actualizar comportamiento automáticamente sin pruebas.
