/* Prueba CUDA real: inventario, transferencia, kernel y sincronizacion. */
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>

static void check(cudaError_t code, const char *action)
{
    if (code != cudaSuccess) {
        std::fprintf(stderr, "CUDA error en %s: %s\n", action, cudaGetErrorString(code));
        std::exit(EXIT_FAILURE);
    }
}

__global__ void sumar(const int *a, const int *b, int *c, int n)
{
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        c[i] = a[i] + b[i];
    }
}

int main()
{
    int devices = 0;
    check(cudaGetDeviceCount(&devices), "cudaGetDeviceCount");
    if (devices < 1) {
        std::fprintf(stderr, "No hay GPU CUDA accesible.\n");
        return EXIT_FAILURE;
    }

    cudaDeviceProp prop = {};
    check(cudaGetDeviceProperties(&prop, 0), "cudaGetDeviceProperties");
    const auto vram_mib = static_cast<unsigned long long>(prop.totalGlobalMem / (1024ULL * 1024ULL));
    std::printf("GPU: %s; SM visibles: %d; VRAM: %llu MiB; CC: %d.%d\n",
                prop.name, prop.multiProcessorCount, vram_mib, prop.major, prop.minor);
    std::puts("ATENCION: multiProcessorCount NO demuestra por si solo CUDA cores efectivos de una vGPU.");

    constexpr int n = 256;
    constexpr size_t bytes = n * sizeof(int);
    int a[n], b[n], c[n] = {};
    for (int i = 0; i < n; i++) {
        a[i] = i;
        b[i] = n - i;
    }
    int *da = nullptr, *db = nullptr, *dc = nullptr;
    check(cudaMalloc(reinterpret_cast<void **>(&da), bytes), "cudaMalloc(a)");
    check(cudaMalloc(reinterpret_cast<void **>(&db), bytes), "cudaMalloc(b)");
    check(cudaMalloc(reinterpret_cast<void **>(&dc), bytes), "cudaMalloc(c)");
    check(cudaMemcpy(da, a, bytes, cudaMemcpyHostToDevice), "cudaMemcpy(a)");
    check(cudaMemcpy(db, b, bytes, cudaMemcpyHostToDevice), "cudaMemcpy(b)");
    sumar<<<(n + 127) / 128, 128>>>(da, db, dc, n);
    check(cudaGetLastError(), "lanzamiento kernel");
    check(cudaDeviceSynchronize(), "cudaDeviceSynchronize");
    check(cudaMemcpy(c, dc, bytes, cudaMemcpyDeviceToHost), "cudaMemcpy(c)");
    for (int i = 0; i < n; i++) {
        if (c[i] != n) {
            std::fprintf(stderr, "ERROR: indice %d, resultado %d, esperado %d\n", i, c[i], n);
            return EXIT_FAILURE;
        }
    }
    check(cudaFree(da), "cudaFree(a)");
    check(cudaFree(db), "cudaFree(b)");
    check(cudaFree(dc), "cudaFree(c)");
    std::puts("CUDA: kernel ejecutado y 256 resultados validados.");
    return EXIT_SUCCESS;
}
