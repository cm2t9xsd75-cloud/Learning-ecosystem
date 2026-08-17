from __future__ import annotations

from learning_ecosystem.enums import (
    STRENGTH_RANK,
    ConceptStatus,
    EvidenceStrength,
    EvidenceType,
)
from learning_ecosystem.errors import MasteryNotJustifiedError
from learning_ecosystem.models import Evidence, MasteryCriterion

# A definition restated once (or repeatedly) is not mastery evidence.
_DEFINITION_ONLY_TYPES = frozenset({EvidenceType.RECALL})


def can_mark_mastered(
    evidence: list[Evidence],
    criteria: list[MasteryCriterion] | None = None,
) -> tuple[bool, str]:
    """Return whether evidence can justify `mastered` and a reason.

    AT-07: a concept cannot become mastered from a single repeated definition.
    Mastery also requires at least two evidence items and one non-recall type.
    When criteria exist, each required evidence type must appear at or above
    the criterion's minimum strength.
    """
    if len(evidence) < 2:
        return False, "mastery requires more than one evidence item"

    types = {item.evidence_type for item in evidence}
    if types <= _DEFINITION_ONLY_TYPES:
        return False, "mastery cannot be justified by definition/recall evidence alone"

    if EvidenceType.RECALL in types and len(types) == 1:
        return False, "repeated definitions are not sufficient for mastery"

    if criteria:
        by_type: dict[EvidenceType, EvidenceStrength] = {}
        for item in evidence:
            current = by_type.get(item.evidence_type)
            if current is None or STRENGTH_RANK[item.strength] > STRENGTH_RANK[current]:
                by_type[item.evidence_type] = item.strength
        missing: list[str] = []
        for criterion in criteria:
            observed = by_type.get(criterion.evidence_type)
            if observed is None:
                missing.append(f"{criterion.evidence_type} (none)")
            elif STRENGTH_RANK[observed] < STRENGTH_RANK[criterion.minimum_strength]:
                missing.append(
                    f"{criterion.evidence_type} "
                    f"(have {observed}, need {criterion.minimum_strength})"
                )
        if missing:
            return False, "missing mastery criteria: " + ", ".join(missing)

    return True, "evidence meets mastery policy"


def assert_can_transition(
    target: ConceptStatus,
    evidence: list[Evidence],
    criteria: list[MasteryCriterion] | None = None,
) -> None:
    if target is not ConceptStatus.MASTERED:
        return
    allowed, reason = can_mark_mastered(evidence, criteria)
    if not allowed:
        raise MasteryNotJustifiedError(reason)
