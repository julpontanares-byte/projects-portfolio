from focusbreaker.core.break_activities import BREAK_ACTIVITY_LIBRARY, get_break_activity_suggestions


def test_break_activity_suggestions_respect_mode_and_limit():
    suggestions = get_break_activity_suggestions("normal", limit=3)

    assert len(suggestions) == 3
    assert len(set(suggestions)) == 3
    assert set(suggestions).issubset(set(BREAK_ACTIVITY_LIBRARY["normal"]))


def test_break_activity_suggestions_fallback_to_normal_mode():
    suggestions = get_break_activity_suggestions("unknown-mode", limit=2)

    assert len(suggestions) == 2
    assert set(suggestions).issubset(set(BREAK_ACTIVITY_LIBRARY["normal"]))


def test_break_activity_suggestions_return_all_when_limit_is_large():
    suggestions = get_break_activity_suggestions("focused", limit=99)

    assert suggestions == BREAK_ACTIVITY_LIBRARY["focused"]