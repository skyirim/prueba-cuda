# prueba-cuda — Laboratorio reproducible de C y NVIDIA CUDA en AWS

**Estado (21-11-2026): DOCUMENTACIÓN / DISEÑO; entorno equivalente NO CERTIFICADO; infraestructura NO DESPLEGADA.**

Este repositorio es la fuente de verdad para investigar, dimensionar, construir, ejecutar y mantener un entorno de desarrollo Linux para **C y NVIDIA CUDA** accesible remotamente y utilizable como runner efímero de GitHub Actions. Prioridad: **compatibilidad con la máquina base, comprobación real de los recursos y coste total mínimo por ejecución**.

> **Fuente UCAM recibida el 21-11-2026:** servidor Ubuntu 22.04.5 x86-64, **12 cores CPU físicos, 31 GiB RAM, una NVIDIA RTX 2080 Ti con 4.352 CUDA cores, 68 SM, 11.264 MiB de VRAM y Compute Capability 7.5**. La fuente y su SHA-256 figuran en [docs/hardware-base.md](docs/hardware-base.md). No se han ejecutado aún tests CUDA en UCAM y AWS; **el equipo equivalente todavía NO está certificado**.

## 1. Requisitos del proyecto

1. Linux con compilador C (GCC/Clang), NVIDIA CUDA Toolkit y controlador compatible; compilar y ejecutar realmente código C y kernels CUDA.
2. Igualar o superar **todos** los mínimos verificables del equipo de referencia. Distinguir núcleos físicos CPU / vCPU / hilos, SM / CUDA cores / memoria GPU y GPU completa / fraccionada. No confundir "8 GiB de RAM" con VRAM.
3. Reproducir el entorno funcional de referencia (ABI, arquitectura CPU, compute capability NVIDIA, versiones de bibliotecas y capacidades particulares). Si se exige ejecutar el mismo binario nativo, comprobar además ISA y arquitectura CPU; si basta portabilidad de código fuente, recompilar y probar en ambas plataformas.
4. Acceso remoto por SSH con claves y origen restringido, o preferentemente Session Manager; runners efímeros aislados sin reutilizar la estación SSH.
5. Por cada push autorizado, aprovisionamiento bajo demanda y prueba; logs, errores, binarios y resultados en GitHub; terminación automática y recuperable ante fallos. No activar el pipeline facturable hasta aprobar los bloqueos de hardware, seguridad y costes.
6. Investigación y operación documentadas, auditables y reproducibles por humanos y agentes OpenCode; sin afirmaciones de compatibilidad basadas únicamente en fichas comerciales.

## 2. Situación de la investigación

Las siguientes son **instantáneas** de AWS consultadas el 21-11-2026; no representan precios futuros, capacidad garantizada o presupuestos totales:

| EC2 Linux | CPU / GPU | Spot observado USD/h | Región/zona | On-Demand USD/h | Nota |
| --- | --- | ---: | --- | ---: | --- |
| g6f.large | x86-64, 2 vCPU, 1/8 NVIDIA L4, ~2,79 GiB VRAM | 0,0565 | us-west-2b | 0,2020 | Menor tarifa Spot observada con cuota en la cuenta; **GPU fraccionada; NO presumir igualdad de cores** |
| g6f.xlarge | x86-64, 4 vCPU, 1/8 NVIDIA L4, ~2,79 GiB VRAM | 0,0741 | us-west-2c | 0,2375 | Más CPU/RAM, misma fracción GPU |
| g5g.xlarge | ARM64, 4 vCPU, 1 NVIDIA T4g, 16 GiB VRAM | 0,1069 | us-west-2a | 0,4200 | GPU completa, ARM64; 8 GiB RAM |
| g4dn.xlarge | x86-64, 4 vCPU, 1 NVIDIA T4, 16 GiB VRAM | 0,2149 | us-west-2c | 0,5260 | GPU completa, x86-64 |
| g6.xlarge | x86-64, 4 vCPU, 1 NVIDIA L4, ~22,35 GiB VRAM | 0,4852 | us-west-2a | 0,8048 | GPU completa moderna |
| g5.xlarge | x86-64, 4 vCPU, 1 NVIDIA A10G, ~22,35 GiB VRAM | 0,5515 | us-west-2c | 1,0060 | GPU completa |
| g6e.xlarge | x86-64, 4 vCPU, 1 NVIDIA L40S, ~44,70 GiB VRAM | 1,7664 | us-west-2d | 1,8610 | GPU completa potente |

