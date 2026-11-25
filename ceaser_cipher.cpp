#include <iostream>
#include <string>
#include <map>

// shift alphs
std::map<char, char> alphabets(int shift) {
    std::map<char, char> alphabet;

    for (int i = 'a'; i <= 'z'; i++) {
        char shifted_char = (i - 'a' + shift) % 26 + 'a';
        alphabet[char(i)] = shifted_char;
    }

    return alphabet;
}

std::map<std::string, std::map<char, char>> enc;

void initialize_enc() {
    for (int i = 0; i < 27; i++) {
        enc["alphabet_" + std::to_string(i)] = alphabets(i);
    }
}

std::string encrypt(std::string text, int shift) {
    std::map<char, char> shifted = alphabets(shift);
    std::string result = "";

    for (char c : text) {
        if (shifted.count(c)) {
            result += shifted[c]; // encrypt
        }
        else {
            result += c; // keeps spaces and punctuation intact
        }
    }

    return result;
}

void input_enc() {
    std::string initial;
    std::string shift_input;

    std::cout << "enter unencoded text >:";
    std::getline(std::cin, initial);

    std::cout << "shift by >:";
    std::getline(std::cin, shift_input);
    
    int i = std::stoi(shift_input);

    std::string result = encrypt(initial, i);

    std::cout << "your secret text is >:" << result << std::endl;
}

void input_dec() {
    std::string initial;

    std::cout << "enter encrypted text >:";
    std::getline(std::cin, initial);

    for (int i = 1; i < 27; i++) {
        std::string result = encrypt(initial, i);
        std::cout << "shift " << i << ": " << result << "\n\n";
    }
}

int main() {
    std::string want;

    std::cout << "encrypt(1) or decrypt(2) >:";
    std::getline(std::cin, want);

    if (want == "1") {
        input_enc();
    }
    else if (want == "2") {
        input_dec();
    }

    return 0;
}