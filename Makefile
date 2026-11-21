CC ?= cc
NVCC ?= nvcc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror
NVCCFLAGS ?= -O2 -lineinfo
# Generar cubin nativo Turing y conservar PTX forward-compatible.
# Cubins sm_75 y sm_89 solos no ejecutan sobre A10G (sm_86).
# Para optimizar una GPU concreta se pueden anadir targets nativos,
# manteniendo sm_75 para UCAM y PTX para los destinos posteriores.
CUDA_GENCODE ?= -gencode arch=compute_75,code=sm_75 -gencode arch=compute_75,code=compute_75
.PHONY: all test clean

all: build/hello_c build/cuda_smoke

build:
	mkdir -p build

build/hello_c: src/hello_c.c | build
	$(CC) $(CFLAGS) $< -o $@

build/cuda_smoke: src/cuda_smoke.cu | build
	$(NVCC) $(NVCCFLAGS) $(CUDA_GENCODE) $< -o $@

test: all
	./build/hello_c
	./build/cuda_smoke

clean:
	rm -f build/hello_c build/cuda_smoke
	rmdir build 2>/dev/null || true
