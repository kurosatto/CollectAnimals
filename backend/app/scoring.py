"""Photo score for a capture, in the spirit of an arcade photo game: points for
how clearly the model recognizes the animal, how sharp the photo is, how well
it's framed and how well it's lit, plus bonuses for rare animals, new species,
golden-hour light and a soft (out of focus) background. Stars (1-5) come from
the photo itself: the photo points plus the golden hour and soft background
bonuses, but not rarity or new species, so a great photo of a pigeon can still
get 5.

Nothing here rewards getting close. Framing compares the model's confidence on
the middle of the photo with the whole photo, so a cropped or zoomed shot
scores as well as a close one, and animals with a safety rating (caution or
danger) get full framing points without being judged at all.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

from datetime import date, datetime, timedelta, timezone

from PIL import Image, ImageFilter, ImageOps, ImageStat

from .classifier import Classifier

CLARITY_MAX = 350
SHARPNESS_MAX = 250
FRAMING_MAX = 250
LIGHTING_MAX = 150
RARITY_BONUS = {"common": 0, "uncommon": 100, "rare": 250, "legendary": 500}
NEW_SPECIES_BONUS = 200
GOLDEN_HOUR_BONUS = 100
SOFT_BACKGROUND_BONUS = 75
# Golden hour: the sun between a little below and a little above the horizon.
GOLDEN_HOUR_ELEVATION = (-4.0, 8.0)
# Night animals are hard to light well, so they never drop below this share of
# the lighting points.
NIGHT_LIGHTING_FLOOR = 0.6
# Stars (5, 4, 3, 2) from the photo points (clarity + sharpness + framing +
# lighting, out of 1000) plus the golden hour and soft background bonuses.
# A flawless photo gets 5 on its own; a very good one needs good light or a
# soft background to get there.
STAR_CUTOFFS = (950, 800, 650, 450)
MAX_STARS = 5
STAR_PARTS = {"Clarity", "Sharpness", "Framing", "Lighting", "Golden hour", "Soft background"}

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


def stars_for(parts: list[tuple[str, int]] | list[list]) -> int:
    """1-5 stars from a score's parts (also works on scores saved before the
    lighting and bonus parts existed)."""
    points = sum(pts for label, pts in parts if label in STAR_PARTS)
    return next((MAX_STARS - i for i, cut in enumerate(STAR_CUTOFFS) if points >= cut), 1)


def lighting(image: Image.Image) -> float:
    """0..1: 1 for a well exposed photo; less when it's too dark or too bright,
    when highlights or shadows are blown out, or when it's flat and hazy."""
    gray = ImageOps.grayscale(image)
    gray.thumbnail((256, 256))
    hist = gray.histogram()
    n = sum(hist)
    mean = sum(i * c for i, c in enumerate(hist)) / n
    std = math.sqrt(sum(c * (i - mean) ** 2 for i, c in enumerate(hist)) / n)
    blown = sum(hist[250:]) / n
    crushed = sum(hist[:6]) / n

    def ramp(x: float, zero: float, full: float) -> float:
        return min(1.0, max(0.0, (x - zero) / (full - zero)))

    # Mean brightness: fine from 70 to 190, nothing below 20 or above 240.
    level = min(ramp(mean, 20, 70), ramp(mean, 240, 190))
    # Up to 2% clipped is normal (sky, specular glints); half the points gone at 20%.
    clipping = 1.0 - 0.5 * ramp(blown + crushed, 0.02, 0.20)
    # Low contrast = fog, haze or shooting through glass.
    contrast = 0.5 + 0.5 * ramp(std, 15, 40)
    return level * clipping * contrast


def soft_background(image: Image.Image) -> bool:
    """A crisp middle on a blurred background (shallow depth of field). Judged
    from sharpness alone, so zooming in from afar counts as much as being close."""
    w, h = image.size
    bw, bh = max(1, w // 6), max(1, h // 6)
    border = [image.crop(box) for box in ((0, 0, w, bh), (0, h - bh, w, h),
                                          (0, bh, bw, h - bh), (w - bw, bh, w, h - bh))]
    border_sharp = sum(sharpness(b) for b in border) / len(border)
    return sharpness(center_crop(image, 0.5)) >= 0.6 and border_sharp <= 0.15


def _us_dst(local: datetime) -> bool:
    """US daylight saving time: 2am on the second Sunday of March to 2am on the
    first Sunday of November (local time)."""
    def nth_sunday(month: int, n: int) -> datetime:
        first = date(local.year, month, 1)
        day = first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (n - 1))
        return datetime(day.year, day.month, day.day, 2)
    naive = local.replace(tzinfo=None)
    return nth_sunday(3, 2) <= naive < nth_sunday(11, 1)


def to_utc(when: datetime, std_offset: int) -> datetime:
    """A photo time in UTC. EXIF times have no zone: they're the phone's local
    time, taken to be the state's (standard offset + US daylight saving)."""
    if when.tzinfo is not None:
        return when.astimezone(timezone.utc)
    offset = std_offset + (1 if _us_dst(when) else 0)
    return (when - timedelta(hours=offset)).replace(tzinfo=timezone.utc)


def sun_elevation(when: datetime, lat: float, lon: float) -> float:
    """Degrees of the sun above the horizon (NOAA's approximate formula, good
    to well under a degree). `when` must be timezone aware."""
    t = when.astimezone(timezone.utc)
    hour = t.hour + t.minute / 60 + t.second / 3600
    g = 2 * math.pi / 365 * (t.timetuple().tm_yday - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                       - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    solar_minutes = hour * 60 + eqtime + 4 * lon
    ha = math.radians(solar_minutes / 4 - 180)
    phi = math.radians(lat)
    cos_zenith = math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1.0, min(1.0, cos_zenith))))


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
                new_species: bool = False, activity: str = "day",
                sun: float | None = None) -> Score:
    """confidence: the model's (state-restricted) probability for this species on
    the whole photo, when the caller already has it. activity: "day", "night" or
    "any" (dex.activity). sun: the sun's elevation in degrees when and where the
    photo was taken, if known."""
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
    light = lighting(image)
    if activity == "night":
        light = max(light, NIGHT_LIGHTING_FLOOR)
    lit = round(LIGHTING_MAX * light)
    parts = [("Clarity", clarity), ("Sharpness", sharp), ("Framing", framing), ("Lighting", lit)]
    if RARITY_BONUS.get(rarity):
        parts.append((f"{rarity.capitalize()} animal", RARITY_BONUS[rarity]))
    if new_species:
        parts.append(("New species", NEW_SPECIES_BONUS))
    if sun is not None and GOLDEN_HOUR_ELEVATION[0] <= sun <= GOLDEN_HOUR_ELEVATION[1]:
        parts.append(("Golden hour", GOLDEN_HOUR_BONUS))
    if soft_background(image):
        parts.append(("Soft background", SOFT_BACKGROUND_BONUS))
    return Score(total=sum(p for _, p in parts), stars=stars_for(parts), parts=parts)
