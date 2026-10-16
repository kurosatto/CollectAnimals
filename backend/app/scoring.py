"""Photo score for a capture, in the spirit of an arcade photo game: points for
how clearly the model recognizes the animal, how sharp the photo is and how well
it's framed, plus bonuses for rare animals and new species. Stars (1-3) come
from the total before bonuses, so a sharp photo of a pigeon can still get 3.

Nothing here rewards getting close. Framing compares the model's confidence on
the middle of the photo with the whole photo, so a cropped or zoomed shot
scores as well as a close one, and animals with a safety rating (caution or
danger) get full framing points without being judged at all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from PIL import Image, ImageFilter, ImageOps, ImageStat

from .classifier import Classifier

CLARITY_MAX = 400
SHARPNESS_MAX = 300
FRAMING_MAX = 300
RARITY_BONUS = {"common": 0, "uncommon": 100, "rare": 250, "legendary": 500}
NEW_SPECIES_BONUS = 200
# Stars from the photo points (clarity + sharpness + framing, out of 1000).
STAR_CUTOFFS = (850, 600)

# Sharpness: how much edge detail a slight blur removes. A blurry photo hardly
# changes (ratio near 1); a crisp one loses a lot. Rough cutoffs, to be tuned
# on real photos.
SHARP_LOW, SHARP_HIGH = 1.3, 3.0
_LAPLACE = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)


@dataclass
class Score:
    total: int
    stars: int
    parts: list[tuple[str, int]] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self.parts)


def _edge_energy(gray: Image.Image) -> float:
    return ImageStat.Stat(gray.filter(_LAPLACE)).var[0]


def sharpness(image: Image.Image) -> float:
    """0..1: 0 for a soft or shaky photo, 1 for a crisp one."""
    gray = ImageOps.grayscale(image)
    gray.thumbnail((512, 512))
    sharp = _edge_energy(gray)
    soft = _edge_energy(gray.filter(ImageFilter.GaussianBlur(1.5)))
    ratio = sharp / max(soft, 1e-6)
    return min(1.0, max(0.0, (ratio - SHARP_LOW) / (SHARP_HIGH - SHARP_LOW)))


def center_crop(image: Image.Image, share: float = 0.6) -> Image.Image:
    w, h = image.size
    cw, ch = int(w * share), int(h * share)
    left, top = (w - cw) // 2, (h - ch) // 2
    return image.crop((left, top, left + cw, top + ch))


def species_probability(model: Classifier, image: Image.Image, slug: str, allowed: set[str]) -> float:
    """The model's probability for this species among the allowed labels."""
    preds = [p for p in model.predict(image, k=1000) if p.label in allowed]
    total = sum(p.probability for p in preds)
    return next((p.probability / total for p in preds if p.label == slug), 0.0) if total > 0 else 0.0


def score_photo(model: Classifier, image: Image.Image, slug: str, allowed: set[str], *,
                confidence: float | None = None, rarity: str = "common", safety: str = "none",
                new_species: bool = False) -> Score:
    """confidence: the model's (state-restricted) probability for this species on
    the whole photo, when the caller already has it."""
    if confidence is None:
        confidence = species_probability(model, image, slug, allowed)
    # Clarity: full points from 95% sure, none at 30% or less.
    clarity = round(CLARITY_MAX * min(1.0, max(0.0, (confidence - 0.3) / 0.65)))
    sharp = round(SHARPNESS_MAX * sharpness(image))
    if safety in ("caution", "danger"):
        framing = FRAMING_MAX
    else:
        middle = species_probability(model, center_crop(image), slug, allowed)
        # Still recognized from the middle alone = the animal is in the frame's
        # center. Capped at the whole-photo confidence, so filling the frame
        # earns nothing extra.
        framing = round(FRAMING_MAX * min(1.0, middle / max(confidence, 0.05)))
    parts = [("Clarity", clarity), ("Sharpness", sharp), ("Framing", framing)]
    photo = clarity + sharp + framing
    stars = 3 if photo >= STAR_CUTOFFS[0] else 2 if photo >= STAR_CUTOFFS[1] else 1
    if RARITY_BONUS.get(rarity):
        parts.append((f"{rarity.capitalize()} animal", RARITY_BONUS[rarity]))
    if new_species:
        parts.append(("New species", NEW_SPECIES_BONUS))
    return Score(total=sum(p for _, p in parts), stars=stars, parts=parts)
