# whisper.cpp server with NVIDIA CUDA (spec §3.2 STT: whisper.cpp).
#
# Built locally instead of using ghcr.io/ggml-org/whisper.cpp:main-cuda because that image is
# compiled with CPU instructions (AVX-512) that many laptop CPUs lack; it crashes with SIGILL
# (exit 132). This build targets AVX2 CPUs and a chosen set of GPU architectures.
#
#   docker compose -f backend/docker-compose.dev.yml build whisper

ARG CUDA_VERSION=13.0.3
ARG UBUNTU_VERSION=22.04

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS build
ARG WHISPER_CPP_VERSION=v1.9.4
# 75 Turing (RTX 20xx/T4), 80/86 Ampere (A100, RTX 30xx), 89 Ada (RTX 40xx), 90 Hopper.
ARG CUDA_ARCHITECTURES="75;80;86;89"

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential cmake git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch ${WHISPER_CPP_VERSION} https://github.com/ggml-org/whisper.cpp.git .

# The build has no GPU driver; link against the CUDA driver stub.
ENV LIBRARY_PATH=/usr/local/cuda/lib64/stubs
RUN cmake -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_SHARED_LIBS=OFF \
      -DGGML_CUDA=ON \
      -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHITECTURES}" \
      -DGGML_NATIVE=OFF -DGGML_AVX=ON -DGGML_AVX2=ON -DGGML_FMA=ON -DGGML_F16C=ON \
      -DGGML_AVX512=OFF \
      -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON -DWHISPER_SDL2=OFF \
 && cmake --build build --config Release -j"$(nproc)" --target whisper-server

FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION}
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 curl \
 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/whisper-server /usr/local/bin/whisper-server
EXPOSE 8080
ENTRYPOINT ["whisper-server", "--host", "0.0.0.0", "--port", "8080"]
