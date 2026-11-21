---
name: runner-efimero
description: Diseña y verifica el escalado bajo demanda de runners GitHub Actions efímeros EC2 NVIDIA, con SSH separado, seguridad, logs, cuotas y eliminación automática.
---

# Runner GitHub-AWS

1. Leer AGENTS.md, docs/arquitectura.md, docs/implementacion.md, docs/seguridad.md y docs/operacion.md.
2. Bloquear creación de runner GPU mientras ficha base e imagen no superen validación y pruebas CUDA reales.
3. Controlador externo escucha workflow_job queued (no depender del runner ausente), verifica firma y repo/ref/labels y deduplica.
4. Selecciona solo EC2 GPU compatible con ficha, cuota, límites de gasto y región autorizadas; no degradación silenciosa de recursos.
5. Runner con token JIT de corta vida y --ephemeral, aislamiento por job, IAM mínimo, IMDSv2, sin SSH público y logs remotos.
6. Configurar watchdog independiente, TTL, tags, límites de concurrencia y rollback; probar errores previos y posteriores al registro GitHub.
7. CI publica cada stdout/stderr, artifacts y estado final; los fallos de arranque e interrupción están en CloudWatch.
8. Entregar Terraform reproducible, plan, pruebas, inventario, coste real, seguridad y evidencia de destrucción antes de aprobar.


## Selección obligatoria antes de arrancar

Ningún flujo de GitHub debe crear una EC2 directamente sin invocar selección de Spot y cuota **justo antes de cada RunInstances**, TTL <=60 segundos, reconsulta ante Spot unavailable y pruebas de compatibilidad con CPU/GPU UCAM. Una oferta actual seleccionada no da derecho a mantenerla cacheada para el siguiente job. Si no hay máquina viable que cumpla >=12 cores físicos CPU y >=4.352 CUDA cores GPU completa, el job debe fallar claramente sin aprovisionar.
