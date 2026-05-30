FROM --platform=linux/arm64 ubuntu:22.04
RUN apt-get update && apt-get install -y cmake build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN mkdir build-arm && cd build-arm && \
    cmake .. -DBUILD_TESTS=OFF -DCMAKE_BUILD_TYPE=Release && \
    cmake --build . -j4
CMD ["./build-arm/benchmark/kinematrix_bench"]
