import pytest

from app.models import APPLICATION_STATUSES
from app.state_machine import ALLOWED, TransitionResult, can_transition

ALLOWED_RESULT = TransitionResult(allowed=True)
CORRECTION = TransitionResult(allowed=True, correction=True)
REJECTED = TransitionResult(allowed=False, reason="not_allowed")

NORMAL_MOVES = [
    ("applied", "assessment"),
    ("applied", "interview"),
    ("applied", "offer"),
    ("applied", "rejected"),
    ("assessment", "interview"),
    ("assessment", "offer"),
    ("assessment", "rejected"),
    ("interview", "offer"),
    ("interview", "rejected"),
    ("stale", "assessment"),
    ("stale", "interview"),
    ("stale", "offer"),
    ("stale", "rejected"),
]

BACKWARD_OR_FROM_FINAL = [
    ("assessment", "applied"),
    ("interview", "applied"),
    ("interview", "assessment"),
    ("offer", "interview"),
    ("offer", "rejected"),
    ("rejected", "applied"),
    ("rejected", "interview"),
]

def test_rules_cover_every_status():
    assert set(ALLOWED) == set(APPLICATION_STATUSES)


@pytest.mark.parametrize("source", ["manual", "email", "extension", "system"])
@pytest.mark.parametrize(("from_status", "to_status"), NORMAL_MOVES)
def test_normal_moves_are_allowed_for_every_source(from_status, to_status, source):
    assert can_transition(from_status, to_status, source) == ALLOWED_RESULT


@pytest.mark.parametrize("source", ["email", "extension", "system"])
@pytest.mark.parametrize(("from_status", "to_status"), BACKWARD_OR_FROM_FINAL)
def test_automated_sources_cannot_go_backward(from_status, to_status, source):
    assert can_transition(from_status, to_status, source) == REJECTED


@pytest.mark.parametrize(("from_status", "to_status"), BACKWARD_OR_FROM_FINAL)
def test_manual_backward_move_is_a_correction(from_status, to_status):
    assert can_transition(from_status, to_status, "manual") == CORRECTION


def test_only_the_system_marks_stale():
    assert can_transition("applied", "stale", "system") == ALLOWED_RESULT
    assert can_transition("applied", "stale", "email") == REJECTED
    assert can_transition("interview", "stale", "system") == REJECTED
    assert can_transition("applied", "stale", "manual") == CORRECTION


@pytest.mark.parametrize("status", APPLICATION_STATUSES)
def test_same_status_is_not_a_move(status):
    result = can_transition(status, status, "manual")
    assert result == TransitionResult(allowed=False, reason="same_status")


def test_unknown_status_is_rejected():
    result = can_transition("applied", "ghosted", "manual")
    assert result == TransitionResult(allowed=False, reason="unknown_status")
