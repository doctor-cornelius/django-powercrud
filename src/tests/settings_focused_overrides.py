"""Focused-override settings used to test the bundled sample presentation."""

from copy import deepcopy

from .settings import *


TEMPLATES = deepcopy(TEMPLATES)
TEMPLATES[0]["DIRS"].insert(
    0,
    os.path.join(BASE_DIR, "sample", "template_overrides", "focused"),
)

SAMPLE_PRESENTATION = "Standard DaisyUI + Book overrides"
