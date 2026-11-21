// Adaptación pedagógica del ejemplo SAXPY de Mark Harris (NVIDIA).
// Fuente: https://developer.nvidia.com/blog/easy-introduction-cuda-c-and-c/
// Licencia de este fichero: MIT (adaptación independiente).
// Resultado esperado: 2 * 1 + 2 = 4, error maximo < 1e-5.
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

#define CHECK_CUDA(expr) do { \
    cudaError_t status_ = (expr); \
    if (status_ != cudaSuccess) { \
        std::fprintf(stderr, "CUDA_ERROR %s:%d: %s\n", \
                     __FILE__, __LINE__, cudaGetErrorString(status_)); \
        std::exit(EXIT_FAILURE); \
    } \
} while (0)

__global__ void saxpy_kernel(int count, float scale,
                             const float *input, float *result) {
    const int index = blockIdx.x * blockDim.x + threadIdx.x;
    if (index < count) {
        result[index] = scale * input[index] + result[index];
    }
}

int main() {
    constexpr int count = (1 << 20);
    constexpr int threads = 256;
    std::vector<float> input(count, 1.0f), output(count, 2.0f);
    float *device_input = nullptr, *device_output = nullptr;

    int device = -1;
    CHECK_CUDA(cudaGetDevice(&device));
    cudaDeviceProp properties{};
    CHECK_CUDA(cudaGetDeviceProperties(&properties, device));
    std::printf("GPU=%s compute_capability=%d.%d\n",
                properties.name, properties.major, properties.minor);

    CHECK_CUDA(cudaMalloc(reinterpret_cast<void **>(&device_input),
                          count * sizeof(float)));
    CHECK_CUDA(cudaMalloc(reinterpret_cast<void **>(&device_output),
                          count * sizeof(float)));
    CHECK_CUDA(cudaMemcpy(device_input, input.data(), count * sizeof(float),
                          cudaMemcpyHostToDevice));
    CHECK_CUDA(cudaMemcpy(device_output, output.data(), count * sizeof(float),
                          cudaMemcpyHostToDevice));

    saxpy_kernel<<<(count + threads - 1) / threads, threads>>>(
        count, 2.0f, device_input, device_output);
    CHECK_CUDA(cudaGetLastError());
    CHECK_CUDA(cudaDeviceSynchronize());
    CHECK_CUDA(cudaMemcpy(output.data(), device_output,
                          count * sizeof(float), cudaMemcpyDeviceToHost));

    float maximum_error = 0.0f;
    for (const float value : output) {
        maximum_error = std::fmax(maximum_error, std::fabs(value - 4.0f));
    }
    std::printf("SAXPY: elementos=%d, error_maximo=%.9f\n",
                count, maximum_error);

    CHECK_CUDA(cudaFree(device_input));
    CHECK_CUDA(cudaFree(device_output));

    if (maximum_error > 0.00001f) {
        std::fprintf(stderr, "SAXPY_FAIL\n");
        return EXIT_FAILURE;
    }
    std::puts("SAXPY_NVIDIA_PASS");
    return EXIT_SUCCESS;
}
