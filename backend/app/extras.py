"""Animals the model can recognise in a state that aren't in its Field Guide yet.

The model is trained on about 200 animals per state, but only the first 100 have
entries and art. species/model_extras.json lists the rest by state. They count as
"not in the collection yet" rather than being dropped, so a photo of one isn't
squeezed onto a look-alike from the Field Guide and wrongly badged.
"""

from __future__ import annotations

import json
from functools import lru_cache

from .config import settings

# The model also knows people, so a selfie isn't matched to an animal.
PERSON_LABEL = "person"


@lru_cache
def _by_state() -> dict[str, frozenset[str]]:
    path = settings.states_json.parent / "model_extras.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {code: frozenset(slugs) for code, slugs in data["states"].items()}


def for_state(code: str) -> frozenset[str]:
    return _by_state().get(code, frozenset())
