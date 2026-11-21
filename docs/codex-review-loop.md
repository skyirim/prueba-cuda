# CODEX-REVIEW-12: corrección iterativa hasta cero revisiones pendientes

**Norma permanente desde el 21/11/2026.** Se aplica a ramas, commits, PR abiertos y fusionados, hilos inline, revisiones generales y comentarios del autor **chatgpt-codex-connector** (también [bot]).

## Procedimiento para todo agente y revisión

1. **Localizar.** Consultar reviews, hilos, comentarios de revisión, comentarios generales y de commits en todos los PR relacionados, incluidos fusionados. Obtener los más recientes después de cada nuevo commit. La etiqueta COMMENTED no implica ausencia de errores.
2. **Registrar.** Guardar URL, ID, prioridad, fecha, SHA, archivo/línea, diagnóstico y criterio de aceptación. Rechazar el supuesto de que un recibo automático significa que todo está correcto.
3. **Analizar y reproducir.** Determinar si existe el fallo. Si no hay hardware/permiso, anotarlo y abrir incidencia; no inventar pruebas.
4. **Implementar.** Proponer la solución en una rama correctiva, añadir regresiones y mantener las reglas C/CUDA, hardware UCAM, seguridad y consulta de tarifas AWS.
5. **Validar.** Ejecutar pruebas y CI; si se afirma compatibilidad CUDA, ejecutar pruebas reales en el equipo correspondiente.
6. **Responder.** Informar en el comentario original de la solución, commit, pruebas y limitaciones; marcar hilo resuelto únicamente después de la comprobación. Si el PR ya fue fusionado, aplicar corrección por otro PR y enlazarlo.
7. **Iterar.** Solicitar nueva revisión a Codex cuando sea pertinente, comprobar su resultado y volver a investigar tanto los hilos anteriores como nuevas observaciones. Repetir hasta cero hallazgos pendientes. Si hay un bloqueo, mantener incidencia abierta.
8. **Cierre.** No fusionar, publicar ni declarar terminado mientras existan hallazgos no resueltos; comprobar status de auditoría. No desactivar o falsificar controles para conseguir éxito.

## Caso inicial: PR #3, P1 de compatibilidad CUDA

Comentario: https://github.com/skyirim/prueba-cuda/pull/3#discussion_r4653362446

Codex observó que conservar exclusivamente cubins sm_75 y sm_89 no produce un ejecutable operativo en A10G sm_86 ni necesariamente en Blackwell. Solución propuesta: mantener cubin sm_75 de UCAM y PTX compute_75 para JIT a GPU posteriores compatibles. Añadir test estático del Makefile; verificar CUDA real cuando haya GPU y driver. Tras fusionar la corrección, responder al hilo original y resolverlo con evidencia, sin reescribir historia.

## Vigilancia y límites

GitHub Actions inspecciona por API hilos de revisión con estado isResolved, revisiones generales y comentarios de commits del autor. Las observaciones pendientes se informan mediante checks y se registran como incidencias. Una automatización de vigilancia **no equivale** a disponer de un agente autónomo que edite código. Las observaciones técnicas fuera de hilos requieren además interpretación humana o por el agente; no se presume que todos los problemas se detectan semánticamente por una expresión regular.

El check detecta revisiones surgidas en cualquier PR, incluso si ya estaba fusionado. Una incidencia cerrada por error sin verificar el hallazgo debe reabrirse. Resolver un hilo sin arreglo es una infracción de esta directiva. La protección efectiva de rama requiere configurar el check como requerido en GitHub.
