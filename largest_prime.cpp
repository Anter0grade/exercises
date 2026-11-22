
#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <utility>

/*
given N, find the largest prime number between 2 & N,
& find the number of primes

test cases:
input N, Largest prime, Prime count
10 : 7 : 4
100 : 97 : 25
1000 : 997 : 168
10000 : 9973 : 1229
100000 : 99991 : 9592
10^8 : ? : ?
10^8 : 99999989 : 5761455

algorithm considerations:

trial division = O(n * sqrt(n))
10^8 * sqrt(10^8) = 10^12 or 1 trillion operations !!!!

Normal Sieve:
O(NloglogN) {time}
O(N) {space}

// R & L are interval boundaries
Segmented Sieve:
O(sqrt(R)loglogR + (R-L + 1)loglogR) {time}
O(sqrt(R) + R - L + 1) {space}
note: using vector<bool>
*/

/*
Pseudocode:

find base primes up to sqrt(n)
create a segment[low, high]
mark multiples of base primes as composite
count remaining primes & update largest_prime
move to next segment

*/

std::vector<int> generate_base_primes(int limit) {
    std::vector<bool> isPrime(limit + 1, true);

    isPrime[0] = false;

    if (limit >= 1)
        isPrime[1] = false;

    for (int i = 2; i * i <= limit; i++) {
        if (isPrime[i]) {
            for (int j = i * i; j <= limit; j += i) {
                isPrime[j] = false;
            }
        }
    }

    std::vector<int> primes;

    for (int i = 2; i <= limit; i++) {
        if (isPrime[i]) {
            primes.push_back(i);
        }
    }

    return primes;
}

// Segmented sieve
std::pair<long long, long long> segmented_sieve(long long N) {

    if (N < 2) {
        return {-1, 0};
    }

    // generate base primes up to sqrt(N)
    int limit = sqrtl(N);
    std::vector<int> base_primes = generate_base_primes(limit);

    // configure segment size
    const int SEGMENT_SIZE = 1000000;

    std::vector<bool> isPrime(SEGMENT_SIZE);

    long long prime_count = 0;
    long long largest_prime = -1;

    // process segments
    for (long long low = 2; low <= N; low += SEGMENT_SIZE) {

        long long high = std::min(
            low + SEGMENT_SIZE - 1, N
        );

        // Initially assume everything is prime
        std::fill(
            isPrime.begin(),
            isPrime.begin() + (high - low + 1),
            true
        );

        // Mark multiples of base primes
        for (long long p : base_primes) {

            long long start = std::max(
                p * p,
                ((low + p - 1) / p) * p
            );

            if (start > high)
                continue;

            for (long long j = start; j <= high; j += p) {
                isPrime[j - low] = false;
            }
        }

        // count primes & update largest
        for (long long i = low; i <= high; i++) {

            if (isPrime[i - low]) {
                prime_count++;
                largest_prime = i;
            }
        }
    }

    return {largest_prime, prime_count};
}

int main() {

    long long N = 100000000; // pow(10, 8);

    auto [largest_prime, prime_count] = segmented_sieve(N);

    std::cout << "largest prime: ";

    if (largest_prime == -1)
        std::cout << "None\n";
    else
        std::cout << largest_prime << '\n';

    std::cout << "prime count: " << prime_count << '\n';

    return 0;
}
