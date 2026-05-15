add_executable(test_kinematrix
    test_spline.cpp
    test_ik.cpp
    test_csv.cpp
    ${CMAKE_SOURCE_DIR}/cli/csv_parser.cpp
)
target_link_libraries(test_kinematrix PRIVATE kinematrix Catch2::Catch2WithMain)
target_include_directories(test_kinematrix PRIVATE ${CMAKE_SOURCE_DIR}/cli)

include(Catch)
catch_discover_tests(test_kinematrix)