Se observó g6f.large Spot a 0,0460 USD/h en São Paulo (sa-east-1a), **pero la cuota Spot G/VT de la cuenta era 0 vCPU** allí. En Oregón constaba una cuota Spot G/VT de 126 vCPU. Otras regiones comprobadas con cuota 0 no pueden considerarse desplegables sin aumento de cuota. La capacidad Spot no está reservada. La región de Madrid (eu-south-2) no estaba activada en la cuenta. Tarifas: EC2 sin EBS, IPv4, imágenes, CloudWatch ni servicio de control.

**IMPORTANTE:** no elegir g6f por precio si la ficha de hardware exige una GPU con más SM, cores CUDA realmente disponibles, VRAM o funciones no expuestas por una vGPU. El modelo de cómputo virtualizado de G6f requiere NVIDIA GRID adecuado; preferir Amazon Linux 2023 o Ubuntu con combinación aprobada de controlador/CUDA. No instalar un controlador genérico Tesla en G6f.

## 3. Política de equivalencia (no negociable)

La equivalencia **NO** se demuestra por el número de vCPU, por el nombre de una GPU, ni por una división teórica de CUDA cores de una GPU física. Para declararla, deben existir:

- Fuente original del equipo base (fichero, hash, fecha y transcripción completa) en [docs/hardware-base.md](docs/hardware-base.md).
- Inventario real de referencia y destino (CPU física / hilos, GPU/SMS, CUDA cores justificables, VRAM, compute capability, ISA, versiones; con evidencia).
- Matriz [docs/compatibilidad.md](docs/compatibilidad.md) con mínimos cuantitativos y pruebas de ejecución en ambas plataformas.
- Comparación sobre resultados, tiempos y consumo de memoria representativos. Si no hay acceso a la referencia para ejecutar programas, declarar la limitación.
- Informe de validación reproducible, con fallos y códigos de salida; **no certificar lo que no se ha probado**.

Hasta conocer el equipo base, la selección AWS es **provisional**; la mejor tarifa horaria no implica la instancia adecuada.

## 4. Diseño de ejecución (pendiente de activar)

~~~mermaid
flowchart TD
  A["Push autorizado en GitHub"] --> B["Validación documental y seguridad (GitHub-hosted)"]
  B --> C{"Ficha base completa y aprobada?"}
  C -->|No| D["Bloquear aprovisionamiento GPU / informar"]
  C -->|Sí| E["Controlador GitHub App + webhook workflow_job"]
  E --> F["Selector EC2 Spot según recursos, cuota y coste"]
  F --> G["EC2 Linux + NVIDIA + AMI prevalidada"]
  G --> H["Runner GitHub Actions --ephemeral"]
  H --> I["GCC / nvcc / tests y logs"]
  I --> J["Publicar artifacts / logs en GitHub"]
  J --> K["Desregistrar y TERMINAR instancia; watchdog independiente"]
~~~

Se requiere separación entre entorno interactivo SSH y runner CI. El controlador debe verificar firma del webhook, repositorio/ramas/etiquetas, deduplicar eventos, registrar coste, aplicar máximo de instancias, timeout y limpieza independiente. La instancia Spot puede ser interrumpida, por lo que **logs a CloudWatch** y recuperación son necesarios. **Esta arquitectura es un diseño; no hay recursos facturables ni runner registrados por esta documentación.**

## 5. Índice documental y guías para agentes

- [docs/hardware-base.md](docs/hardware-base.md): transcripción técnica del servidor UCAM y sus 12 cores CPU / 4.352 CUDA cores GPU, con SHA-256 y datos pendientes.
- [docs/compatibilidad.md](docs/compatibilidad.md): reglas para demostrar equivalencia CPU y GPU, compatibilidad de binarios, CUDA y regresiones.
- [docs/aws-investigacion.md](docs/aws-investigacion.md): consulta reproducible EC2, precios, cuotas, regiones, método y hallazgos con fecha.
- [docs/arquitectura.md](docs/arquitectura.md): autoscaling GitHub/AWS, acceso SSH, amenaza, cierre y operación.
- [docs/implementacion.md](docs/implementacion.md): plan de aprovisionamiento en etapas y prueba integral.
- [docs/operacion.md](docs/operacion.md): logs, diagnósticos, interrupciones Spot, control de costes y recuperación.
- [docs/decisiones/0001-criterios-de-equivalencia.md](docs/decisiones/0001-criterios-de-equivalencia.md): decisión técnica y evidencia necesaria.
- [AGENTS.md](AGENTS.md): directivas permanentes obligatorias, aplicables a personas y agentes.
- [.opencode/skills/cuda-equivalencia/SKILL.md](.opencode/skills/cuda-equivalencia/SKILL.md): flujo de evaluación de hardware y CUDA.
- [.opencode/skills/aws-spot-gpu/SKILL.md](.opencode/skills/aws-spot-gpu/SKILL.md): investigación periódica de precios y cuotas.
- [.opencode/skills/runner-efimero/SKILL.md](.opencode/skills/runner-efimero/SKILL.md): diseño y pruebas seguras del runner.
- [config/hardware-base.schema.json](config/hardware-base.schema.json): ficha para transcribir mínimos, **sin valores inventados**.
- [scripts/check_repo.py](scripts/check_repo.py): verificación documental automática; [scripts/check_baseline.py](scripts/check_baseline.py) valida perfil base **cuando esté disponible**.
- [.github/workflows/docs-check.yml](.github/workflows/docs-check.yml): controles gratuitos en push y PR; no inicia GPU.

