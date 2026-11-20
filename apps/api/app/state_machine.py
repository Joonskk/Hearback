"""Which status changes are allowed (design doc 6.4). Pure Python, no database."""

from dataclasses import dataclass

# Normal forward moves. Offer and rejected are final.
ALLOWED: dict[str, frozenset[str]] = {
    "applied": frozenset({"assessment", "interview", "offer", "rejected", "stale"}),
    "assessment": frozenset({"interview", "offer", "rejected"}),
    "interview": frozenset({"offer", "rejected"}),
    "offer": frozenset(),
    "rejected": frozenset(),
    "stale": frozenset({"assessment", "interview", "offer", "rejected"}),
}

@dataclass(frozen=True)
class TransitionResult:
    allowed: bool
    correction: bool = False
    reason: str | None = None

def _is_normal_move(from_status: str, to_status: str, source: str) -> bool:
    if to_status == "stale" and source != "system":
        return False
    return to_status in ALLOWED[from_status]


def can_transition(from_status: str, to_status: str, source: str) -> TransitionResult:
    if from_status not in ALLOWED or to_status not in ALLOWED:
        return TransitionResult(False, reason="unknown_status")
    if from_status == to_status:
        return TransitionResult(False, reason="same_status")
    if _is_normal_move(from_status, to_status, source):
        return TransitionResult(True)
    if source == "manual":
        return TransitionResult(True, correction=True)
    return TransitionResult(False, reason="not_allowed")
