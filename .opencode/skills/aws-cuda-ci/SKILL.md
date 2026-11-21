---
name: aws-cuda-ci
description: Implementar, auditar, mantener y diagnosticar GitHub Actions para compilar y ejecutar C/CUDA en EC2 GPU Spot usando OIDC, Systems Manager, S3, CloudWatch y cleanup por TTL.
---

# AWS GPU C CUDA — operación reproducible

1. Leer README.md, AGENTS.md, docs/hardware-base.md, docs/aws-gpu-ci.md, docs/precio-en-arranque.md y docs/codex-review-loop.md.
2. Los mínimos son 12 cores físicos CPU, 4.352 CUDA cores de una GPU completa, 31 GiB RAM, 11.264 MiB VRAM y fuentes C/CUDA compatibles con RTX 2080 Ti sm_75 de la UCAM.
3. Antes de cada EC2 RunInstances, volver a consultar DescribeSpotPriceHistory, cuotas y tipos actuales; minimizar costo sin debilitar requisitos, TTL del plan 60 segundos.
4. Mantener modo qualify aislado, manual y económicamente limitado; nunca convertir evidencia AWS en compatibilidad UCAM sin ejecución comparativa.
5. Usar CloudFormation gpu-ci-base.json (IAM OIDC main, SSM, S3 cifrado, CloudWatch, Lambda TTL), GitHub Actions aws-gpu-ci.yml y scripts/ci.
6. Registrar stdout/stderr de todas las fases, propagar códigos de salida a GitHub, publicar artifacts si falla, conservar S3 temporalmente, terminar siempre EC2 y EBS.
7. No usar tokens permanentes, SSH público, PR sin confianza o AMIs no aprobadas. Las variables AWS_CUDA_ENABLED y AWS_CUDA_PROBE_ENABLED solo se activan tras autorización y verificación.
8. Ejecutar scripts/check_repo.py, unittest y validar plantilla AWS con API; revisar cada comentario de chatgpt-codex-connector iterativamente hasta cero hallazgos.
9. Para problemas en PR de forks, workflows de Code Review Sentinel solo lectura; Issue Sync únicamente desde main confiable.
10. Si la infraestructura no está desplegada o faltan variables, informar claramente que CI GPU es preparada/no operativa, nunca prometer tests CUDA inexistentes.
