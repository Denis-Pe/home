#!/bin/python3
"""Mental-math drills for quant interview prep.

Every answer is appended to RESPONSE_PATH as CSV, so progress can be analysed later.
Inside a drill, type "back" to return to the menu, "clear" to clear the screen
or "quit" to exit. Ctrl+C / Ctrl+D also exit and print a session summary.
"""

import csv
import datetime as dt
import operator
import os
import random
import signal
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import reduce
from pathlib import Path

RESPONSE_PATH = Path("~/arithmetic.csv").expanduser()
CSV_HEADER = ["problem_type", "prompt", "right_answer", "user_answer", "delay_seconds", "timestamp", "correct"]

Config = dict[str, object]
Number = Fraction | float


@dataclass
class Response:
    problem_type: str
    prompt: str
    right_answer: str
    user_answer: str
    delay_seconds: float
    timestamp: dt.datetime
    correct: bool


@dataclass(frozen=True)
class Problem:
    prompt: str
    answer: Number
    tolerance: float = 0.0  # relative error allowed; 0 means the answer must be exact
    tag: str | None = None  # overrides the mode's tag (used by mixed mode)

    def check(self, guess: Fraction) -> bool:
        if self.tolerance == 0:
            return guess == self.answer
        return abs(float(guess) - float(self.answer)) <= self.tolerance * abs(float(self.answer))


@dataclass(frozen=True)
class Setting:
    key: str
    label: str
    default: object | Callable[[Config], object]  # may depend on earlier settings
    parse: Callable[[str], object] = int
    valid: Callable[[object, Config], bool] = lambda value, cfg: value >= 1

    def default_for(self, cfg: Config) -> object:
        return self.default(cfg) if callable(self.default) else self.default


@dataclass(frozen=True)
class Mode:
    key: str
    name: str
    tag: str
    generate: Callable[[Config], Problem]
    settings: tuple[Setting, ...] = ()

    def default_config(self) -> Config:
        cfg: Config = {}
        for setting in self.settings:
            cfg[setting.key] = setting.default_for(cfg)
        return cfg


session: list[Response] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rannum(digits: int) -> int:
    return random.randint(10 ** (digits - 1), 10 ** digits - 1)


def draw(cfg: Config, name: str) -> int:
    """Random number whose digit count lies in the configured range for `name`."""
    return rannum(random.randint(cfg[f"{name}_min"], cfg[f"{name}_max"]))


def fmt(x: Number) -> str:
    if isinstance(x, Fraction):
        # Exact answers here always have terminating decimal expansions.
        return str(x.numerator) if x.denominator == 1 else str(float(x))
    return f"{x:.4f}".rstrip("0").rstrip(".")


def parse_answer(raw: str) -> Fraction:
    cleaned = raw.replace(",", "").replace("_", "")
    if not cleaned or "/" in cleaned:  # no typing "3/7" back in fraction mode
        raise ValueError(raw)
    return Fraction(cleaned)


SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def digits(name: str, label: str, default: int) -> tuple[Setting, Setting]:
    return (
        Setting(f"{name}_min", f"Minimum digits for {label}", default),
        Setting(f"{name}_max", f"Maximum digits for {label}", lambda cfg: cfg[f"{name}_min"],
                valid=lambda value, cfg: value >= cfg[f"{name}_min"]),
    )


def tolerance(default: float) -> Setting:
    return Setting("tolerance", "Allowed relative error in percent", default,
                   parse=float, valid=lambda value, cfg: value >= 0)


def operand_settings(default_digits: int) -> tuple[Setting, ...]:
    return (
        *digits("operand", "each operand", default_digits),
        Setting("operands", "Number of operands", 2, valid=lambda value, cfg: value >= 2),
        Setting("decimals", "Decimal places per operand", 0, valid=lambda value, cfg: value >= 0),
    )


# ---------------------------------------------------------------------------
# Problem generators
# ---------------------------------------------------------------------------

def chain(symbol: str, op: Callable[[Fraction, Fraction], Fraction]) -> Callable[[Config], Problem]:
    """Generator for `a op b op c ...` problems, evaluated left to right."""

    def generate(cfg: Config) -> Problem:
        scale = 10 ** cfg["decimals"]
        nums = [Fraction(draw(cfg, "operand"), scale) for _ in range(cfg["operands"])]
        return Problem(f" {symbol} ".join(map(fmt, nums)), reduce(op, nums))

    return generate


def division(cfg: Config) -> Problem:
    divisor, quotient = 1, draw(cfg, "quotient")
    while divisor == 1:  # dividing by one isn't practice
        divisor = draw(cfg, "divisor")
    return Problem(f"{divisor * quotient} ÷ {divisor}", Fraction(quotient))


def power(cfg: Config) -> Problem:
    base, exponent = draw(cfg, "base"), cfg["exponent"]
    return Problem(f"{base}{str(exponent).translate(SUPERSCRIPT)}", Fraction(base ** exponent))


def root(cfg: Config) -> Problem:
    radicand, degree = draw(cfg, "radicand"), cfg["degree"]
    symbol = {2: "√", 3: "∛", 4: "∜"}.get(degree, f"{str(degree).translate(SUPERSCRIPT)}√")
    value = radicand ** (1 / degree)
    if round(value) ** degree == radicand:
        return Problem(f"{symbol}{radicand}", Fraction(round(value)))
    return Problem(f"{symbol}{radicand}", value, cfg["tolerance"] / 100)