## 6. Reproducción por un agente OpenCode

1. Leer **README.md completo** y a continuación **AGENTS.md**; en OpenCode son instrucciones persistentes del proyecto.
2. Verificar que existe el fichero de referencia real; si no, documentar el bloqueo y **no asignar cores ni certificar compatibilidad**.
3. Usar Skills específicas de la tarea y anotar herramienta/API AWS, región, momento, tipo y estado de cada dato.
4. Leer el perfil base; realizar inventario de instancias y pruebas reales de compilación/ejecución.
5. Proponer cambios mediante PR revisable, con matriz de requisitos/evidencias, pruebas, cálculo de costes e instrucciones de reversión.
6. No instalar componentes o activar AWS/GitHub App/credenciales por aproximación. Consultar [docs/implementacion.md](docs/implementacion.md).

### Fuentes primarias

- [AWS EC2 accelerator specs](https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html)
- [AWS EC2 Spot](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html)
- [AWS NVIDIA GRID install](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-GRID-driver.html)
- [NVIDIA GPU virtualisation AWS support](https://docs.nvidia.com/vgpu/cloud-service-support.html)
- [NVIDIA CUDA Programming Guide](https://docs.nvidia.com/cuda/cuda-programming-guide/)
- [GitHub self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)
- [OpenCode Skills](https://opencode.ai/docs/skills)

## 7. Estado de los hitos

| Hito | Estado |
| --- | --- |
| Investigación EC2 NVIDIA Spot/On-Demand en varias regiones | Referencia fechada; **renovar antes del despliegue** |
| Ficha técnica del equipo base | **DOCUMENTADA** a partir del TXT UCAM, con identificación y hash |
| Mínimos de cores CPU/GPU | **12 cores físicos CPU, 4.352 CUDA cores GPU**; AWS aún sin ensayo real |
| Imagen Linux CUDA con controladores probados | No construida |
| AWS GitHub runner efímero, SSH, logs, limpieza y presupuesto | Documentado; no desplegado |
| Tests C/CUDA ejecutados en base y AWS | No ejecutados |
| Garantía de portabilidad y equivalencia | **NO DEMOSTRADA** |

**Última revisión documental:** 2026-11-21. Actualizar las evidencias y este estado al completar cada hito. Nunca convertir un pendiente en aprobado sin logs y pruebas enlazables.


## 8. Vigilancia permanente (sin gasto AWS)

- La Action [.github/workflows/maintenance.yml](.github/workflows/maintenance.yml) programa una **auditoría mensual**: comprueba si falta verificar la equivalencia y si los datos de [config/research-snapshot.json](config/research-snapshot.json) tienen más de 30 días; publica un resumen y crea una incidencia GitHub sin duplicarla si existe un aviso. No consulta tarifas en AWS de forma automática ni consume instancias.
- [scripts/audit_maintenance.py](scripts/audit_maintenance.py) implementa el control temporal y el bloqueo de baseline. [docs/plan-pruebas.md](docs/plan-pruebas.md) define las pruebas de aceptación; [docs/registro.md](docs/registro.md) conserva el histórico.
- [infrastructure/README.md](infrastructure/README.md) explica el estado del IaC: **todavía no desplegado**. Activar recursos de pago requiere equivalencia comprobada, AMI y presupuesto aprobado.
- Los agentes OpenCode deben analizar las incidencias abiertas y proponer PRs con datos, fuentes y pruebas, no fingir que se corrigieron automáticamente.


## 9. REGLA PERMANENTE: elegir precio AWS en el instante de CADA arranque

> **Obligatorio para cualquier nueva EC2 GPU, tanto SSH como GitHub Actions:** el controlador debe realizar una consulta fresca y directa a la API **`DescribeSpotPriceHistory` y a Service Quotas inmediatamente antes de cada `RunInstances`**. Está **prohibido** utilizar para decidir la tarifa de un TXT, un README, una tabla del día anterior o una caché persistente. Si el plan tiene más de 60 segundos, **repetir** la consulta. Si la API falla, **no lanzar**.

**Primero el hardware, después el precio:** seleccionar solo máquinas que demuestren >=12 cores físicos CPU, >=4.352 CUDA cores GPU en **una GPU completa**, >=31 GiB de RAM y >=11.264 MiB de VRAM utilizable, con Linux, drivers y CUDA compilables/ejecutables para el propio hardware y para la **RTX 2080 Ti `sm_75`**. Los 68 SM de la referencia se registran, pero **no** equivalen a 4.352 cores de una microarquitectura distinta y **no** constituyen un mínimo separado.

1. Recuperar catálogo AWS actual `DescribeInstanceTypes`, perfiles aprobados de AMI/driver/CUDA, regiones y AZ autorizadas, cuota vCPU Spot suficiente y subredes.
2. Rechazar cualquier tipo con CPU/GPU/RAM/VRAM insuficiente, fracción GPU no demostrada, GPU desconocida, incompatibilidad software, cuota insuficiente o AMI no certificada.
3. En cada región/AZ elegible consultar el precio Spot **último por pareja tipo/zona** (y On-Demand sólo si se permite explícitamente), calcular coste total previsible, ordenar ofertas válidas por tarifa real y elegir la menor a la que pueda acceder la cuenta.
4. Registrar hora UTC, respuesta de AWS, región, zona, tipo, tarifa USD/h, perfil y AMI; justo antes de `RunInstances` comprobar vigencia del plan (TTL máximo 60 segundos). Una instancia Spot **puede carecer de capacidad aunque sea la más barata**: probar la siguiente oferta aprobada, con nueva consulta; nunca degradar requisitos.
5. Terminar la instancia al finalizar el trabajo; registrar tiempo y coste real. El selector inicial está en [infrastructure/select_gpu_spot.py](infrastructure/select_gpu_spot.py), con pruebas [tests/test_spot_selector.py](tests/test_spot_selector.py) y procedimiento [docs/precio-en-arranque.md](docs/precio-en-arranque.md). **El despliegue AWS sigue pendiente**: el selector es un módulo de decisión, no un controlador de instancias ya instalado.

La tarifa **0,4929 USD/h de `gr6.8xlarge` en Oregón** fue la menor Spot observada hoy entre las opciones numéricamente adecuadas con cuota regional. **No es un precio que deba utilizarse en futuros lanzamientos sin volver a consultar AWS.** Más detalles en [docs/aws-investigacion.md](docs/aws-investigacion.md) y [ADR-0002](docs/decisiones/0002-tarifa-tiempo-real.md).

## 10. Revisión iterativa permanente de Codex

La regla **CODEX-REVIEW-12** de [AGENTS.md](AGENTS.md) obliga a analizar y tratar toda revisión de chatgpt-codex-connector en ramas, commits, PRs abiertos/fusionados y comentarios, corregir el código, ejecutar pruebas, responder a los hilos y volver a inspeccionar revisiones anteriores y nuevas hasta que no queden hallazgos pendientes.

Se documenta en [docs/codex-review-loop.md](docs/codex-review-loop.md) y en la [Skill OpenCode](.opencode/skills/codex-review-loop/SKILL.md). El control automatizado [Codex Review Sentinel](.github/workflows/codex-review-sentinel.yml) inspecciona discusiones y hace visibles las pendientes; no escribe soluciones por sí solo.

El hallazgo P1 de [PR #3](https://github.com/skyirim/prueba-cuda/pull/3#discussion_r4653362446) detectó la falta de PTX forward-compatible con A10G sm_86 y otras GPU. El Makefile pasa a conservar código sm_75 y PTX compute_75; los tests previenen esta regresión. Pendiente validar ejecución física GPU en las instancias aprobadas.

### Separación de permisos para revisiones de forks

El workflow [Codex Review Sentinel](.github/workflows/codex-review-sentinel.yml) inspecciona las revisiones con un token **de solo lectura** y publica un fallo de check si existen pendientes. Un segundo workflow [Codex Review Issue Sync](.github/workflows/codex-review-issue-sync.yml), activado mediante `workflow_run`, vuelve a auditar desde código confiable de `main` y sincroniza GitHub Issues con permisos de escritura. No ejecuta código de forks ni consume sus artefactos; los comentarios de commits se detectan en el barrido diario y la auditoría general.
