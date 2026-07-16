"""Focused-override presentation settings for the bundled sample app."""

from copy import deepcopy

from .settings import *


TEMPLATES = deepcopy(TEMPLATES)
TEMPLATES[0]["DIRS"].insert(
    0,
    BASE_DIR / "sample" / "template_overrides" / "focused",
)

SAMPLE_PRESENTATION = "Standard DaisyUI + Book overrides"
