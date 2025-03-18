import argparse
import os
import pathlib
import random
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import ceil, log2


class ErrorCode:
    RETURNCODE_ERROR = -1
    NO_NUMBER_OF_COMPARISONS = -2


class TermColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


ALIGN = 50


def format_result(label: str, result: int | float, okcolor: str):
    type_of_result = type(result)
    result_str = ""
    if type_of_result is int:
        result_str = f"{result}"
    elif type_of_result is float:
        result_str = f"{result:.1f}"
    return (
        f"{label}{TermColors.FAIL}{result_str}{TermColors.ENDC}".ljust(ALIGN)
        + f"{TermColors.FAIL}FAIL{TermColors.ENDC}"
        if maximal_number_of_comparisons < result
        else f"{label}{okcolor}{result_str}{TermColors.ENDC}".ljust(ALIGN) + f"{TermColors.OKGREEN}OK{TermColors.ENDC}"
    )


def calculate_number_of_maximal_comparisons(n: int):
    sum = 0
    for k in range(1, n + 1):
        value = (3.0 / 4.0) * k
        sum += ceil(log2(value))
    return sum


def valid_executable(path: str):
    """
    Validates the executable argument: it should exist and it should be executable.
    """
    executable_path = pathlib.Path(path)
    if not executable_path.exists() or not executable_path.is_file() or not os.access(executable_path, os.X_OK):
        raise argparse.ArgumentTypeError("Not a valid executable")
    return executable_path


def extract_range(range_str: str):
    """
    Converts a hyphen-separated string representation of a range to an actual range.
    Example: '50-100' -> range(50, 100)
    """
    range_list = range_str.split("-")
    if range_list[0] == range_list[1]:
        return None
    return range(int(range_list[0]), int(range_list[1]))


def valid_range(input_range: str):
    """
    Validates the format of the range argument: it should be:
    {positive number}-{positive number}[, {positive number}-{positive number}].
    """
    # ^\d+-\d+                     matches string that starts with {positive number}-{positive number}

    # (?:,\s*\d+-\d+)*$            that string can additionally have any number of comma separated
    #                              {positive number}-{positive number}
    pattern = r"^\d+-\d+(?:,\s*\d+-\d+)*$"
    if not re.fullmatch(pattern, input_range):
        raise argparse.ArgumentTypeError(f"Not a valid range: {TermColors.WARNING}{input_range}{TermColors.ENDC}."
                                          " Use positive numbers. Format: start-end[, ... start-end]")

    # re.split(r'\s*,\s*', input_range) splits the string by comma and any number of spaces before or after it
    ranges = [extract_range(range_str) for range_str in re.split(r"\s*,\s*", input_range)]
    if not all(ranges):
        raise argparse.ArgumentTypeError(f"Not a valid range: {TermColors.WARNING}{input_range}{TermColors.ENDC}. "
                                          "Use positive numbers. Format: start-end[, ... start-end]")

    return ranges


def bigger_than_zero_int(times: str):
    try:
        res = int(times)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Not a valid times argument: {TermColors.WARNING}{times}{TermColors.ENDC}."
                                          " Please enter a positive number.") from e
    if res <= 0:
        raise argparse.ArgumentTypeError(f"Not a valid times argument: {TermColors.WARNING}{times}{TermColors.ENDC}."
                                          " Please enter a positive number.")
    return res


def create_test_input(test_range: range) -> list[str]:
    """
    Takes a range of numbers and convert it to the shuffled list of strings.
    """
    res = list(test_range)
    random.shuffle(res)
    return [str(i) for i in res]


def run_test(executable_path: pathlib.Path, test_input: list[str]):
    result = subprocess.run(
        [executable_path.absolute()] + test_input,
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

    number_of_comparisons = int(found_pattern.group(0).split()[3])
    return number_of_comparisons, inputs, result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Ford-Johnson tester",
        description="Tests if an implementation of the Ford-Johnson algorithm exceeds allowed number of comparisons "
        "and sorts the input properly.",
    )

    parser.add_argument(
        "-e",
        "--executable",
        dest="executable",
        metavar="EXECUTABLE",
        type=valid_executable,
        default="./PmergeMe",
        help="Path to the PmergeMe executable to test. Default: %(default)s",
    )

    parser.add_argument(
        "-r",
        "--ranges",
        dest="ranges",
        metavar="RANGES",
        type=valid_range,
        default="0-10, 0-15, 0-18, 0-19, 0-20, 0-21, 0-23, 0-25, 0-30, 0-50, 0-100",
        help="Ranges of non-negative numbers that get shuffled and used on the executable.\n"
        "Use format: [start-end)[, ... [start-end)] Default: %(default)s",
    )

    parser.add_argument(
        "-t",
        "--times",
        dest="times",
        metavar="TIMES",
        type=bigger_than_zero_int,
        default=1000,
        help="How many times to run the executable for each of the given ranges. Default: %(default)s",
    )

    one_of_inputs_failed = False
    args = parser.parse_args()
    ranges_to_test = args.ranges

    for i, test_range in enumerate(ranges_to_test):
        print(f"Testing set of {len(test_range)} numbers:")
        maximal_number_of_comparisons = calculate_number_of_maximal_comparisons(len(test_range))
        test_inputs = [create_test_input(test_range) for _ in range(args.times)]
        results = []
        with ProcessPoolExecutor() as executor:
            futures = [executor.submit(run_test, args.executable, test_input) for test_input in test_inputs]
            for future in as_completed(futures):
                result, inputs, returncode = future.result()

                match result:
                    case ErrorCode.RETURNCODE_ERROR:
                        print(
                            f"Executable failed with {returncode} on input:\n{' '.join(inputs)}",
                            file=sys.stderr,
                        )
                        exit(1)

                    case ErrorCode.NO_NUMBER_OF_COMPARISONS:
                        print(
                            "Please modify your executable to count the amount of comparisons"
                            "and print them in format: [Number of comparisons: -count-]",
                            file=sys.stderr,
                        )
                        exit(1)

                    case _:
                        if result > maximal_number_of_comparisons:
                            print(
                                f"Maximal number of comparisons is exceeded on input:\n{' '.join(inputs)}\n",
                                file=sys.stderr,
                            )
                            one_of_inputs_failed = True
                        results.append(result)

        maximal_number_of_comparisons_str = (
            f"Maximal comparisons allowed: "
            f"F({TermColors.WARNING}{len(test_range)}{TermColors.ENDC}) = "
            f"{TermColors.WARNING}{maximal_number_of_comparisons}{TermColors.ENDC}".ljust(ALIGN)
        )
        worst_result = max(results)
        worst_result_str = format_result("Worst result:                ", worst_result, TermColors.OKGREEN)

        best_result = min(results)
        best_result_str = format_result("Best result:                 ", best_result, TermColors.OKBLUE)

        average_result = sum(results) / len(results)
        average_result_str = format_result("Average result:              ", average_result, TermColors.OKCYAN)

        print(f"{maximal_number_of_comparisons_str}")
        print(f"{worst_result_str}")
        print(f"{best_result_str}")
        print(f"{average_result_str}")
        if i != len(ranges_to_test) - 1:
            print("")

    if one_of_inputs_failed:
        print(f"\n{TermColors.FAIL}SOME OF THE TESTS FAILED{TermColors.ENDC}")
        exit(1)
    else:
        print(f"\n{TermColors.OKGREEN}ALL OF THE TESTS PASSED{TermColors.ENDC}")

