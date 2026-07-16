"""Small public test helpers for independently maintained template packs."""

from __future__ import annotations

from powercrud.template_pack_validation import validate_template_pack
from powercrud.template_packs import TemplatePack, resolve_template_pack


def assert_template_pack_conforms(
    selector_or_pack: str | TemplatePack,
) -> TemplatePack:
    """Resolve and validate one pack from the author's own test suite.

    The caller remains responsible for configuring Django with the pack's app,
    dependencies, and chosen staticfiles backend. Returning the declaration
    makes ordinary author tests concise without exposing PowerCRUD's internal
    first-party fixture modules.
    """
    template_pack = (
        resolve_template_pack(selector_or_pack)
        if isinstance(selector_or_pack, str)
        else selector_or_pack
    )
    validate_template_pack(template_pack)
    return template_pack
