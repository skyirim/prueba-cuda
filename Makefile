CC ?= cc
NVCC ?= nvcc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror
NVCCFLAGS ?= -O2 -lineinfo
# nvcc AWS >=12.2 para L4 sm_89. En el servidor UCAM, si nvcc es más
# antiguo, pasar CUDA_GENCODE="-gencode arch=compute_75,code=sm_75".
CUDA_GENCODE ?= -gencode arch=compute_75,code=sm_75 -gencode arch=compute_89,code=sm_89
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
