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
