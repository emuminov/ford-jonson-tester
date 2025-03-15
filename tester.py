import argparse
import os
import pathlib
import sys
import random
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import ceil, log2


class ErrorCode:
    RETURNCODE_ERROR = -1
    NO_NUMBER_OF_COMPARISONS = -2


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


def run_test(executable_path, test_input):
    result = subprocess.run(
        [executable_path] + test_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    inputs = result.args[1:]
    if result.returncode != 0:
        return ErrorCode.RETURNCODE_ERROR, inputs, result.returncode

    found_pattern = re.search(r"^Number of comparisons: [0-9]+$", result.stdout, re.MULTILINE)
    if not found_pattern:
        return ErrorCode.NO_NUMBER_OF_COMPARISONS, inputs, result.returncode

    return int(found_pattern.group(0).split()[3]), inputs, result.returncode


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
    default_testing_sets = (1, 21), (1, 50), (1, 100), (1, 1000)

    for test_set in default_testing_sets:
        print(f"Testing set of {test_set[1]} numbers:")
        test_inputs = [create_test_input(*test_set) for _ in range(1000)]
        results = []
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(run_test, str(args.executable.absolute()), test_input) for test_input in test_inputs
            ]
            for future in as_completed(futures):
                result, inputs, returncode = future.result()

                match result:
                    case ErrorCode.RETURNCODE_ERROR:
                        print(f"Executable failed with {returncode} on input:\n{inputs}", file=sys.stderr)
                        exit(1)
                    case ErrorCode.NO_NUMBER_OF_COMPARISONS:
                        print("Please modify your executable to count the amount of comparisons"
                              "and print them in format: [Number of comparisons: -count-]", file=sys.stderr)
                        exit(1)
                    case _:
                        results.append(result)

        maximal_number_of_comparisons = calculate_number_of_maximal_comparisons(test_set[1])
        print(f"Maximal comparisons allowed: {maximal_number_of_comparisons}")
        print(f"Worst result:                {max(*results)}")
        print(f"Best result:                 {min(*results)}")
        print(f"Average result:              {(sum(results) / len(results)):.1f}")

