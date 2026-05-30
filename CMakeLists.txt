cmake_minimum_required(VERSION 3.20)
project(kinematrix_edge CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(BUILD_BENCHMARK "Build benchmark binary" ON)
option(BUILD_TESTS     "Build unit tests"       ON)

add_subdirectory(lib)
add_subdirectory(cli)

if(BUILD_BENCHMARK)
    add_subdirectory(benchmark)
endif()

if(BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.4.0
    )
    FetchContent_MakeAvailable(Catch2)
    include(CTest)
    enable_testing()
    add_subdirectory(tests)
endif()
