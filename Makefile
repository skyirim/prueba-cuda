CC ?= cc
NVCC ?= nvcc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic -Werror
NVCCFLAGS ?= -O2 -lineinfo
.PHONY: all test clean

all: build/hello_c build/cuda_smoke

build:
	mkdir -p build

build/hello_c: src/hello_c.c | build
	$(CC) $(CFLAGS) $< -o $@

build/cuda_smoke: src/cuda_smoke.cu | build
	$(NVCC) $(NVCCFLAGS) $< -o $@

test: all
	./build/hello_c
	./build/cuda_smoke

clean:
	rm -f build/hello_c build/cuda_smoke
	rmdir build 2>/dev/null || true
