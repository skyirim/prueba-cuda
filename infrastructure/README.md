# Infraestructura AWS — estado NO DESPLEGADA

El repositorio documenta una arquitectura reproducible, pero **no contiene Terraform aplicable** porque falta la ficha técnica del equipo base. Ninguna EC2, volumen, GitHub App, OIDC, webhook o permiso se ha creado en esta fase. No ejecutar scripts de aprovisionamiento improvisados.

## Componentes planificados (Terraform/Packer u herramienta equivalente)

- AMI base oficial Linux aprobada por familia/arquitectura, con receta versionada de drivers NVIDIA (GRID para G6f), CUDA, gcc, GitHub Runner y CloudWatch/SSM; verificación nvidia-smi y smoke CUDA.
- VPC y subredes permitidas, SG sin SSH público para runner CI; perfil SSH independiente con acceso acotado.
- Controlador con GitHub App y webhook workflow_job autenticado, deduplicación, cola/estado, función de aprovisionamiento y watchdog separado de terminación/TTL.
- IAM mínimo para cada componente; secretos solo en AWS Secrets Manager/entorno seguro, OIDC de GitHub cuando corresponda.
- Parámetros de costo: región, máximo de 1 runner inicial, timeout, tipos de instancia permitidos tras equivalencia, máximo Spot y presupuesto AWS; nunca consumir On-Demand sin límite/consentimiento.
- CloudWatch con política de retención y logs de cloud-init, nvidia-smi y runner antes del registro GitHub.
- Scripts de test de fallos (Spot unavailable, bootstrap, revocación, pérdida de red, timeout), con evidencia de limpieza de EBS/EC2/runner.

## Criterios para crear los ficheros IaC

1. Transcribir equipo base de fuente original; completar config/hardware-base.json.
2. Medir y verificar si G6f (fraccionada) cumple sus cores o seleccionar GPU completa que cumpla.
3. Elegir e instalar AMI validada; guardar ID y receta reproducible con hashes.
4. Generar Terraform pinneando módulos y proveedores; adjuntar terraform fmt/validate/plan en PR.
5. Aprobación explícita para costos y despliegue; aplicar en cuenta/region y hacer smoke test.
6. Activar plantilla templates/cuda-gpu-workflow.yml solo cuando el controlador y la terminación autónoma estén probados.
7. Para rollback, desactivar webhook, detener/controlar solicitudes, destruir EC2/EBS y revisar consumo residual.

Guías relacionadas: docs/arquitectura.md, docs/seguridad.md, docs/implementacion.md y docs/operacion.md.
