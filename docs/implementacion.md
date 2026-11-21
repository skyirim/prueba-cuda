# Plan reproducible de implantación por fases

## Fase 0 — hardware fuente disponible, verificación de ejecución PENDIENTE

- Fichero base UCAM recibido el 21-11-2026, identificado mediante SHA-256. Configurado config/hardware-base.json con CPU >=12 cores físicos, NVIDIA >=4.352 CUDA cores, RAM >=31 GiB, VRAM >=11.264 MiB. Falta comprobar el Toolkit instalado y ejecutar pruebas reales en UCAM.
- Identificar número de cores **físicos** CPU, CUDA cores disponibles y SM, GPU completa vs virtualizada, VRAM, arquitectura de CPU, compute capability, SO/driver/CUDA, apps, librerías y formas de ejecución.
- Determinar si se exige misma ISA/binario o portabilidad de código fuente. Aprobar pruebas equivalentes ejecutables en base y nube.
- Con requisitos numéricos documentados pero sin pruebas C/CUDA cruzadas ni AMI certificada: mantener CI GPU deshabilitado. No declarar garantizada la portabilidad.

## Fase 1 — investigación y selección coste/capacidad

1. Ejecutar consultas docs/aws-investigacion.md (fecha, regiones, tipos, Spot reciente por AZ, On-Demand, cuotas G/VT, imagen Linux compatible, presupuesto).
2. Filtrar por todos los mínimos UCAM: >=12 cores físicos, >=4.352 CUDA cores de una GPU completa, >=11.264 MiB VRAM, >=31 GiB RAM, CUDA sm_75 portable. G6f y G5g pequeñas quedan descartadas; no sumar cores de GPUs ni vCPU como cores físicos.
3. Estimar coste desde encendido hasta destrucción; añadir EBS, IPv4, logs, imágenes, contingencias; comparar USD por compilación correcta.
4. Registrar ADR para la elección final, con versiones de sistema/toolchain, precios, AWS región/AMI y opciones rechazadas. Antes de **cada** EC2 RunInstances, ejecutar selector de precios/cuotas de AWS en tiempo real (TTL <=60 segundos) y registrar la tarifa escogida.

## Fase 2 — fabricar AMI probada

1. Elegir AMI arm64 o x86-64 Linux desde propietario/firmas legítimos; inicialmente Amazon Linux 2023 o Ubuntu para G6f y distro compatible para GPU completa; fijar IDs **por región y arquitectura**, sin usar AMI x86 en arm64.
2. Con constructor reproducible (Packer/EC2 Image Builder), instalar git, gcc, make, cmake, Python, runner ARM64/x64, agente CloudWatch/SSM, NVIDIA GRID/Tesla según familia, CUDA toolkit compatible y versionado.
3. Driver G6f: seguir https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-GRID-driver.html ; no aplicar guías Tesla genéricas a GPUs fraccionadas.
4. Ejecutar uname -m, lscpu, gcc --version, nvcc --version, nvidia-smi, y compilar src/cuda_smoke.cu. Ejecutar el binario sobre la GPU y comparar resultados.
5. Recopilar salida de GPU SM, RAM/VRAM y compute capability; completar perfil medido con evidencia de CUDA cores efectivos cuando se justifique. Sellar AMI con versión/fecha y hash de receta.
6. No distribuir imagen a otras cuentas sin revisión de licencias. No guardar secretos ni ficheros de usuario en AMI.

## Fase 3 — seguridad, acceso SSH y controlador

1. Definir Terraform para red/SG, IAM mínimos, GitHub App, webhook firmado, controlador y backend de estado; versionar código **sin secretos**.
2. Implementar IAM roles scoped, OIDC/Secret Manager, IMDSv2, EBS cifrado, tags y destrucción independiente. No usar credenciales de root.
3. Validar firmas, audiencia y origen del evento; que solo jobs de rama y etiqueta autorizados puedan solicitar GPU.
4. Configurar acceso SSH exclusivamente al perfil dev, limitando CIDR; usar claves y, de preferencia, Systems Manager. No abrir 22 en runner CI.
5. Fijar coste máximo, región/zonas permitidas, número máximo de instancias y TTL; documentar fallback Spot y límites.

## Fase 4 — GitHub Actions

- Activar plantilla templates/cuda-gpu-workflow.yml **solo después** de pruebas y permisos. Renombrar/copiar bajo .github/workflows cuando el controlador ya esté listo.
- No confiar en que un workflow lanzado en self-hosted cree su propia máquina: hace falta el controlador independiente.
- Si hay Makefile de usuario, ejecutar objetivos all/test con pipefail y tee; subir artefactos con if:always; CloudWatch para errores previos a registro GitHub.
- Mantener docs-check.yml ligero en GitHub-hosted, sin GPU ni AWS.

## Fase 5 — prueba de extremo a extremo y aceptación

1. Probar workflow documental en push y PR.
2. Ejecutar caso C y caso CUDA, registrar logs de compiler/runtime, inventario, SHA y versión AMI.
3. Repetir casos representativos en equipo base y nube; comparar resultados y restricciones. Sin equipo base disponible, no declarar equivalencia garantizada.
4. Forzar error gcc, error nvcc, fallo GPU, fallo de webhook, IAM AccessDenied, cuota cero, Spot unavailable, interrupción Spot y timeout.
5. Comprobar que el job reporta error, logs disponibles en GitHub y CloudWatch, instancia terminada y EBS borrado. Revisar facturación después.
6. Abrir PR de habilitación GPU con evidencia; revisión humana de costes/seguridad, aprobación y cambio controlado.

## Despliegue y rollback

- Antes de desplegar: plan de Terraform y estimación, verificación de roles/recursos; aprobación explícita.
- Después: prueba con solo 1 runner y tiempo máximo pequeño; monitorización.
- Rollback: desactivar webhook/controlador, cancelar solicitudes, terminar instancias marcadas, desregistrar runners, revisar volúmenes/SG/secrets, conservar logs.
- No se considera terminado hasta verificar ausencia de instancias, IP públicas, volúmenes huérfanos y cobros inesperados.


## Fase implementada como artefactos reproducibles (pendiente de despliegue)

Se añadieron [CloudFormation](../infrastructure/cloudformation/gpu-ci-base.json), [workflow GitHub](../.github/workflows/aws-gpu-ci.yml), [controlador Python](../scripts/aws_gpu_job.py) y [scripts Linux](../scripts/ci). Tras configurar OIDC, permisos, una AMI y pruebas de referencia, se podrán crear EC2 Spot bajo demanda con fases independientes de GCC/nvcc, ejecutar kernels reales, guardar registros íntegros, publicar artifacts y terminar automáticamente las VMs. El modo manual qualify permite comprobar la AMI sin habilitar push automático ni marcarla VERIFIED. El modo SSM no es un runner self-hosted de GitHub registrado. Para los pasos de activación, ver [docs/aws-gpu-ci.md](aws-gpu-ci.md).
