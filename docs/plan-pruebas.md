# Plan de pruebas y criterios de aceptación

Las pruebas unitarias del gate validan el validador, **no la existencia de hardware equivalentes**. No declarar plataforma funcional hasta que todas las pruebas de destino y equipo base tengan evidencia.

| ID | Prueba | Evidencia/resultado esperado | Estado |
| --- | --- | --- | --- |
| DOC-01 | README y rutas de documentos | python3 scripts/check_repo.py retorna 0 | Pendiente de verificación CI |
| GATE-01 | perfil baseline en estado DRAFT | check_baseline.py retorna error BLOQUEADO | Diseñado, no verificado en CI |
| GATE-02 | inventario ficticio inferior CPU/GPU | tests/test_baseline.py rechaza | Diseñado, no verificado en CI |
| GPU-01 | NVCC y driver | nvcc --version + nvidia-smi + propiedad CC | NO EJECUTADO |
| GPU-02 | ejecución CUDA real | make test, output correctos y GPU accesible | NO EJECUTADO |
| BASE-01 | referencia frente destino | GPU CUDA cores >=4.352 en una GPU (SM informativos), CPU físicos >=12, VRAM >=11.264 MiB y RAM >=31 GiB | Fuente recibida; pruebas comparativas pendientes |
| PORT-01 | compilar/ejecutar mismas fuentes | resultados correctos en base y AWS | BLOQUEADO |
| SPOT-01 | cuota/capacidad e interrupción | mensaje y fallback sin degradar hardware | NO EJECUTADO |
| SEC-01 | webhook e IAM | rechazo firma falsa/PR no confiable | NO EJECUTADO |
| LIFE-01 | finalización y rollback | instancia, volumen y runner eliminados | NO EJECUTADO |
| LOG-01 | errores previos y posteriores a runner | GitHub/CloudWatch y alarmas correctas | NO EJECUTADO |
| COST-01 | factura real | EC2+EBS+control, consumo no residual | NO EJECUTADO |
| PRICE-01 | selector justo antes de lanzar | Consultas actuales AWS Spot/cuotas por instancia y caducidad <=60s | TESTS UNITARIOS PENDIENTES |
| PRICE-02 | opciones insuficientes y fallo API | no seleccionar GPU fraccionada, vCPU insuficiente, respuesta sin precio o antigua; fallo cerrado | TESTS UNITARIOS PENDIENTES |

## Criterios de aprobación

- Perfil del equipo base extraído del documento íntegro y aprobado; hashes y pruebas.
- Todos los recursos requeridos por la referencia medidos/justificados; GPU fraccionada excluida si no se demuestra.
- Tests reales de C/CUDA y datos representativos en base y nube; logs vinculados al commit, AMI y fecha.
- Tests de fallos y destrucción ejecutados; resumen de costes reales.
- Cambios en docs y README con evidencia; revisión de agente y revisión humana.


## Comparación de SM y CUDA cores

La RTX 2080 Ti UCAM tiene 68 SM con 64 núcleos FP32 por SM, total 4.352. NVIDIA L4 tiene 58 SM con 128 núcleos FP32 por SM, total 7.424. El requisito explícito son **4.352 CUDA cores**, no >=68 SM en todas las arquitecturas. Gate en scripts/check_baseline.py comprueba >=68 SM únicamente si `require_sm_parity=true` (no se exige ahora). Comparar pruebas reales de kernel sobre ambas tarjetas sigue obligatorio.
