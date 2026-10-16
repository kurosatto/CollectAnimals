import random

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
    assert labels["Clarity"] == 400 and labels["Framing"] == 300
    assert labels["Rare animal"] == 250 and labels["New species"] == 200
    assert s.stars == 3 and s.total == sum(labels.values())

    # Off-center animal: framing drops, no bonus for a common repeat.
    s = scoring.score_photo(CenterOnly(0.2), busy_photo(), "coyote", allowed)
    labels = dict(s.parts)
    assert labels["Framing"] < 100 and "New species" not in labels


def test_safety_animals_get_full_framing():
    s = scoring.score_photo(CenterOnly(0.0), busy_photo(), "coyote", {"coyote", "gray_fox"}, safety="caution")
    assert dict(s.parts)["Framing"] == scoring.FRAMING_MAX
