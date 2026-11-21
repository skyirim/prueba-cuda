# Instrucciones permanentes para agentes humanos, OpenCode y GitHub Copilot

Ámbito: todo el repositorio. **Leer README.md y AGENTS.md antes de investigar, editar, ejecutar, presupuestar o proponer infraestructura**. El README es el índice y la fuente de verdad del estado; una contradicción se resuelve mediante PR documental verificable, no ignorando el bloqueo.

## Reglas innegociables

1. **BASELINE-01, fuente obligatoria.** El TXT UCAM ya se recibió; leer docs/hardware-base.md y su SHA-256. Exigir >=12 núcleos CPU físicos, >=4.352 CUDA cores efectivos en UNA GPU NVIDIA completa, RAM >=31 GiB y VRAM >=11.264 MiB. No publicar usuario, IP ni hostname internos del TXT en este repositorio público. No declarar validada la ejecución en UCAM hasta realizarla.
2. **HARDWARE-02, conteos comparables.** Distinguir 12 CPU físicos de vCPU/SMT y 4.352 CUDA cores de 68 SM Turing. Los 68 SM no son requisito numérico separado: GPUs Ada/Blackwell tienen distinta densidad de cores por SM. Exigir GPU completa y no sumar GPUs débiles para el mínimo de una sola GPU; documentar cores FP32 reales según NVIDIA.
3. **COMPAT-03, prueba y portabilidad.** Compilar C con avisos estrictos y CUDA con arquitecturas objetivo; ejecutar tests y comparar resultados en AWS y la máquina base. Recompilar para CPU ISA diferente. No asumir que número de CUDA cores garantiza el mismo comportamiento, rendimiento, VRAM o funciones. Registrar compute capability, driver, toolkit, bibliotecas y pruebas de regresión.
4. **GATE-04, fail-closed.** La promoción a entorno VALIDADO exige baseline completo, inventarios, matriz y resultados reales. Si una prueba falta o es ambigua, falla; NO activar workflow GPU automático. CI documental puede funcionar sin GPU; no suprimir un fallo de equivalencia para obtener build verde.
5. **COST-05, minimizar coste verdadero.** Consultar precios Spot REALES, cuotas, zonas y capacidad **JUSTO ANTES DE CADA NUEVO ARRANQUE EC2**, tanto entorno SSH como CI, sin usar precios históricos del README o cache. Validar primero hardware/software UCAM, luego ordenar candidatos por el coste más económico, con EBS/IP/arranque. Si falla precio/cuota, no arrancar. Refrescar selección si plan >60 s, antes de RunInstances; Spot unavailable exige reconsulta y siguiente oferta válida. Prohibido fallback On-Demand no autorizado.
6. **SEC-06, identidad mínima.** AWS/GitHub por OIDC o GitHub App; sin credenciales duraderas en repo/logs/AMI. Webhooks firmados y acotados por repo/ref/etiquetas, IMDSv2, EBS cifrado, egress mínimo, SG restringidos. Nunca ejecutar pull_request_target con código no confiable y secretos; no ejecutar PR externos en runners privilegiados.
7. **LIFECYCLE-07, runner efímero.** Un runner por job, registro token corto, expiración dura y eliminación independiente incluso ante fallo del workflow, pérdida de red o Spot interruption; nunca usar la estación SSH como runner público.
8. **CHANGES-08, calidad y reproducibilidad.** PRs pequeños con matriz de requisitos, citas/fecha, tests, cambios de coste, riesgos, rollback, comprobación de logs, verificación de permisos. Markdown legible, C comentado técnicamente, Makefile con objetivos propios y limpieza sólo de sus productos.
9. **CURRENT-09, actualización responsable.** Antes de cambiar controlador NVIDIA, CUDA, AMI, arquitectura, versión de Actions o precios, leer fuentes primarias actuales, mantener tablas y ejecutar smoke tests. No actualizar versiones a ciegas. Si soporte baja, bloquear despliegue y emitir una incidencia.
10. **EVIDENCE-10, trazabilidad.** Diferenciar hecho verificado por API, dato publicado por proveedor, hipótesis y prueba pendiente. Registrar comandos, región, timestamp UTC, versión, resultado y enlaces a ejecuciones. Prohibido declarar "provisionado" o "garantizado" si sólo se redactó documentación.

## Proceso de cada cambio

1. Identificar tipo de cambio y cargar skill local adecuada: cuda-equivalencia, aws-spot-gpu o runner-efimero.
2. Revisar los datos de referencia y su estado. Si faltan, especificar bloqueo; sólo preparar documentación/infraestructura desactivada.
3. Describir impacto en CPU/GPU, seguridad, costes, rendimiento y portabilidad.
4. Ejecutar scripts/check_repo.py; para perfil completo ejecutar scripts/check_baseline.py con inventario real. Compilar y ejecutar C/CUDA en hardware real cuando se afirme compatibilidad.
5. Presentar logs y SHA/versiones en PR; **no fusionar con requisitos de equivalencia rotos**.
6. Ante cualquier cambio de AWS/GitHub, revisar la política de cuotas, costo máximo por ejecución, notificaciones, terminación y rollback.

