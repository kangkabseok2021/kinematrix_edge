add_library(kinematrix STATIC
    src/spline.cpp
    src/ik.cpp
)
target_include_directories(kinematrix PUBLIC include)
target_compile_options(kinematrix PRIVATE -Wall -Wextra)
