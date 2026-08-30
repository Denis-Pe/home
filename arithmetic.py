#!/bin/python3

from functools import *
import signal
import os
import sys
import time
from dataclasses import dataclass
import datetime as dt
import random
import csv
from pathlib import Path

RESPONSE_PATH = "~/arithmetic.csv"


@dataclass
class Response:
    problem_type: str
    prompt: str
    right_answer: str
    user_answer: str
    delay_seconds: float
    timestamp: dt.datetime
    correct: bool


_shutting_down = False

all_responses: list[Response] = []


def shutdown(signum=None, frame=None):
    global _shutting_down

    if _shutting_down:
        return

    _shutting_down = True
    print("\nShutting down...")
    path = os.path.expanduser(RESPONSE_PATH)

    try:
        with open(path, "a") as f:
            writer = csv.writer(f)
            if os.path.exists(path) and os.path.getsize(path) == 0:
                writer.writerow(
                    ["problem_type", "prompt", "right_answer", "user_answer", "delay_seconds", "timestamp", "correct"])
            for response in all_responses:
                writer.writerow([response.problem_type, response.prompt, response.right_answer, response.user_answer,
                                 response.delay_seconds, response.timestamp, response.correct])

        print(f"Done writing responses to {path}")
    finally:
        sys.stdout.flush()
        raise SystemExit(0)


def handle_signals():
    signal.signal(signal.SIGINT, shutdown)  # Ctrl+C
    signal.signal(signal.SIGTERM, shutdown)  # kill / service-manager shutdown

    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, shutdown)


def rannum(digits):
    return random.randint(10 ** (digits - 1), 10 ** digits - 1)


def multiplication():
    global all_responses
    min_digits = None
    max_digits = None
    noperands = None
    print("Multiplication mode engaged!")
    print("Enter minimum digits for each operand (default 2 if blank):")
    min_digits = input("> ")
    if min_digits == "":
        min_digits = 2
    else:
        try:
            min_digits = int(min_digits)
        except ValueError:
            print("Invalid input. Using default value of 2.")
            min_digits = 2
    print("")
    print("Enter maximum digits for each operand (default same as minimum if blank):")
    max_digits = input("> ")
    if max_digits == "":
        max_digits = min_digits
    else:
        try:
            max_digits = int(max_digits)
            if max_digits < min_digits:
                print(f"Invalid input. Using default value of {min_digits}.")
                max_digits = min_digits
        except ValueError:
            print(f"Invalid input. Using default value of {min_digits}.")
            max_digits = min_digits
    print("")
    print("Enter number of operands (default 2 if blank):")
    noperands = input("> ")
    if noperands == "":
        noperands = 2
    else:
        try:
            noperands = int(noperands)
            if noperands < 2:
                print(f"Invalid input. Using default value of {2}.")
                noperands = 2
        except ValueError:
            print(f"Invalid input. Using default value of {min_digits}.")
            noperands = 2

    response = ""
    while True:
        operands = []
        print("")
        for _ in range(noperands):
            digits = random.randint(min_digits, max_digits)
            operands.append(rannum(digits))
        problem = ' * '.join(map(str, operands))
        right_answer = reduce(lambda x, y: x * y, operands)
        print(f"> {problem} = ", end="")
        start = time.time()
        timestamp = dt.datetime.now()
        response = input()
        if response == "back":
            return
        elif response == "quit":
            shutdown()
        elif response == "clear":
            os.system("clear")
            continue
        try:
            response = int(response)
        except ValueError:
            print("Invalid input. Let's try another problem...")
            continue
        end = time.time()
        delay = end - start
        correct = response == right_answer

        all_responses.append(
            Response("mul", problem, str(right_answer), str(response), delay, timestamp, correct))

        print(f"{delay:.2f}s | {right_answer} | ", end="")

        if correct:
            print("✔✔✔")
        else:
            print("𝔁𝔁𝔁")


def division():
    pass


def addition():
    pass


def subtraction():
    pass


def main():
    handle_signals()

    try:
        response = ""
        while True:
            try:
                print("Choose mode or type \"quit\". Available:")
                print("  * (m)ultiplication")
                print("  * (d)ivision")
                print("  * (a)ddition")
                print("  * (s)ubtraction")
                response = input("> ")
            except EOFError:
                shutdown()
                break
            while response == "":
                response = input("> ")

            print("")
            command = response[0]
            if command == "m":
                multiplication()
            elif command == "d":
                division()
            elif command == "a":
                addition()
            elif command == "s":
                subtraction()
            elif response == "clear":
                os.system("clear")
            elif response == "quit":
                shutdown()
            else:
                print("Invalid command")
                continue
    finally:
        shutdown()


if __name__ == "__main__":
    main()