## Prohibiciones

- No lanzar EC2 facturable, crear instancias persistentes, reservas, Savings Plans, Github App, webhooks o secretos sin una operación explícitamente autorizada y con límites de gasto y limpieza.
- No almacenar valores de tokens, claves SSH privadas, datos del cliente AWS, direcciones IP personales, ni cuenta AWS en archivos.
- No equiparar 1/8 de L4 a "1 GPU L4 completa" o declarar automáticamente un octavo de CUDA cores físicos.
- No suprimir controles para que las Action aparezcan verdes.
- No usar resultados de una prueba x86-64 para afirmar que un binario ARM64 ejecuta allí.

## Propuesta de mantenimiento

Cada push: validar formato/presencia y consistencia de documentación con CI barato. Actualizaciones de tarifas/versiones: revisiones fechadas, PR y validación humana; no ejecutar seguimiento de pago oculto. Cuando baseline esté completo, automatizar inventarios, controles de capacidades y regresiones CUDA como requerimientos para fusionar. Estos son requisitos documentados; **un AGENTS.md no despliega por sí mismo mecanismos AWS**.


## Regla permanente PRICE-LAUNCH-11: control no eludible del lanzamiento

- Todo agente, Terraform, Lambda, GitHub Action o script que cree EC2 con GPU debe llamar al módulo de selección [infrastructure/select_gpu_spot.py](infrastructure/select_gpu_spot.py) o implementación equivalente **evaluada automáticamente**, dentro de los 60 segundos previos a `RunInstances`.
- Para cada instancia nueva se vuelve a consultar AWS EC2 y cuota; no usar tablas estáticas. El registro de precios en `config/research-snapshot.json` sirve SOLO para investigación histórica.
- Excluir antes de comparar precios cualquier tipo que no cumpla [docs/hardware-base.md](docs/hardware-base.md), incluidos CPU físicos, CUDA cores de UNA GPU completa, VRAM/RAM, AMI Linux probada y compatibilidad `sm_75`.
- Recalcular todas las opciones elegibles por región/AZ y registrar motivo de exclusión de cada candidata. La falta de capacidad de la más barata no habilita a bajar recursos; pasar a la siguiente elegible, previa reconsulta.
- Nunca se presupone que «menor tarifa Spot» implica «capacidad Spot disponible»: la selección requiere gestionar solicitudes fallidas y limpieza. Costes por hora y por job separados.
- Mantener pruebas de regresión del filtro y del criterio de selección cada vez que cambie un requisito, GPU, Toolkit o AWS. El controlador no existe aún; esta norma queda ya almacenada para su implementación obligatoria.

## CODEX-REVIEW-12 — regla permanente de revisiones iterativas

**Ámbito: todas las ramas, commits, PR abiertos o fusionados y comentarios del repositorio.** Toda revisión del autor chatgpt-codex-connector (incluida la cuenta [bot]) debe examinarse, corregirse si procede, probarse, responderse y verificarse de nuevo hasta que los hallazgos estén resueltos.

1. Antes de empezar un cambio, antes de fusionar y después de cada corrección, consultar reviews generales, comentarios inline, hilos de revisión, comentarios de conversación/commit y resúmenes de Codex. Inspeccionar también revisiones en PR fusionados; una revisión COMMENTED puede contener P1.
2. Registrar cada hallazgo por URL/ID/commit/archivo/criticidad, reproducir el problema y diseñar un arreglo. Implementarlo en una rama/PR y añadir pruebas de regresión. No ocultar o silenciar errores ni desactivar tests.
3. Ejecutar los tests y comprobar el código; responder en el hilo original con commit, explicación y resultados. Resolverlo en GitHub únicamente tras validar la corrección; si el PR original está fusionado, enlazar un PR correctivo separado.
4. Volver a inspeccionar todas las revisiones existentes y **las nuevas** de Codex, especialmente sobre el PR de la corrección. Repetir revisión → solución → pruebas → respuesta → nueva revisión hasta que no queden pendientes.
5. Si no es técnicamente posible corregirla, abrir o mantener una incidencia con motivo y bloqueo, y no declarar el hallazgo resuelto. Si la observación es incorrecta, justificarlo con evidencias al revisor antes de resolverla.
6. Los agentes OpenCode deben usar la Skill codex-review-loop y la guía docs/codex-review-loop.md. El workflow de vigilancia detecta y da visibilidad a incidencias, pero **no modifica código automáticamente**. No fusionar PRs con hallazgos Codex pendientes.
7. Cuando estén disponibles reglas de protección de ramas, exigir el check de auditoría de revisiones como condición de fusión. La falta de permisos para configurar protección se declara como pendiente, no como requisito ya aplicado.

