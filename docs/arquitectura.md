# Arquitectura objetivo — Linux/C/CUDA + SSH + GitHub Actions efímero

## 1. Dos planos separados

**Desarrollo interactivo:** EC2 Linux con GPU adecuada y AMI versionada, SSH con clave pública y Security Group limitado a IP administrada o Session Manager, directorio y EBS controlados. Apagar por inactividad; no registrar esta máquina como runner público.

**CI (push autorizado):** GitHub Actions -> webhook firmado workflow_job -> API Gateway + Lambda -> cola/estado (SQS/DynamoDB o controlador Terraform auditado) -> consulta selector AWS -> RunInstances Spot -> cloud-init/AMI prevalidada -> runner just-in-time --ephemeral -> GCC/nvcc/test -> GitHub job logs y artefactos + CloudWatch -> terminación EC2 y desregistro runner.

## 2. Eventual controlador GitHub/AWS

1. Autenticar GitHub App con permisos mínimos y verificar X-Hub-Signature-256 sobre body crudo. Aceptar solo el repo skyirim/prueba-cuda, evento workflow_job queued, nombre de workflow y etiquetas GPU autorizadas. Webhook puede repetirse; deduplicar delivery ID / job ID.
2. Antes de llamar a EC2, leer perfil base firmado/validado y catálogo de AMIs con certificación; fallo cerrado si no hay perfil o la imagen/instancia no satisface hardware. Exigir cuotas, máximo de VMs concurrentes, budget, lista blanca regiones y zonas.
3. Solicitar Spot con strategy adecuada y fallback entre AZ permitidas, sin elegir "menor coste" si la capacidad no existe. **No cambiar de familia/arquitectura silenciosamente**; etiquetar todos los recursos con proyecto/job/run_id/expiry.
4. Solo al crear la VM se obtiene token JIT efímero de GitHub, por identidad de máquina autorizada; nunca inyectar PAT persistente. Usar IMDSv2, rol de instancia mínimo, AMI inmutable probada, EBS cifrado y logs externos.
5. Runner consume 1 trabajo; GitHub registra stdout/stderr por step, código de salida y artefactos publicados siempre que host viva. CloudWatch recoge cloud-init y registros de runner desde el inicio, incluso si nunca conecta a GitHub.
6. Al completarse job, expiración o Spot interruption, terminar instancia, EBS efímero y tokens; watchdog independiente (EventBridge + Lambda o mecanismo equivalente), con alerta en fallo.
7. No lanzar directamente workflow al recibir push en webhook sin verificar trusted ref/labels. Los PR de forks no deben usar runners con roles AWS ni tokens de escritura.

## 3. Línea base de seguridad

- GitHub App, secretos en Secrets Manager, log de acceso a eventos. AWS desde GitHub con OIDC acotado al repo/rama/environment y permisos mínimos, nunca root.
- VPC, subnet y SG restringidos; para CI preferentemente sin 22 abierto. SSH solo en modo dev y desde IPs conocidas, no 0.0.0.0/0.
- No almacenar claves SSH privadas en GitHub, AMI, logs ni repositorio. SSM Session Manager cuando posible.
- Límite de tiempo 30 min inicial ampliable tras benchmarking, máximo concurrente 1, presupuesto y etiqueta TTL. No suponer que timeout del job apaga una EC2: watchdog separado.
- NVIDIA GRID solo con licencia/versión soportada para G6f; probar Amazon Linux 2023 o Ubuntu. La compatibilidad Debian no se da por supuesta.
- IAM de controlador solo poder crear/terminar recursos marcados y pasar el rol preciso; revisar protección ante escalada y configuración de GitHub workflow permissions.

## 4. Riesgos y criterios de fin

| Riesgo | Mitigación |
| --- | --- |
| Sin archivo base | Bloquear equivalencia y GPU automático |
| GPU fraccionada sin cores equivalentes | Excluirla y elegir GPU completa |
| Spot insuficiente/cuota cero | Reintentos limitados, error visible, no facturación alternativa oculta |
| Imagen/driver incompatibles | AMI probada por smoke CUDA y checksum |
| Worker detenido antes de subir logs | Envío externo CloudWatch y diagnóstico de controlador |
| Runner queda vivo y factura | TTL obligatorio, watchdog independiente, alarma |
| Ataque por PR externo | No ejecutar código de fork en runner privilegiado |
| Desviación de versiones CUDA / GPU | Matriz, pins, pruebas en equipo base y destino |

**Estado: arquitectura propuesta; no está desplegada.** Tras aprobación del perfil de referencia, implementar con Terraform versionado y pruebas de destrucción.


## 5. Selector de precios en tiempo de arranque (obligatorio)

Entre recibir un job y pedir EC2, ejecutar selección fresca **inmediatamente antes de cada nueva instancia**: consulta actual de `DescribeInstanceTypes`, `DescribeSpotPriceHistory` y cuotas regionales, filtrado de GPU y CPU según [UCAM](hardware-base.md), consideración de regiones/AZ y AMIs certificadas, ordenación por coste real. El precio de un runner previo no sirve para otro push; tampoco sirve el precio documentado el día de creación de la AMI.

TTL máximo del plan 60 segundos. Revalidar en el instante de `RunInstances`; si expira reconsultar; ante rechazo Spot reconsultar y seleccionar otra opción sin degradar. Registrar cotización UTC exacta y AWS request IDs de los eventos de lanzamiento y limpieza. Recurso de control y máquina de desarrollo por SSH siguen la **misma regla**. [Implementación de referencia de selector](../infrastructure/select_gpu_spot.py).

**Actualmente no existe un controlador en producción que haga RunInstances automáticamente**; el selector es un componente comprobable para incorporarlo a ese controlador.
