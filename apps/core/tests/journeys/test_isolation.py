"""Walk all identifier-bearing app URLs against both foreign owner/actor pairs."""

import pytest

from apps.core.tests.journeys.isolation_data import owner_bundle, second_journey
from apps.core.tests.journeys.isolation_walk import record_walk, walk_foreign_routes

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "target_index,actor_kind",
    [(0, "staff"), (0, "learner"), (1, "staff"), (1, "learner")],
)
def test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner(
    journey: tuple, target_index: int, actor_kind: str
) -> None:
    """Check trainers A/B and trainees A/B against real foreign objects."""
    owners = (owner_bundle(journey), owner_bundle(second_journey(journey)))
    actor, target = owners[1 - target_index], owners[target_index]
    evidence = walk_foreign_routes((actor[actor_kind], actor_kind), target)
    record_walk(f"target_{target_index}_{actor_kind}", evidence)
