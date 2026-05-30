#pragma once
#include "kinematrix/types.hpp"
#include <string>
#include <vector>

class CsvParser {
public:
    static std::vector<Point3> parseFile(const std::string& path);
    static std::vector<Point3> parseString(const std::string& content);
};
