# Seguridad de GitHub Actions, AWS, SSH y datos

## Identidades y acceso

- GitHub App con permisos mínimos para recibir workflow_job y registrar runners; secretos fuera de código y AMI.
- Controlador AWS autentica y autoriza la procedencia del webhook (HMAC SHA-256), admite solo skyirim/prueba-cuda y ramas/labels confiables; comprueba cada evento, deduplicación y replay.
- Para CI desde GitHub a AWS preferir OIDC federado condicionado por repo, branch y audiencia sts.amazonaws.com; no credenciales IAM permanentes.
- Roles EC2 mínimo para SSM/CloudWatch y recursos de inicio autorizados; evitar iam:PassRole sobre * y privilegios de root.
- VPC/SG mínimo. Runner CI sin puerto 22 público; SSH dev restringido a IP explícita, sólo claves, sin contraseñas. Session Manager recomendado.
- IMDSv2 requerido, EBS cifrado y eliminado al terminar CI, sin snapshots conteniendo secretos.

## Riesgo principal de runners self-hosted

Son máquinas que ejecutan código del repositorio y Makefiles: ese código puede ser malicioso. No alojar runners duraderos, no dar permisos AWS de control de EC2 al proceso de compilación, no usar pull_request_target con código no confiable y secretos. Proteger ramas, revisiones y releases de acciones fijadas por SHA.

## Daños económicos

Configurar límite de runners y presupuesto, alertas y terminación independiente. Un cancel de workflow no sustituye el cierre EC2; probar fallo de webhook, interrupción y pérdida de red. No habilitar fallback On-Demand sin máximo de precio y aprobación.

## Validación de versiones

- G6f: solo NVIDIA GRID compatible; validar OS/driver según https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-GRID-driver.html y https://docs.nvidia.com/vgpu/cloud-service-support.html
- Fijar versiones AMI, CUDA, driver, Actions/runner con notas de compatibilidad; renovar solo tras test en GPU real.
- Documentar EULA aplicable y no publicar los binarios de controladores si su licencia lo prohíbe.

Referencias:
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_passrole.html


## Política económica de ejecución

El camino hacia `ec2:RunInstances` deberá validar un plan generado con consulta AWS **justo antes del arranque**, caducidad <=60 segundos y lista de imágenes/roles autorizados. No conceder a los jobs GitHub de usuario acceso al permiso RunInstances: es el controlador aislado quien consume el plan y arranca. No hay excepción para una sesión SSH de desarrollo. Si el selector falla o no hay imagen Linux CUDA certificada, **no provisionar**, aunque exista una tarifa Spot atractiva.
