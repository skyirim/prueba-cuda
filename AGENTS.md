# Instrucciones permanentes para agentes humanos, OpenCode y GitHub Copilot

Ámbito: todo el repositorio. **Leer README.md y AGENTS.md antes de investigar, editar, ejecutar, presupuestar o proponer infraestructura**. El README es el índice y la fuente de verdad del estado; una contradicción se resuelve mediante PR documental verificable, no ignorando el bloqueo.

## Reglas innegociables

1. **BASELINE-01, fuente obligatoria.** No inventar especificaciones del equipo base. Si el adjunto no existe, registrar BLOQUEADO en docs/hardware-base.md; no afirmar equivalencia de cores CPU/GPU. Incorporar íntegramente transcripción técnica, procedencia, fecha y SHA-256 cuando se suministre (material con licencia: conservar referencia o resumen permitido, no publicar documentos confidenciales sin permiso).
2. **HARDWARE-02, conteos comparables.** Distinguir CPU física, hilos/vCPU, SMT, GPU física, SM, CUDA cores FP32, Tensor cores, memoria VRAM y fracción virtualizada; no estimar cores asignados de una GPU fraccionada multiplicando automáticamente el total físico. Documentar fuente NVIDIA/AWS o medida realmente verificable.
3. **COMPAT-03, prueba y portabilidad.** Compilar C con avisos estrictos y CUDA con arquitecturas objetivo; ejecutar tests y comparar resultados en AWS y la máquina base. Recompilar para CPU ISA diferente. No asumir que número de CUDA cores garantiza el mismo comportamiento, rendimiento, VRAM o funciones. Registrar compute capability, driver, toolkit, bibliotecas y pruebas de regresión.
4. **GATE-04, fail-closed.** La promoción a entorno VALIDADO exige baseline completo, inventarios, matriz y resultados reales. Si una prueba falta o es ambigua, falla; NO activar workflow GPU automático. CI documental puede funcionar sin GPU; no suprimir un fallo de equivalencia para obtener build verde.
5. **COST-05, minimizar coste verdadero.** Reconsultar precios Spot, On-Demand, zonas, cuotas, capacidad y servicios adicionales (EBS, IPv4, red, almacenamiento, control). Fechar región/consulta y calcular por duración total incluyendo arranque, interrupciones y limpieza. Priorizar coste por trabajo correcto, no USD/h aislado. Nunca presentar tarifa puntual como precio fijo.
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
