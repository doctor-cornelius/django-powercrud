"""Settings for browser acceptance of an independently shaped pack declaration."""

from copy import deepcopy

from .settings import *


TEMPLATES = deepcopy(TEMPLATES)
TEMPLATES[0]["DIRS"].insert(0, os.path.join(BASE_DIR, "tests", "templates"))

POWERCRUD_SETTINGS = {
    **POWERCRUD_SETTINGS,
    "POWERCRUD_TEMPLATE_PACK": "tests.template_pack_fixtures:external_browser_template_pack",
}

SAMPLE_PRESENTATION = "External browser fixture pack"
