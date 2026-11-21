# Tres pruebas reales de NVIDIA SAXPY sobre AWS GPU desde GitHub Actions

## Fuente y equivalencia

Fuente estudiada: [Mark Harris, *An Easy Introduction to CUDA C and C++* (NVIDIA, 2012)](https://developer.nvidia.com/blog/easy-introduction-cuda-c-and-c/).

El archivo [programs/cuda/saxpy_nvidia.cu](../programs/cuda/saxpy_nvidia.cu) es una **adaptación original** del ejemplo SAXPY de esa página (no una reproducción literal): para 1.048.576 elementos inicializa `x=1`, `y=2` y aplica `y=2*x+y` en una GPU NVIDIA con bloques de 256 hilos. El resultado esperado es `y=4` y error máximo `0.000000`. La adaptación comprueba los resultados de las llamadas CUDA, el lanzamiento, la sincronización y devuelve código distinto de cero si falla. La confirmación inequívoca será `SAXPY_NVIDIA_PASS`.

La ejecución del programa prueba que se ha ejecutado un kernel CUDA real sobre la GPU seleccionada, no solo que el compilador funciona. Los 12 núcleos físicos CPU y 4.352 CUDA cores GPU mínimos se siguen validando mediante el inventario del entorno UCAM.

## Flujo de tres pruebas independientes

[Workflow GitHub Actions](../.github/workflows/aws-saxpy-three-runs.yml) y [verificador](../scripts/ci/verify_three_runs.py).

1. Inicio **manual**, únicamente en `main`, con confirmación `EJECUTAR` y variable `AWS_CUDA_PROBE_ENABLED=true`.
2. Usar GitHub-hosted runner como orquestador, conexión OIDC a AWS sin claves permanentes.
3. Por cada iteración 1/3, 2/3, 3/3: seleccionar **precio Spot recién consultado**, respetando la arquitectura de CPU/GPU y límite 0,60 USD/h; arrancar una EC2 nueva etiquetada con `ExpireAtEpoch` máximo 30 minutos.
4. EC2 SSM descarga las fuentes *del commit GitHub*, muestra CPU/GPU, GCC y NVCC, compila el programa SAXPY mediante `nvcc`, ejecuta el kernel y genera stdout/stderr completos para cada comando, además de resultados tar.gz.
5. Imprimir en la consola GitHub Actions todas las salidas SSM recogidas desde S3, conservar CloudWatch y S3 temporales, y publicar `aws-saxpy-3x-<run>-<attempt>` en GitHub Artifacts (90 días solicitados, sujeto a configuración del plan).
6. Al terminar cada ciclo, verificar la **terminación de la EC2** y solicitar su borrado desde `finally`, con paso de limpieza adicional `if: always()` y watchdog AWS cada 5 minutos.
7. Continuar con la siguiente iteración **solo si la anterior fue satisfactoria**. No lanzar las tres simultáneamente. Si AWS devuelve `Client.Blocked`, se aborta sin repetir.
8. El verificador final exige 3 `instance_id` distintos, 3 `SAXPY_NVIDIA_PASS`, todas las fases SSM con código 0, 3 archivos de resultados y 3 terminaciones confirmadas. Si falta cualquiera, GitHub Actions debe fallar.

### Coste previsto

- Límite de precio de instancia: **0,60 USD/h Spot**, no una tarifa garantizada ni un precio total.
- Límite de tiempo de instancia: **30 minutos por ciclo**, en tres ciclos secuenciales. El **máximo teórico de tiempo de cómputo** según esos topes es 3 × 0,5 h × 0,60 USD/h = **0,90 USD** (no incluye EBS, IPv4, transferencias, logs ni costes de reintentos/servicios auxiliares).
- Sin capacidad Spot suficiente o por encima del precio máximo, rechazar, no degradar recursos y no arrancar.
- Un workflow GitHub Actions tiene límite de 110 minutos y acceso OIDC temporal; la caducidad AWS se ejecuta mediante un watchdog independiente aunque falle GitHub.

### Pasos de puesta en servicio

1. **Imprescindible desbloquear AWS:** el 21-11-2026 a las 17:14:20 UTC, tras actualizar la tarjeta, la petición `RunInstances` recibió de nuevo `Client.Blocked`, por lo que **no se ha ejecutado ninguna de las tres pruebas reales**. Petición: `ddc25c95-c5d6-45b0-9fac-79ed675b705b`; evento CloudTrail `a6a506dc-4f75-49e7-ab08-5017c17a5a44`.
2. Configurar las variables de repositorio con los outputs de la pila CloudFormation `prueba-cuda-ci`, siguiendo [docs/aws-gpu-ci.md](aws-gpu-ci.md). La conexión GitHub disponible permite editar código, pero no administrar directamente las variables o secretos del repositorio.
3. Una vez AWS Support confirme la retirada de la restricción, habilitar `AWS_CUDA_PROBE_ENABLED=true` y mantener `AWS_CUDA_ENABLED=false` (evita activación de GPU en cada push).
4. Ir a [GitHub Actions — NVIDIA SAXPY 3 ciclos](https://github.com/skyirim/prueba-cuda/actions/workflows/aws-saxpy-three-runs.yml), seleccionar `main`, introducir `EJECUTAR` y ejecutar. Comprobar el resultado de las 3 iteraciones y los artefactos publicados.
5. Solo tras tres éxitos AWS, seguir con comparación en la RTX 2080 Ti del servidor UCAM. No marcar el baseline `VERIFIED` hasta demostrar esa portabilidad real.

## Diagnóstico de la AMI y versiones de CUDA

AMI prevista: `Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04) 20261113` (imagen AWS oficial). Incluye una pila NVIDIA/CUDA, pero la prueba `nvcc --version`, `nvidia-smi` y compilación efectiva no se ha ejecutado en la cuenta por el bloqueo. Si la AMI carece de herramientas, el paso de preparación registrará error y la prueba se marcará fallida, sin declarar compatibilidad inexistente.

La ejecución independiente de pruebas de Python `tests/test_saxpy_three_runs.py` emplea datos de prueba **ficticios expresamente identificados como tales** para comprobar que el verificador rechaza fallos. **No constituyen evidencias de ejecución CUDA en AWS.**
