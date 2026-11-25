#include <iostream>
#include <string>
#include <cstdlib>
#include <ctime>

bool luhn_check(std::string card_number) {
    int sum = 0;
    bool double_digit = false;

    // Start from the rightmost digit
    for (int i = card_number.length() - 1; i >= 0; i--) {
        int digit = card_number[i] - '0';

        if (double_digit) {
            digit *= 2;

            if (digit > 9) {
                digit -= 9;
            }
        }

        sum += digit;
        double_digit = !double_digit;
    }

    return sum % 10 == 0;
}

// Fill everything except the check digit with random digits,
// then try 0-9 and keep whichever one luhn_check accepts.
std::string generate_card(std::string prefix, int length) {
    std::string card_number = prefix;

    while (card_number.length() < length - 1) {
        card_number += (char)('0' + rand() % 10);
    }

    for (int d = 0; d <= 9; d++) {
        std::string candidate = card_number + (char)('0' + d);

        if (luhn_check(candidate)) {
            return candidate;
        }
    }

    return card_number; // unreachable, exactly one digit always passes
}

int main() {

    srand((unsigned)time(NULL));
    
    for (int i=0; i<10; i++){

    // "424242" is a standard visa test BIN
    std::string card = generate_card("424242", 16);

    std::cout << card << ": ";

    if (luhn_check(card)) {
        std::cout << "passes\n\n";
    } else {
        std::cout << "failed\n\n";
    }
}

    return 0;
}