add_executable(kinematrix_cli
    csv_parser.cpp
    main.cpp
)
target_link_libraries(kinematrix_cli PRIVATE kinematrix)
