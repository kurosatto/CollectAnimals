"""Profile pictures: ten pixel-art nature lovers (tools/make_avatars.py draws them
as species/sprites/avatar_<n>.png, served from /sprites/). Each player gets one
at random when they sign up; older accounts without one get a fixed pick from
their id, so a player's picture never changes between visits."""

import random

COUNT = 10


def pick() -> int:
    return random.randint(1, COUNT)


def avatar_of(user) -> int:
    a = user.avatar
    return a if a and 1 <= a <= COUNT else user.id * 7 % COUNT + 1
