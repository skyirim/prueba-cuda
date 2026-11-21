# ADR-0002: optimizar Spot justo antes de cada aprovisionamiento

Fecha: 2026-11-21
Estado: Política aprobada; implementación del selector disponible como módulo, controlador AWS no desplegado.

## Necesidad

Las tarifas Spot varían por región, zona y tipo EC2 y la capacidad no está garantizada. En la cuenta usada para investigar hubo cuotas Spot G/VT 126 vCPU en Oregón y 0 en otras regiones consultadas. El ahorro depende de preguntar AWS **en el instante de cada nuevo arranque**, no de una tabla publicada.

## Decisión obligatoria

1. **Antes de cualquier RunInstances**: obtener requisitos del equipo UCAM y solo pools aprobados (AMI, driver, CUDA, repositorio, región, AZ, subred); consultar atributos actuales DescribeInstanceTypes y cuotas Service Quotas.
2. Excluir todos los candidatos incapaces de ofrecer >=12 cores físicos de CPU, >=4.352 CUDA cores de una GPU completa, >=31 GiB RAM, >=11.264 MiB GPU y Linux CUDA compatible con GPU AWS y sm_75 UCAM.
3. Consultar la tarifa Spot de AWS mediante DescribeSpotPriceHistory **en esa misma operación**; para cada (tipo, región, AZ) tomar el dato más reciente, no el mínimo histórico. Cada instancia usa su **propia consulta**; nunca reutilizar un plan antiguo, snapshot documental o precio cacheado.
4. Filtrar por cuotas suficientes, región activada, imagen certificada, política de gasto y disponibilidad administrativa. Comparar ofertas técnicas válidas por coste por hora y coste total previsto, incluyendo EBS/IPv4/logs/tiempos; elegir menor coste según las restricciones aprobadas.
5. Validez de plan <=60 segundos, justo antes del lanzamiento; expiración -> reconsulta. Si la cotización falla, precio desconocido o cuota cero: NO arrancar. Spot agotada: reconsulta y siguiente oferta aprobada; nunca reducir CPU/GPU ni subir a On-Demand sin autorización y límite de precio.
6. Guardar log auditable de consulta, hora UTC, tarifas y AZ candidatas, elección, AMI, costos adicionales previstos, intentos y resultado. Terminar recursos y auditar costes reales.
7. Aplicar exactamente la misma regla a instancias CI efímeras y estaciones de desarrollo SSH.

## Implementación y límites

Código: [infrastructure/select_gpu_spot.py](../../infrastructure/select_gpu_spot.py), [tests/test_spot_selector.py](../../tests/test_spot_selector.py), [docs/precio-en-arranque.md](../precio-en-arranque.md). Un selector que solo devuelve plan **no arranca** la VM y no sustituye el controlador transaccional; se integrará cuando exista AMI certificada, permisos, tests y presupuesto aprobado. La instancia mas barata observada no significa capacidad disponible.

## Rechazos

Se rechaza elegir por tarifa guardada en README/research-snapshot o elegir antes de validar cores y compatibilidad. Se rechaza usar una instancia más barata con menos recursos que el servidor UCAM. Se rechaza sumar núcleos CUDA de GPUs diferentes para dar equivalencia monodispositivo.
