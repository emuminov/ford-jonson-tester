import argparse
import os
import pathlib
import random
import subprocess
from math import ceil, log2


def calculate_number_of_maximal_comparisons(n: int):
    sum = 0
    for k in range(1, n + 1):
        value = (3.0 / 4.0) * k
        sum += ceil(log2(value))
    return sum


def valid_executable(path: str):
    executable_path = pathlib.Path(path)
    if not executable_path.exists() or not executable_path.is_file() or not os.access(executable_path, os.X_OK):
        raise argparse.ArgumentTypeError("Not a valid executable")
    return executable_path


def create_test_input(start: int, end: int):
    """
    start and end are inclusive.
    """
    res = list(range(start, end + 1))
    random.shuffle(res)
    return [str(i) for i in res]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tests the Ford-Johnson algorithm.")
    parser.add_argument(
        "executable",
        metavar="path-to-executable",
        type=valid_executable,
        nargs="?",
        default="./PmergeMe",
        help="Path to the PmergeMe executable to test.",
    )
    args = parser.parse_args()
    testing_sets = (1, 21), (1, 50), (1, 100), (1, 1000)

    for test_set in testing_sets:
        print(f"Testing set of {test_set[1]} numbers:")
        results = []
        for i in range(1, 10001):
            test_input = create_test_input(*test_set)
            # TODO: check the exit code of the program
            result = subprocess.run([args.executable.absolute()] + test_input, stdout=subprocess.PIPE)

            # TODO: check the exit code of grepped
            grepped = subprocess.run(
                ["grep", "-E", "^Number of comparisons: [0-9]+$"], input=result.stdout, stdout=subprocess.PIPE,
            )

            number_of_comparisons = int(grepped.stdout.decode("utf-8").strip("\n").split(" ")[3])
            results.append(number_of_comparisons)
        maximal_number_of_comparisons = calculate_number_of_maximal_comparisons(len(test_input))
        print(f"Maximal comparisons allowed: {maximal_number_of_comparisons}")
        print(f"Worst result:                {max(*results)}")
        print(f"Best result:                 {min(*results)}")
        print(f"Average result:              {sum(results) / len(results)}")
