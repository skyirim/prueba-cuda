# ADR-0001: criterio de selección y equivalencia de hardware

Fecha: 2026-11-21
Estado: APROBADA COMO POLÍTICA; hardware objetivo PENDIENTE

## Contexto

El usuario quiere Linux+C+CUDA y el menor coste AWS, con un entorno al menos igual al del archivo adjunto en núcleos CPU y GPU y capacidad de compilar y ejecutar código del equipo base. No se recibió el archivo citado. Las instancias g6f.large Spot fueron más baratas en Oregón pero su GPU es fraccionada; g5g.xlarge ofrece una GPU T4g completa.

## Decisión

Los criterios de igualdad de recursos y ejecución prevalecen sobre el coste horario. Nunca asignar valores al equipo base sin fuente. Los núcleos físicos CPU, vCPU/hilos, SM y núcleos CUDA no son lo mismo. No certificar recursos de fracciones GPU por simple proporción; exigir medición o documentación de garantía específica. Documentar compatibilidad CUDA/ABI y ejecución real.

## Alternativas

- G6f: minimiza coste pero con CUDA cores/VRAM fraccionados; puede incumplir mínimos.
- G5g: ARM64 y GPU completa de 16 GiB; debe compilar para ARM y no ejecuta binarios x86-64.
- G4dn/G5/G6/G6e: GPU completa x86-64 con precios y recursos crecientes.
- GPUs P: reservadas a mínimos grandes o cargas de alto rendimiento; excesivas para pruebas pequeñas.

## Consecuencias

La fase de despliegue permanece bloqueada hasta recibir la ficha del equipo. Los agentes pueden editar docs, investigar y desarrollar prototipos sin costes, pero no aprobar equivalencia ni activar autoscaling GPU. La elección final se registrará en un ADR posterior con AMI, pruebas y coste por job.
