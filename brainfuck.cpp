#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <stack>
#include <unordered_map>
#include <stdexcept>

// test with: ++++++++++[>++++++++++>+++<<-]>++++.---.+++++++..+++.>++.<++++++++.--------.+++.------.--------.>----------------------.

std::string loadFile(const std::string& filename) {

    std::ifstream file(filename);

    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filename);
    }

    // read file into buffer
    std::stringstream buffer;
    buffer << file.rdbuf();

    file.close();

    return buffer.str();
}

// Build bracket matching map
std::unordered_map<int, int> build_bracket_map(const std::string& code) {
    std::unordered_map<int, int> bracket_map;
    std::stack<int> brackets;

    for (int i = 0; i < static_cast<int>(code.size()); i++) {

        if (code[i] == '[') {
            brackets.push(i);
        }

        else if (code[i] == ']') {

            if (brackets.empty()) {
                throw std::runtime_error(
                    "Unmatched closing bracket at position " +
                    std::to_string(i)
                );
            }

            int opening = brackets.top();
            brackets.pop();

            bracket_map[opening] = i;
            bracket_map[i] = opening;
        }
    }

    if (!brackets.empty()) {
        throw std::runtime_error(
            "Unmatched opening bracket at position " +
            std::to_string(brackets.top())
        );
    }

    return bracket_map;
}

void interpret(const std::string& code) {

    std::vector<int> tape(1, 0);

    int pointer = 0;
    int instruction_pointer = 0;

    // Build bracket map
    auto bracket_map = build_bracket_map(code);

    while (instruction_pointer < static_cast<int>(code.size())) {

        char instruction = code[instruction_pointer];

        switch (instruction) {

            case '>':
                pointer++;

                if (pointer >= static_cast<int>(tape.size())) {
                    tape.resize(tape.size() * 2, 0);
                }
                break;

            case '<':
                if (pointer == 0) {
                    throw std::runtime_error("Tape underflow");
                }

                pointer--;
                break;

            case '+':
                tape[pointer]++;
                break;

            case '-':
                tape[pointer]--;
                break;

            case '.':
                std::cout << static_cast<char>(
                    static_cast<unsigned char>(tape[pointer])
                );
                break;

            case ',':
            {
                char input;

                if (std::cin.get(input)) {
                    tape[pointer] =
                        static_cast<unsigned char>(input);
                }

                break;
            }

            case '[':
                if (tape[pointer] == 0) {
                    instruction_pointer = bracket_map.at(
                        instruction_pointer
                    );
                }
                break;

            case ']':
                if (tape[pointer] != 0) {
                    instruction_pointer = bracket_map.at(
                        instruction_pointer
                    );
                }
                break;
        }

        instruction_pointer++;
    }
}

int main(int argc, char* argv[]) {

    if (argc < 2) {
        std::cerr << "Usage: ./program <filename>\n";
        return 1;
    }

    try {
        std::string code = loadFile(argv[1]);

        interpret(code);
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << '\n';
        return 1;
    }

    return 0;
}
