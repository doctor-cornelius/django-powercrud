"""Bootstrap 5 presentation settings for the bundled sample app."""

from copy import deepcopy

from .settings import *


TEMPLATES = deepcopy(TEMPLATES)
TEMPLATES[0]["DIRS"].insert(
    0,
    BASE_DIR / "sample" / "templates_bootstrap",
)

INSTALLED_APPS = [
    *INSTALLED_APPS,
    "crispy_bootstrap5",
    "powercrud.contrib.bootstrap5",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = [*CRISPY_ALLOWED_TEMPLATE_PACKS, "bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

POWERCRUD_SETTINGS = {
    **POWERCRUD_SETTINGS,
    "POWERCRUD_CSS_FRAMEWORK": "bootstrap5",
    "POWERCRUD_TEMPLATE_PACK": "powercrud.contrib.bootstrap5:template_pack",
}

SAMPLE_PRESENTATION = "Bootstrap 5 pack"
