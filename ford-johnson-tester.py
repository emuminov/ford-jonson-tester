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
    NO_NUMBER_OF_COMPARISONS_IN_OUTPUT = -2
    NUMBER_OF_COMPARISONS_EXCEEDED = -3
    NO_AFTER_OUTPUT = -4
    OUTPUT_NUMBERS_DIFFER_FROM_INPUT = -5
    OUTPUT_NUMBERS_NOT_SORTED = -6


class C:
    """
    Terminal color codes for easy use.
    """

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
        f"{label}{C.FAIL}{result_str}{C.ENDC}".ljust(ALIGN) + f"{C.FAIL}FAIL{C.ENDC}"
        if maximal_number_of_comparisons < result
        else f"{label}{okcolor}{result_str}{C.ENDC}".ljust(ALIGN) + f"{C.OKGREEN}OK{C.ENDC}"
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
        raise argparse.ArgumentTypeError(
            f"Not a valid range: {C.WARNING}{input_range}{C.ENDC}."
            " Use positive numbers. Format: start-end[, ... start-end]",
        )

    # re.split(r'\s*,\s*', input_range) splits the string by comma and any number of spaces before or after it
    ranges = [extract_range(range_str) for range_str in re.split(r"\s*,\s*", input_range)]
    if not all(ranges):
        raise argparse.ArgumentTypeError(
            f"Not a valid range: {C.WARNING}{input_range}{C.ENDC}. "
            "Use positive numbers. Format: start-end[, ... start-end]",
        )

    return ranges


def bigger_than_zero_int(t: str):
    try:
        res = int(t)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Not a valid times argument: {C.WARNING}{t}{C.ENDC}. Please enter a positive number.",
        ) from e
    if res <= 0:
        raise argparse.ArgumentTypeError(
            f"Not a valid times argument: {C.WARNING}{t}{C.ENDC}. Please enter a positive number.",
        )
    return res


def create_test_input(test_range: range) -> list[str]:
    """
    Takes a range of numbers and convert it to the shuffled list of strings.
    """
    res = list(test_range)
    random.shuffle(res)
    return [str(i) for i in res]


