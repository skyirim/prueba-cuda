## Motivo y ámbito

Describir cambios, ticket y documentación fuente.

## Compatibilidad equipo base

- [ ] Requisitos CPU físicos y CUDA cores acreditados y vinculados a docs/hardware-base.md o se mantiene BLOQUEADO
- [ ] x86-64/ARM64 y compute capability controlados
- [ ] VRAM, vGPU, controlador y CUDA verificados
- [ ] Compilaciones y pruebas reales realizadas, o explícitamente pendientes sin garantía

## Seguridad/costes

- [ ] No aparecen claves, tokens, datos personales ni credenciales
- [ ] Terraform/AMI/Actions con permisos mínimos y versiones fijadas
- [ ] Presupuesto, cuotas, logs y terminación de instancias verificados
- [ ] Precio con fecha/región y coste total actualizado

## Pruebas y reversión

Enlazar resultados de scripts/check_repo.py, unittest y pruebas CUDA de hardware real. Describir rollback y recursos AWS que quedarían tras fallo. No fusionar como funcionalidad lista si faltan evidencias.

## CODEX-REVIEW-12 — cerrar todas las revisiones

- [ ] Revisadas reviews, hilos inline, comentarios de conversación/commits y PRs anteriores relacionados.
- [ ] Observaciones de chatgpt-codex-connector analizadas, corregidas y cubiertas por tests o justificadas con evidencia.
- [ ] Hilos respondidos con enlaces a los cambios; hilos resueltos en GitHub solo tras verificación.
- [ ] Volví a buscar revisiones nuevas después de las últimas modificaciones y no quedan observaciones Codex pendientes.
- [ ] Check Codex Review Sentinel comprobado antes de fusionar.
