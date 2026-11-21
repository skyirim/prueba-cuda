# AWS — registro de investigación reproducible

**Instantánea del 21-11-2026.** Obtenida mediante AWS EC2 DescribeInstanceTypes, DescribeSpotPriceHistory, Service Quotas GetServiceQuota, DescribeRegions y Price List GetProducts. Tarifas USD/h de Linux/UNIX, tenancy Shared, preInstalledSw=NA y capacitystatus=Used. No se han creado recursos facturables. No asumir que se mantienen precios/soporte/cuotas. La API Price List está disponible en us-east-1; especificar allí el endpoint aunque el producto sea de otra región.

## 1. Hallazgo principal

| Tipo | ISA | CPU / GPU | Oregón Spot más barato | Zona | On-Demand Oregón |
| --- | --- | --- | ---: | --- | ---: |
| g6f.large | x86-64 | 2 vCPU; 1/8 L4, 8 GiB RAM, ~2,79 GiB VRAM | 0,0565 | us-west-2b | 0,2020 |
| g6f.xlarge | x86-64 | 4 vCPU; 1/8 L4, 16 GiB RAM | 0,0741 | us-west-2c | 0,2375 |
| g5g.xlarge | arm64 | 4 vCPU; NVIDIA T4g completa, 8 GiB RAM, 16 GiB VRAM | 0,1069 | us-west-2a | 0,4200 |
| g4dn.xlarge | x86-64 | 4 vCPU; T4 completa, 16 GiB RAM | 0,2149 | us-west-2c | 0,5260 |
| g6.xlarge | x86-64 | 4 vCPU; L4 completa | 0,4852 | us-west-2a | 0,8048 |
| g5.xlarge | x86-64 | 4 vCPU; A10G completa | 0,5515 | us-west-2c | 1,0060 |

En sa-east-1a se observó g6f.large a 0,0460 USD/h pero la cuota Spot G/VT era 0. En us-west-2 la cuota G/VT Spot era 126 vCPU; en us-east-1, eu-central-1 y sa-east-1 era 0. La región eu-south-2 (Madrid) estaba sin opt-in en la cuenta; solo se publicaron tarifas On-Demand sin verificación Spot ni autorización regional. No almacenar IDs de cuenta.

## 2. Familias NVIDIA identificadas

GPU fraccionadas: G6f (L4, 1/8 a 1/2), Gr6f (L4 fraccionada). GPU completas de coste moderado: G5g (T4g con Graviton ARM), G4dn (T4), G5 (A10G), G6 (L4), G6e (L40S), G7 (RTX PRO 4500), G7e (RTX PRO Server 6000), Gr6. Cómputo de alto coste: P3dn V100, P4d/P4de A100, P5 H100/H200, P6 B200/B300. Precios históricos aparecen para G2/G3/G3s/P2/P3 pero **no justifican** su empleo actual con CUDA moderno. **G4ad no sirve como NVIDIA CUDA nativo porque su GPU es AMD.**

La API DescribeInstanceTypes devuelve arquitectura soportada, CPU vCPUs y memoria, modelo GPU, número, memoria y fracción. **No devuelve CUDA cores garantizados ni capacidad Spot libre.**

## 3. Reproducir consultas desde AWS CLI v2

Leer fecha UTC primero. Usar un perfil IAM de solo lectura. Regiones y tipos no deben quedar fijados permanentemente a los de 2026.

~~~bash
date -u +%FT%TZ
aws sts get-caller-identity
aws ec2 describe-regions --all-regions --region us-east-1 \
  --query 'Regions[].{Region:RegionName,OptIn:OptInStatus}'
aws ec2 describe-instance-types --region us-west-2 \
  --instance-types g6f.large g6f.xlarge g5g.xlarge g4dn.xlarge g6.xlarge \
  --query 'InstanceTypes[].{Tipo:InstanceType,CPU:VCpuInfo.DefaultVCpus,Arch:ProcessorInfo.SupportedArchitectures,Mem:MemoryInfo.SizeInMiB,GPU:GpuInfo.Gpus}'
aws ec2 describe-spot-price-history --region us-west-2 \
  --instance-types g6f.large g6f.xlarge g5g.xlarge g4dn.xlarge \
  --product-descriptions Linux/UNIX \
  --max-results 100
aws service-quotas get-service-quota --region us-west-2 \
  --service-code ec2 --quota-code L-3819A6DF
aws ec2 describe-subnets --region us-west-2 \
  --query 'Subnets[].{Az:AvailabilityZone,Id:SubnetId}'
~~~

Spot API es histórico y paginado; filtrar por fecha de referencia, obtener el **último precio por pareja (instancia, AZ)**, no tomar el mínimo histórico como tarifa actual. Las cotizaciones se pueden mover minutos antes de aprovisionar; confirmar cuota y capacidad. Consultar zona por ID para evitar diferencias de mapeo AZ entre cuentas.

~~~bash
aws pricing get-products --region us-east-1 --service-code AmazonEC2 \
 --filters \
 Type=TERM_MATCH,Field=instanceType,Value=g6f.large \
 Type=TERM_MATCH,Field=location,Value="US West (Oregon)" \
 Type=TERM_MATCH,Field=operatingSystem,Value=Linux \
 Type=TERM_MATCH,Field=tenancy,Value=Shared \
 Type=TERM_MATCH,Field=preInstalledSw,Value=NA \
 Type=TERM_MATCH,Field=capacitystatus,Value=Used
~~~

Parsear terms.OnDemand con priceDimensions y unidad Hrs, no el primer SKU sin comprobar filtros. Price List no entrega Spot ni Capacity Blocks. RI/Savings Plans implican compromiso; comparar coste de uso real y no solo tasa equivalente. Service Quotas G/VT se expresa en vCPU de la familia relevante y 0 bloquea el lanzamiento salvo ampliación.

## 4. Coste real y criterios de selección

- Sumar EC2 desde inicio hasta terminación, EBS gp3 (provisión/IOPS extra), almacenamiento AMI/snapshots, IPv4 pública por hora, transferencia, CloudWatch y controlador Lambda/API Gateway/SQS/Secrets Manager si se emplea.
- Para desarrollo por SSH, considerar EBS persistente incluso apagado; para runner efímero, DeleteOnTermination y TTL externos.
- Spot está sujeto a interrupción/capacidad; tener fallback documentado o fallar con información, sin activar On-Demand de forma oculta.
- Mantener máximos por ejecución y mensuales, Budget y alarmas; publicar precio consultado, AZ, duración, número de intentos y coste estimado para cada job.
- El tipo elegido **primero** debe satisfacer equivalencia; si G6f fraccionada no demuestra cores suficientes, comparar GPU completas y permitir tipos mayores. El perfil del documento base prevalece sobre cualquier ranking.

## 5. Fuentes / actualización

- https://docs.aws.amazon.com/ec2/latest/instancetypes/ac.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-spot-instances.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nvidia-GRID-driver.html
- https://aws.amazon.com/ec2/instance-types/g5g/
- https://aws.amazon.com/ec2/instance-types/accelerated-computing/
- https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html
- https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html

**Todos los importes se deben volver a consultar antes de utilizar esta tabla como presupuesto o de lanzar una instancia.**
