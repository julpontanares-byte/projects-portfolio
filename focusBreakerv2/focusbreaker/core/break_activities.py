"""Suggested activities shown during breaks."""

from __future__ import annotations

import random


BREAK_ACTIVITY_LIBRARY = {
    "normal": [
        "Stand up and stretch your shoulders for 30 seconds.",
        "Drink a glass of water before your next task.",
        "Look away from the screen and rest your eyes.",
        "Walk around the room or down the hall once.",
        "Take 3 slow breaths and unclench your jaw.",
        "Write down the next tiny step for your task.",
    ],
    "strict": [
        "Breathe slowly and let your shoulders drop.",
        "Step away from the desk and walk a few minutes.",
        "Sip water and relax your hands.",
        "Do a gentle neck roll and reset your posture.",
        "Close your eyes for a short, quiet pause.",
        "Avoid screens and give your attention a real reset.",
    ],
    "focused": [
        "Get up and take a short reset walk.",
        "Refill your water or tea before returning.",
        "Stretch your back and open your chest.",
        "Write the next move for your project before you resume.",
        "Take a few calm breaths and let your brain cool down.",
        "Step away from notifications for a moment.",
    ],
}


def get_break_activity_suggestions(mode: str, limit: int = 3) -> list[str]:
    """Return a small, randomized list of break-time activity suggestions."""

    if limit <= 0:
        return []

    pool = BREAK_ACTIVITY_LIBRARY.get(mode, BREAK_ACTIVITY_LIBRARY["normal"])
    if limit >= len(pool):
        return list(pool)

    return random.sample(pool, limit)