# Ford-Johnson tester
This is a program that tests the implementation of the [Ford-Johnson algorithm](https://dev.to/emuminov/human-explanation-and-step-by-step-visualisation-of-the-ford-johnson-algorithm-5g91), also known as [merge-insertion sort](https://en.wikipedia.org/wiki/Merge-insertion_sort). The tester was made specifically for testing the exercises from cpp09 module from the common core of the 42 school, where you have to implement this algorithm.

https://github.com/user-attachments/assets/658ca645-9b64-4097-9269-9f833d97e17e

Just drop this single-file script into the directory with your program and run it against its executable.

## Prerequisites
This script requires Python 3.10 to run properly.

It also requires you to modify your program to print on separate lines:
- The sorted sequence. The format should be: `After: {number}, {number}, ... {number}`
- The number of comparisons. Add some variable to your program and increment it each time you compare numbers against each other. Then, print the number of comparisons in the format: `Number of comparisons: {number}`.

It expects something similar to this:
![image](https://github.com/user-attachments/assets/159ba7af-cbfe-45ff-9b9b-171ba739186b)

## Usage
Default usage:
```sh
python3 ford-johnson-tester.py
```

This will run the executable `./PmergeMe` using the default parameters.

You can specify the following CLI options:
```
python3 ford-johnson-tester.py -h                                  # prints help
python3 ford-johnson-tester.py --times={number}                    # how many times to run the executable against every single rage
python3 ford-johnson-tester.py --ranges={[start-end)[, start=end)} # specify ranges of numbers to test with inclusive start and exclusive end
python3 ford-johnson-tester.py --executable={path-to-executable}   # specify the path to the valid executable
python3 ford-johnson-tester.py --no-colors                         # if you hate fun and colors :( (or if you want to redirect stderr to somewhere without fancy styling)
python3 ford-johnson-tester.py --no-output-check                   # DO NOT check if the outputted sequence is sorted and corresponds to the input, use it if you know that your program sorts the number correctly and just want to benchmark it
```

## Example usage:
- Run the program `2000` times on the ranges of `0..21` and `10..40` numbers each.
```
python3 ford-johnson-tester.py --executable=./PmergeMe2 --times=2000 --ranges="0-21, 10-40"
```

- Do the same, but strip the colors and redirect the `stderr` to the `log.txt`.
```
python3 ford-johnson-tester.py --executable=./PmergeMe2 --times=2000 --ranges="0-21, 10-40" --no-colors 2> log.txt
```
