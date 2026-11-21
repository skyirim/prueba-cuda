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

## 2026-11-21 — CODEX-REVIEW-12 y cierre de hallazgos en PR #3 y PR #4

- La revisión P1 de Codex en PR #3 detectó que el Makefile conservaba cubins sm_75 y sm_89 sin fallback PTX para A10G sm_86 y GPU futuras. El PR #4 añadió cubin sm_75 y PTX compute_75, además de prueba de regresión.
- En PR #4 Codex encontró una incidencia P2 por conservar espacios en el marcador de incidencias, corregida con strip() y test de dos sincronizaciones consecutivas sin duplicación.
- Una nueva revisión de PR #4 detectó otra P2: escrituras de GitHub Issues desde eventos de revisión de forks con token de solo lectura. Se separó Codex Review Sentinel (solo lectura) y Codex Review Issue Sync (workflow_run, checkout exclusivo de main, issues write).
- Se incorporó la norma CODEX-REVIEW-12 a AGENTS.md y una Skill OpenCode. El PR #4 superó 25 tests unitarios y documentales y fue fusionado mediante commit 8bb117399c65f72ebe92553cd831cb0c98d229d2.
- Los dos hilos P2 de PR #4 se contestaron y resolvieron. El hilo P1 de PR #3 se contestó y resolvió tras fusionar la corrección.
- Una ejecución inicial de Sentinel (44921088320) vio PR #3 pendiente porque se ejecutó antes del cierre del hilo. Una auditoría posterior debe comprobar el estado final y no debe dejarse el check rojo sin justificación.
- Importante: estos tests no acreditan aún ejecución de kernels CUDA en las instancias AWS ni en el servidor UCAM; sigue siendo un requisito pendiente distinto de la revisión del código.


## 21-11-2026 — implementación CI AWS y bloqueo de cuenta

- PR #5 fusionado tras revisar y resolver tres hallazgos P1 de Codex sobre permisos CloudWatch, alcance SSM SendCommand y reducción de egress a TCP/443. Pruebas CI offline correctas; funcionalidad AWS GPU todavía sin probar.
- CloudFormation prueba-cuda-ci desplegada en us-west-2 con estado CREATE_COMPLETE: IAM OIDC y roles, S3 cifrado, CloudWatch, SG sin entradas, Lambda watchdog TTL.
- Intento manual de lanzar Spot gr6.8xlarge con precio máximo 0,60 USD/h, plazo máximo 20 minutos y GPU L4 suficiente en especificaciones: respuesta EC2 RunInstances error Blocked por estado de la cuenta AWS. No se creó EC2, por lo tanto no se ejecutaron GCC, nvcc ni kernel CUDA.
- DescribeInstances posterior con Project=prueba-cuda: cero instancias. No se habilitó CI automática mediante GitHub variables.
- Incidencia [#7](https://github.com/skyirim/prueba-cuda/issues/7) creada con pasos de desbloqueo AWS y configuración pendiente.