def percentage(cfg: Config) -> Problem:
    percent, base = random.randint(1, 99), draw(cfg, "base")
    return Problem(f"{percent}% of {base}", Fraction(percent * base, 100))


def fraction(cfg: Config) -> Problem:
    denominator = random.randint(2, cfg["max_denominator"])
    numerator = random.randint(1, denominator - 1)
    return Problem(f"{numerator}/{denominator}", numerator / denominator, cfg["tolerance"] / 100)


def mixed(cfg: Config) -> Problem:
    mode = MODES_BY_KEY[random.choice(cfg["modes"])]
    return replace(mode.generate(mode.default_config()), tag=mode.tag)


MODES = (
    Mode("a", "addition", "add", chain("+", operator.add), operand_settings(3)),
    Mode("s", "subtraction", "sub", chain("-", operator.sub), operand_settings(3)),
    Mode("m", "multiplication", "mul", chain("×", operator.mul), operand_settings(2)),
    Mode("d", "division", "div", division, (*digits("divisor", "the divisor", 1), *digits("quotient", "the quotient", 3))),
    Mode("e", "exponents", "pow", power, (*digits("base", "the base", 2), Setting("exponent", "Exponent", 2))),
    Mode("r", "roots", "root", root, (*digits("radicand", "the radicand", 3),
                                      Setting("degree", "Root degree", 2, valid=lambda value, cfg: value >= 2),
                                      tolerance(0.1))),
    Mode("p", "percentages", "pct", percentage, digits("base", "the base", 3)),
    Mode("f", "fractions to decimals", "frac", fraction,
         (Setting("max_denominator", "Maximum denominator", 12, valid=lambda value, cfg: value >= 2), tolerance(0.1))),
)
MODES_BY_KEY = {mode.key: mode for mode in MODES}
MODES += (
    Mode("x", "mixed", "mixed", mixed,
         (Setting("modes", "Modes to mix, e.g. \"mdr\"", "".join(MODES_BY_KEY), parse=str.strip,
                  valid=lambda value, cfg: value != "" and all(c in MODES_BY_KEY for c in value)),)),
)
MODES_BY_KEY = {mode.key: mode for mode in MODES}


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def ask(setting: Setting, cfg: Config) -> object:
    default = setting.default_for(cfg)
    print(f"{setting.label} (default {default} if blank):")
    raw = input("> ").strip()
    print("")
    if raw == "":
        return default
    try:
        value = setting.parse(raw)
        if setting.valid(value, cfg):
            return value
    except ValueError:
        pass
    print(f"Invalid input. Using default value of {default}.\n")
    return default


def save(response: Response) -> None:
    session.append(response)
    new_file = not RESPONSE_PATH.exists() or RESPONSE_PATH.stat().st_size == 0
    with RESPONSE_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(CSV_HEADER)
        writer.writerow([response.problem_type, response.prompt, response.right_answer, response.user_answer,
                         response.delay_seconds, response.timestamp, response.correct])


def summarize() -> None:
    if not session:
        return
    by_tag: dict[str, list[Response]] = defaultdict(list)
    for response in session:
        by_tag[response.problem_type].append(response)
    print("\nSession summary:")
    for tag, responses in by_tag.items():
        right = sum(r.correct for r in responses)
        avg = sum(r.delay_seconds for r in responses) / len(responses)
        print(f"  {tag:<5} {right:>3}/{len(responses):<3} correct ({right / len(responses):.0%}), avg {avg:.2f}s")
    print(f"Responses saved to {RESPONSE_PATH}")


def drill(mode: Mode) -> None:
    print(f"{mode.name.capitalize()} mode engaged!")
    cfg: Config = {}
    for setting in mode.settings:
        cfg[setting.key] = ask(setting, cfg)

    while True:
        problem = mode.generate(cfg)
        timestamp = dt.datetime.now()
        start = time.monotonic()
        while True:
            raw = input(f"> {problem.prompt} = ").strip()
            if raw == "back":
                return
            if raw == "quit":
                raise SystemExit(0)
            if raw == "clear":
                os.system("clear")
                continue
            try:
                guess = parse_answer(raw)
                break
            except ValueError:
                print("Invalid input. Try again.")
        delay = time.monotonic() - start
        correct = problem.check(guess)

        save(Response(problem.tag or mode.tag, problem.prompt, fmt(problem.answer), raw, delay, timestamp, correct))
        print(f"{delay:.2f}s | {fmt(problem.answer)} | {'✔✔✔' if correct else '𝔁𝔁𝔁'}\n")


def menu() -> None:
    while True:
        print("Choose mode or type \"quit\". Available:")
        for mode in MODES:
            print(f"  * ({mode.key}) {mode.name}")
        choice = input("> ").strip().lower()
        if choice == "":
            continue
        if choice == "quit":
            return
        if choice == "clear":
            os.system("clear")
            continue
        mode = MODES_BY_KEY.get(choice) or next((m for m in MODES if m.name.startswith(choice)), None)
        if mode is None:
            print("Invalid command\n")
            continue
        print("")
        drill(mode)
        print("")


def main() -> None:
    def terminate(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, terminate)  # kill / service-manager shutdown
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, terminate)

    try:
        menu()
    except (KeyboardInterrupt, EOFError):
        print("")
    finally:
        summarize()


if __name__ == "__main__":
    main()
