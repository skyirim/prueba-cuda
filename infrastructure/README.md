# Infraestructura AWS — estado NO DESPLEGADA

El repositorio documenta una arquitectura reproducible, pero **no contiene Terraform aplicable** porque falta ejecutar y certificar los programas C/CUDA en el servidor UCAM y en una AMI AWS validada, y no se ha desplegado todavía el controlador. Ninguna EC2, volumen, GitHub App, OIDC, webhook o permiso se ha creado en esta fase. No ejecutar scripts de aprovisionamiento improvisados.

## Componentes planificados (Terraform/Packer u herramienta equivalente)

- AMI base oficial Linux aprobada por familia/arquitectura, con receta versionada de drivers NVIDIA (GRID para G6f), CUDA, gcc, GitHub Runner y CloudWatch/SSM; verificación nvidia-smi y smoke CUDA.
- VPC y subredes permitidas, SG sin SSH público para runner CI; perfil SSH independiente con acceso acotado.
- Controlador con GitHub App y webhook workflow_job autenticado, deduplicación, cola/estado, función de aprovisionamiento y watchdog separado de terminación/TTL.
- IAM mínimo para cada componente; secretos solo en AWS Secrets Manager/entorno seguro, OIDC de GitHub cuando corresponda.
- Parámetros de costo: región, máximo de 1 runner inicial, timeout, tipos de instancia permitidos tras equivalencia, máximo Spot y presupuesto AWS; nunca consumir On-Demand sin límite/consentimiento.
- CloudWatch con política de retención y logs de cloud-init, nvidia-smi y runner antes del registro GitHub.
- Scripts de test de fallos (Spot unavailable, bootstrap, revocación, pérdida de red, timeout), con evidencia de limpieza de EBS/EC2/runner.

## Criterios para crear los ficheros IaC

1. Equipo base transcrito desde archivo UCAM recibido: >=12 cores CPU físicos y >=4.352 CUDA cores. Completar medidas y pruebas reales UCAM/AWS y certificar config/hardware-base.json.
2. Medir y verificar si G6f (fraccionada) cumple sus cores o seleccionar GPU completa que cumpla.
3. Elegir e instalar AMI validada; guardar ID y receta reproducible con hashes.
4. Generar Terraform pinneando módulos y proveedores; adjuntar terraform fmt/validate/plan en PR.
5. Aprobación explícita para costos y despliegue; aplicar en cuenta/region y hacer smoke test.
6. Activar plantilla templates/cuda-gpu-workflow.yml solo cuando el controlador y la terminación autónoma estén probados.
7. Para rollback, desactivar webhook, detener/controlar solicitudes, destruir EC2/EBS y revisar consumo residual.

Guías relacionadas: docs/arquitectura.md, docs/seguridad.md, docs/implementacion.md y docs/operacion.md.


## Selección de precio por instancia

El código [select_gpu_spot.py](select_gpu_spot.py) implementa un **selector Spot de solo lectura** para AMIs/pools certificados. La lista de pools en [config/approved-gpu-pools.json](../config/approved-gpu-pools.json) está vacía: no es correcto activarla antes de pruebas CUDA en UCAM y AWS. En el futuro, el controlador de arranque deberá llamar al selector AWS justo antes de **cada** RunInstances y comprobar TTL máximo 60 s. Ningún despliegue debe saltarse el filtro de CPU físicos>=12, CUDA cores>=4.352, RAM>=31 GiB y VRAM>=11.264 MiB. [Proceso detallado](../docs/precio-en-arranque.md).


## Estado real de AWS (21-11-2026)

La plantilla CloudFormation de base **sí** está desplegada (prueba-cuda-ci, CREATE_COMPLETE, us-west-2). No existen EC2 GPU activas. Un intento de calificación con RunInstances devolvió error Blocked: AWS considera la cuenta no validada. Los scripts CI y las reglas siguen preparados pero inactivos hasta desbloqueo, configuración de variables GitHub y pruebas reales. [Seguimiento #7](https://github.com/skyirim/prueba-cuda/issues/7). Los apartados históricos anteriores de este documento reflejan el estado previo al despliegue.