### CODEX-REVIEW-12 — separación de privilegios

**Prohibido escribir GitHub Issues desde eventos `pull_request_review` o `pull_request_review_comment`**: los PR externos pueden recibir un GITHUB_TOKEN de solo lectura. La auditoría de esos eventos debe limitarse a lecturas y devolver check fallido cuando existan observaciones. La creación/cierre de incidencias se realiza únicamente en `codex-review-issue-sync.yml`, workflow independiente `workflow_run` que vuelve a consultar la API usando exclusivamente scripts de `main` (nunca ejecutando código, comandos ni artefactos de PR de terceros). Mantener pruebas de regresión que garanticen la separación de permisos.


## AWS-GPU-13: ejecución GPU, logs completos y política fail-closed

1. GitHub Actions debe ejecutar fases Linux de preparación, inventario, compilación C, compilación CUDA, ejecución y archivado en EC2 NVIDIA, registrar stdout/stderr y código de retorno de cada fase, e incorporar los resultados en artifacts de GitHub incluso ante errores.
2. Antes de CADA RunInstances consultar tarifa Spot, cuota y hardware AWS actuales. Cumplir 12 cores CPU físicos, 4.352 CUDA cores de una GPU completa, 31 GiB RAM, 11.264 MiB VRAM, compatibilidad con la RTX 2080 Ti UCAM, TTL máximo 60 segundos para la elección y techo de coste definido.
3. La calificación manual se ejecuta solo mediante workflow_dispatch y variable AWS_CUDA_PROBE_ENABLED=true, sin certificar automáticamente la referencia. Push solo funciona con AWS_CUDA_ENABLED=true, baseline VERIFIED y pools aprobados con pruebas reales.
4. Acceder a AWS con OIDC temporal y rol restringido a main, sin claves permanentes y sin SSH público; la compilación EC2 se hace mediante Systems Manager. Guardar logs en S3 y CloudWatch y devolverlos a GitHub Actions.
5. Terminar instancias en finally y en paso always; watchdog EventBridge/Lambda como protección independiente, y EBS DeleteOnTermination. Almacenar logs en GitHub con retención solicitada de 90 días, sujeto a límites del plan.
6. No declarar desplegada ni probada la infraestructura hasta comprobar CloudFormation, configurar GitHub variables, verificar OIDC y ejecutar tests C/CUDA reales. Aplicar CODEX-REVIEW-12 antes de fusionar.
7. Leer [Guía operativa](docs/aws-gpu-ci.md) y [Skill OpenCode](.opencode/skills/aws-cuda-ci/SKILL.md) antes de cambiar scripts, IAM, workflow o guardas de gasto.


## AWS-ACCOUNT-14 — bloquear intentos mientras AWS rechace RunInstances

El 21/11/2026 la pila prueba-cuda-ci se desplegó con estado CREATE_COMPLETE, pero una petición EC2 RunInstances para calificar gr6.8xlarge devolvió error Blocked por estado/verificación de la cuenta. [Incidencia #7](https://github.com/skyirim/prueba-cuda/issues/7).

- No repetir lanzamientos GPU, ni con otra tarifa/familia/región, ni activar GitHub push para sortear el bloqueo. Se necesita resolución de AWS Support.
- Mantener el perfil UCAM en DRAFT y los pools CI sin aprobar, y las variables AWS_CUDA_ENABLED / AWS_CUDA_PROBE_ENABLED desactivadas.
- Guardar evidencia de que CloudFormation está CREATE_COMPLETE y que no hay EC2 activas; no afirmar que se ha ejecutado GCC/nvcc o kernels.
- Tras el desbloqueo, comprobar otra vez las cuotas, tarifas Spot en el preciso instante de cada arranque, roles y AMI; luego calificación manual con techo y TTL, logs y comparación real UCAM.
- No escribir datos de cuenta sensibles en README, PRs, Issues ni logs. Exigir CODEX-REVIEW-12 al modificar infraestructura.


## AWS-SAXPY-15 — prueba real en 3 entornos distintos

La prueba [NVIDIA SAXPY 3×](docs/nvidia-saxpy-3x.md) debe verificar tres ID EC2 diferentes, compilaciones `nvcc`, tres ejecuciones reales con `SAXPY_NVIDIA_PASS`, stdout/stderr originales y eliminación efectiva de cada máquina. Usar selección Spot fresca por arranque, máximo 0,60 USD/h y 30 minutos por EC2. No repetir automáticamente un `Client.Blocked`: detener los ciclos, documentar el error y consultar con AWS Support. Los tests Python con datos simulados NO representan ejecuciones reales. La cuenta sigue bloqueada después del cambio de tarjeta el 21/11/2026. Aplicar CODEX-REVIEW-12 antes de fusionar.