def run_test(executable_path: pathlib.Path, test_input: list[str], output_check: bool):
    result = subprocess.run(
        [executable_path.absolute()] + test_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    inputs = result.args[1:]
    if result.returncode != 0:
        return ErrorCode.RETURNCODE_ERROR, inputs, result.returncode

    cleaned_ouput = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    number_of_comparisons_match = re.search(r"^Number of comparisons: [0-9]+$", cleaned_ouput, re.MULTILINE)
    if not number_of_comparisons_match:
        return ErrorCode.NO_NUMBER_OF_COMPARISONS_IN_OUTPUT, cleaned_ouput

    number_of_comparisons = int(number_of_comparisons_match.group(0).split()[3])
    if number_of_comparisons > maximal_number_of_comparisons:
        return ErrorCode.NUMBER_OF_COMPARISONS_EXCEEDED, inputs, number_of_comparisons

    if output_check:
        valid_output_match = re.search(r"^\s*After:\s*\[?((?:\d+\s*)+)\]?\s*$", cleaned_ouput, re.MULTILINE)
        if not valid_output_match:
            return ErrorCode.NO_AFTER_OUTPUT, cleaned_ouput

        split_output = valid_output_match.group(1).strip().split()
        if len(split_output) != len(test_input):
            return ErrorCode.OUTPUT_NUMBERS_DIFFER_FROM_INPUT, " ".join(split_output), " ".join(test_input)

        expected = [int(n) for n in test_input]
        expected.sort()
        split_output_int = [int(n) for n in split_output]
        if split_output_int != expected:
            return ErrorCode.OUTPUT_NUMBERS_NOT_SORTED, " ".join(split_output), " ".join([str(n) for n in expected])

    return number_of_comparisons, inputs


def represent_range(r: range):
    return f"{C.HEADER}[{r[0]}-{r[-1] + 1}){C.ENDC}"


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

    parser.add_argument(
        "-n",
        "--no-output-check",
        dest="output_check",
        action="store_false",
        help="With this flag enabled, the program won't check the validity of an output and whether it's sorted or not."
        " If you know that the algorithm implementation outputs correct values which are sorted correctly, enabing "
        "this will reduce overhead.",
    )

    parser.add_argument(
        "-c",
        "--no-colors",
        dest="no_colors",
        action="store_true",
        help="Do not add colors to the output of the program. :(",
    )

    one_of_inputs_failed = False
    args = parser.parse_args()
    ranges_to_test = args.ranges

    if args.no_colors:

        class C:
            HEADER = ""
            OKBLUE = ""
            OKCYAN = ""
            OKGREEN = ""
            WARNING = ""
            FAIL = ""
            ENDC = ""

    print(
        f"Running the program {C.WARNING}{args.times}{C.ENDC} times for each of the ranges: "
        f"{', '.join([represent_range(r) for r in args.ranges])}\n",
    )
    for i, test_range in enumerate(ranges_to_test):
        print(f"Testing set of {len(test_range)} numbers:")
        maximal_number_of_comparisons = calculate_number_of_maximal_comparisons(len(test_range))
        test_inputs = [create_test_input(test_range) for _ in range(args.times)]
        results = []
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(run_test, args.executable, test_input, args.output_check) for test_input in test_inputs
            ]
            for future in as_completed(futures):
                result = future.result()

                match result[0]:
                    case ErrorCode.RETURNCODE_ERROR:
                        inputs, returncode = result[1], result[2]
                        print(
                            f"Executable failed with return code {C.FAIL}{returncode}{C.ENDC} "
                            f"on input:\n{C.FAIL}{' '.join(inputs)}{C.WARNING}",
                            file=sys.stderr,
                        )
                        exit(1)

                    case ErrorCode.NO_NUMBER_OF_COMPARISONS_IN_OUTPUT:
                        cleaned_output = result[1]
                        print(
                            "Please modify your executable to count the amount of comparisons "
                            f"and print them in format: "
                            f"{C.WARNING}[Number of comparisons: -count-]{C.ENDC}\n"
                            f"Your output:\n{C.FAIL}{cleaned_output}{C.ENDC}",
                            end="",
                            file=sys.stderr,
                        )
                        exit(1)

                    case ErrorCode.NUMBER_OF_COMPARISONS_EXCEEDED:
                        inputs, number_of_comparisons = result[1], result[2]
                        print(
                            f"Maximal number of comparisons is exceeded on input: "
                            f"{C.FAIL}{number_of_comparisons}{C.ENDC} > "
                            f"{C.WARNING}{maximal_number_of_comparisons}{C.ENDC}\n"
                            f"{' '.join(inputs)}\n",
                            file=sys.stderr,
                        )
                        one_of_inputs_failed = True
                        results.append(number_of_comparisons)

                    case ErrorCode.NO_AFTER_OUTPUT:
                        cleaned_output = result[1]
                        print(
                            "Please modify your executable to print the result of the sort in the output: "
                            f"{C.WARNING}[After: number1, number2, ... numberN]{C.ENDC}\n"
                            f"Your output:\n{C.FAIL}{cleaned_output}{C.ENDC}",
                            end="",
                            file=sys.stderr,
                        )
                        exit(1)

                    case ErrorCode.OUTPUT_NUMBERS_DIFFER_FROM_INPUT:
                        split_output, test_input = result[1], result[2]
                        print(
                            "Numbers in the input are different from numbers in the output! Your program chewed up "
                            f"some of the numbers. Your output:\n{C.FAIL}{split_output}{C.ENDC}\n"
                            f"Input that caused failure:\n{C.WARNING}{test_input}{C.ENDC}",
                            file=sys.stderr,
                        )
                        exit(1)

                    case ErrorCode.OUTPUT_NUMBERS_NOT_SORTED:
                        failed_output, expected_output = result[1], result[2]
                        print(
                            "Your output is not sorted! Your program failed to sort the input. "
                            f"Your output:\n{C.FAIL}{failed_output}{C.ENDC}\n"
                            f"Expected output:\n{C.WARNING}{expected_output}{C.ENDC}",
                            file=sys.stderr,
                        )
                        exit(1)

                    case _:
                        results.append(result[0])

        maximal_number_of_comparisons_str = (
            f"Maximal comparisons allowed: "
            f"F({C.WARNING}{len(test_range)}{C.ENDC}) = "
            f"{C.WARNING}{maximal_number_of_comparisons}{C.ENDC}".ljust(ALIGN)
        )
        worst_result = max(results)
        worst_result_str = format_result("Worst result:                ", worst_result, C.OKGREEN)

        best_result = min(results)
        best_result_str = format_result("Best result:                 ", best_result, C.OKBLUE)

        average_result = sum(results) / len(results)
        average_result_str = format_result("Average result:              ", average_result, C.OKCYAN)

        print(f"{maximal_number_of_comparisons_str}")
        print(f"{worst_result_str}")
        print(f"{best_result_str}")
        print(f"{average_result_str}")
        if i != len(ranges_to_test) - 1:
            print("")

    if one_of_inputs_failed:
        print(f"\n{C.FAIL}SOME OF THE TESTS FAILED{C.ENDC}")
        exit(1)
    else:
        print(f"\n{C.OKGREEN}ALL OF THE TESTS PASSED{C.ENDC}")
