import random
from datetime import datetime, timezone

from PIL import Image, ImageDraw, ImageFilter

from app import scoring
from app.classifier import Prediction


class CenterOnly:
    """Sure it's a coyote on the whole photo; `middle` is how sure on the center crop."""

    def __init__(self, middle):
        self.middle = middle
        self.size = None

    def predict(self, image, k=3):
        if self.size is None:
            self.size = image.size
        p = 0.95 if image.size == self.size else self.middle
        return [Prediction("coyote", p), Prediction("gray_fox", 1 - p)][:k]


def busy_photo():
    rng = random.Random(1)
    im = Image.new("RGB", (400, 300), "white")
    d = ImageDraw.Draw(im)
    for _ in range(300):
        x, y = rng.randrange(400), rng.randrange(300)
        d.rectangle((x, y, x + rng.randrange(2, 12), y + rng.randrange(2, 12)),
                    fill=tuple(rng.randrange(256) for _ in range(3)))
    return im


def test_blurry_photo_scores_lower_on_sharpness():
    sharp = busy_photo()
    assert scoring.sharpness(sharp) > 0.8
    assert scoring.sharpness(sharp.filter(ImageFilter.GaussianBlur(4))) < 0.2


def test_score_parts_stars_and_bonuses():
    allowed = {"coyote", "gray_fox"}
    s = scoring.score_photo(CenterOnly(0.95), busy_photo(), "coyote", allowed, rarity="rare", new_species=True)
    labels = dict(s.parts)
    assert labels["Clarity"] == scoring.CLARITY_MAX and labels["Framing"] == scoring.FRAMING_MAX
    assert labels["Rare animal"] == 250 and labels["New species"] == 200
    # Mostly white, so lighting is poor: 4 stars.
    assert s.stars == 4 and s.total == sum(labels.values())

    # Off-center animal: framing drops, no bonus for a common repeat.
    s = scoring.score_photo(CenterOnly(0.2), busy_photo(), "coyote", allowed)
    labels = dict(s.parts)
    assert labels["Framing"] < 100 and "New species" not in labels


def test_safety_animals_get_full_framing():
    s = scoring.score_photo(CenterOnly(0.0), busy_photo(), "coyote", {"coyote", "gray_fox"}, safety="caution")
    assert dict(s.parts)["Framing"] == scoring.FRAMING_MAX


def gray_photo(level):
    """A smooth spread of tones, 70 either side of `level`."""
    ramp = Image.linear_gradient("L").resize((200, 200))
    return ramp.point(lambda v: int(level - 70 + v * 140 / 255)).convert("RGB")


def test_lighting_prefers_a_well_exposed_photo():
    good = scoring.lighting(gray_photo(128))
    assert good > 0.9
    assert scoring.lighting(gray_photo(128).point(lambda v: v // 8)) < 0.2  # far too dark
    assert scoring.lighting(Image.new("RGB", (200, 200), (250, 250, 250))) < 0.2  # blown out
    flat = Image.new("RGB", (200, 200), (130, 130, 130))
    assert scoring.lighting(flat) < good  # no contrast at all


def test_night_animals_keep_some_lighting_points():
    dark = gray_photo(128).point(lambda v: v // 8)
    day = dict(scoring.score_photo(CenterOnly(0.95), dark, "coyote", {"coyote", "gray_fox"}).parts)
    night = dict(scoring.score_photo(CenterOnly(0.95), dark, "coyote", {"coyote", "gray_fox"},
                                     activity="night").parts)
    assert night["Lighting"] == round(scoring.LIGHTING_MAX * scoring.NIGHT_LIGHTING_FLOOR) > day["Lighting"]



def test_soft_background():
    crisp = busy_photo()
    blurred = crisp.filter(ImageFilter.GaussianBlur(5))
    w, h = crisp.size
    box = (w // 4, h // 4, 3 * w // 4, 3 * h // 4)
    portrait = blurred.copy()
    portrait.paste(crisp.crop(box), box[:2])
    assert scoring.soft_background(portrait)
    assert not scoring.soft_background(crisp)  # sharp all over
    assert not scoring.soft_background(blurred)  # blurry all over


def test_five_star_cutoffs():
    def photo(points, *bonus):
        return [("Clarity", points), ("Rare animal", 250), ("New species", 200)] + [(b, 100) for b in bonus]
    assert [scoring.stars_for(photo(p)) for p in (1000, 950, 900, 700, 500, 200)] == [5, 5, 4, 3, 2, 1]
    # Rarity and new species don't add stars; a soft background does.
    assert scoring.stars_for(photo(900, "Soft background")) == 5
    # Retired parts (golden hour) no longer add stars.
    assert scoring.stars_for(photo(900, "Golden hour")) == 4
    # Scores saved before lighting existed (three parts out of 1000) still work.
    assert scoring.stars_for([["Clarity", 400], ["Sharpness", 300], ["Framing", 280]]) == 5


def test_to_local_uses_us_daylight_saving():
    assert scoring.to_local(datetime(2026, 7, 2, 2, 0, tzinfo=timezone.utc), -8) == datetime(2026, 7, 1, 19, 0)
    assert scoring.to_local(datetime(2026, 1, 16, 3, 0, tzinfo=timezone.utc), -8) == datetime(2026, 1, 15, 19, 0)
