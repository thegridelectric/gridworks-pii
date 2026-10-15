"""Partner labels: the name a partner knows a house by.

A scheme is a prefix plus a digit count. Its draw list is every number of
that width, shuffled once with a system random source; minting pops the
head. Drawn without replacement, so a label is never reused and says
nothing about the order houses were enrolled in.
"""

from __future__ import annotations

import random


def fresh_draw_list(digits: int, rng: random.Random | None = None) -> list[int]:
    if digits < 1:
        raise ValueError("a label scheme needs at least one digit")
    numbers = list(range(10**digits))
    (rng or random.SystemRandom()).shuffle(numbers)
    return numbers


def format_label(prefix: str, digits: int, number: int) -> str:
    return f"{prefix}{number:0{digits}d}"
