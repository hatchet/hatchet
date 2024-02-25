/* Copyright 2024 University of Maryland and other Hatchet Project Developers.
 * See the top-level LICENSE file for details.
 *
 * SPDX-License-Identifier: MIT
 */

#include <iostream>
#include <vector>
#include <cstdlib>
#include <cmath>

double scan(std::vector<double> const& x, std::vector<double>& partials) {
    partials[0] = x[0];
    for (int i = 1; i < x.size(); ++i) {
        partials[i] = partials[i - 1] + x[i];
    }
    return partials[x.size() - 1];
}

double sum(std::vector<double> const& x) {
    double sum = 0.0;
    for (int i = 0; i < x.size(); ++i) {
        sum += x[i];
    }
    return sum;
}

double product(std::vector<double> const& x) {
    double prod = 1.0;
    for (auto const& val : x) {
        prod *= val;
    }
    return prod;
}

double sumOfLog2(std::vector<double> const& x) {
    double sum = 0.0;
    for (auto const& val : x) {
        sum += log2( val );
    }
    return sum;
}


int main() {

    std::vector<double> x(1 << 15), partials(1 << 15);

    for (int i = 0; i < x.size(); ++i) {
        x[i] = std::rand() / (double) RAND_MAX + 1.0;
    }

    std::cout << scan(x, partials) << std::endl;

    std::cout << sum(x) << std::endl;

    auto prod = product(x);
    std::cout << log2( prod ) << std::endl;

    std::cout << sumOfLog2(x) << std::endl;

    return 0;
}
