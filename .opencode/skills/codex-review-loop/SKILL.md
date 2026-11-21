---
name: codex-review-loop
description: Revisar cada hallazgo de chatgpt-codex-connector en ramas commits y PRs, corregir, probar, responder y comprobar nuevas revisiones hasta resolver todos los hilos.
---

# Revisión iterativa Codex

Leer README.md, AGENTS.md (CODEX-REVIEW-12) y docs/codex-review-loop.md.

1. Consultar revisiones de Codex en PRs abiertos y cerrados, hilos, comentarios de PR y de commit; priorizar P1 y seguridad.
2. Para cada hallazgo anotar ID, URL, SHA, localización, reproducción y criterio de aceptación.
3. Desarrollar el arreglo, crear tests de regresión y ejecutar los checks; para CUDA exigir sm_75 y código/PTX compatible con el conjunto de GPUs seleccionables.
4. Responder en hilo original con enlaces y logs. Resolver solo tras verificar; PR fusionado se arregla con PR nuevo.
5. Solicitar nueva revisión si procede; inspeccionar comentarios originales y nuevos. Repetir hasta cero hallazgos.
6. Mantener incidencia abierta si no es posible corregir y documentar bloqueo; no simular éxito.
7. Consultar workflow Codex Review Sentinel y nunca saltarse fallos ni procesar código no fiable desde una ejecución privilegiada.

## Privilegios de GitHub Actions

En PR de forks, las revisiones deben inspeccionarse con token read-only; no sincronizar incidencias desde ese evento. El workflow con permisos issues:write debe ser exclusivamente el de workflow_run con checkout de main confiable y auditoría fresca; nunca cargar código, comandos o artifacts aportados por el PR externo.
