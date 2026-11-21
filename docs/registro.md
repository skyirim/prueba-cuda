# Registro de hitos y cambios de evidencia

## 2026-11-21 — inicialización documental

- Consultas de AWS EC2 / Price List / Service Quotas de la conversación: G6f y G5g como candidatos, precios Spot y On-Demand en regiones comparadas, cuotas por región. **Instantáneas temporales**, no contratos.
- GitHub: repositorio skyirim/prueba-cuda inicialmente vacío; README, documentación, AGENTS.md, Skills OpenCode y configuraciones añadidas.
- Bloqueo: el archivo adjunto del equipo base mencionado por el usuario no está disponible en esta conversación; ni GPU ni instancia equivalente verificada.
- Pipeline de documentación y pruebas unitarias preparado; plantilla GPU inactiva, sin recursos AWS desplegados.
- Auditoría mensual de documentación/precios configurada para detectar incumplimientos y abrir incidencia; actualizar la tabla de precios/quotas y el perfil mediante PR revisado, no reconfigurar instancias automáticamente.

**Toda afirmación de funcionamiento GPU, compatibilidad con referencia y disponibilidad Spot queda pendiente de pruebas reales.**


## 2026-11-21 — documento original UCAM recibido

- SHA-256 archivo: `07a5105d27c18ffd3caa464054885187d93a65b0240d4804d0efae910c349f8f`, **26.012 bytes**. Datos de servidor Ubuntu 22.04.5 x86-64, 2× Xeon E5-2603 v4, 12 cores físicos totales, 12 lógicos, 31 GiB RAM, NVIDIA RTX 2080 Ti 11.264 MiB VRAM, driver 535.288.01, nvidia-smi CUDA 12.2; NVIDIA acredita 4.352 CUDA cores, 68 SM, CC 7.5.
- Hardware base ahora documentado. PENDIENTE la versión real nvcc de UCAM y la ejecución C/CUDA en equipo de referencia y AWS.
- Mínimos normativos: CPU>=12 cores físicos, GPU>=4.352 CUDA cores por GPU completa, RAM>=31 GiB, VRAM>=11.264 MiB, portabilidad de fuentes para GPU UCAM sm_75 y dispositivo AWS.
- AWS Spot Oregón gr6.8xlarge 16 cores físicos CPU, NVIDIA L4 7.424 CUDA cores y ~22.888 MiB VRAM, Spot observado 0,4929 USD/h, cuota Spot GPU 126 vCPU. Precio meramente histórico.
- Nueva regla PRICE-LAUNCH-11: consulta Spot/quotas INMEDIATAMENTE antes de **cada** creación, filtro de recursos y compatibilidad antes de precio, TTL máximo 60 segundos, fallo cerrado, no utilizar histórico.
