#include "csv_parser.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

static bool isNumericToken(const std::string& s) {
    if (s.empty()) return false;
    try { std::stod(s); return true; }
    catch (...) { return false; }
}

static std::vector<Point3> parseStream(std::istream& in) {
    std::vector<Point3> pts;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        std::istringstream ss(line);
        std::string tok;
        std::vector<std::string> fields;
        while (std::getline(ss, tok, ','))
            fields.push_back(tok);

        if (fields.empty()) continue;
        if (!isNumericToken(fields[0])) continue;  // header row

        if (fields.size() < 3)
            throw std::runtime_error("CSV row has fewer than 3 columns: " + line);

        try {
            pts.push_back({std::stod(fields[0]),
                           std::stod(fields[1]),
                           std::stod(fields[2])});
        } catch (...) {
            throw std::runtime_error("Non-numeric value in CSV row: " + line);
        }
    }
    return pts;
}

std::vector<Point3> CsvParser::parseString(const std::string& content) {
    std::istringstream ss(content);
    return parseStream(ss);
}

std::vector<Point3> CsvParser::parseFile(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("Cannot open file: " + path);
    return parseStream(f);
}
