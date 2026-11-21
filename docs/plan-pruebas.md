# Plan de pruebas y criterios de aceptación

Las pruebas unitarias del gate validan el validador, **no la existencia de hardware equivalentes**. No declarar plataforma funcional hasta que todas las pruebas de destino y equipo base tengan evidencia.

| ID | Prueba | Evidencia/resultado esperado | Estado |
| --- | --- | --- | --- |
| DOC-01 | README y rutas de documentos | python3 scripts/check_repo.py retorna 0 | Pendiente de verificación CI |
| GATE-01 | perfil base incompleto | check_baseline.py retorna error BLOQUEADO | Diseñado, no verificado en CI |
| GATE-02 | inventario ficticio inferior CPU/GPU | tests/test_baseline.py rechaza | Diseñado, no verificado en CI |
| GPU-01 | NVCC y driver | nvcc --version + nvidia-smi + propiedad CC | NO EJECUTADO |
| GPU-02 | ejecución CUDA real | make test, output correctos y GPU accesible | NO EJECUTADO |
| BASE-01 | referencia frente destino | GPU cores y SM certificados + CPU cores suficientes | BLOQUEADO: sin adjunto |
| PORT-01 | compilar/ejecutar mismas fuentes | resultados correctos en base y AWS | BLOQUEADO |
| SPOT-01 | cuota/capacidad e interrupción | mensaje y fallback sin degradar hardware | NO EJECUTADO |
| SEC-01 | webhook e IAM | rechazo firma falsa/PR no confiable | NO EJECUTADO |
| LIFE-01 | finalización y rollback | instancia, volumen y runner eliminados | NO EJECUTADO |
| LOG-01 | errores previos y posteriores a runner | GitHub/CloudWatch y alarmas correctas | NO EJECUTADO |
| COST-01 | factura real | EC2+EBS+control, consumo no residual | NO EJECUTADO |

## Criterios de aprobación

- Perfil del equipo base extraído del documento íntegro y aprobado; hashes y pruebas.
- Todos los recursos requeridos por la referencia medidos/justificados; GPU fraccionada excluida si no se demuestra.
- Tests reales de C/CUDA y datos representativos en base y nube; logs vinculados al commit, AMI y fecha.
- Tests de fallos y destrucción ejecutados; resumen de costes reales.
- Cambios en docs y README con evidencia; revisión de agente y revisión humana.
