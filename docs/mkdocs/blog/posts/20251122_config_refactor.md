---
date: 2025-11-22
categories:
  - config
  - enhancement
  - plan
---
# Refactoring PowerCRUD Configuration

This is a plan to refactor configuration by consolidating all parameter resolution methods into a new `ConfigMixin.config` method, to make it easier to reason about and maintain configuration rules.
<!-- more -->

## Background and Strategy

PowerCRUD already relies on an aggregator-mixin architecture: internal mixins, each with a narrow, well-defined responsibility, are combined into a single public `PowerCRUDMixin`. Downstream projects subclass one mixin plus Neapolitan’s `CRUDView`, and everything “just works” through shared `self` and MRO composition. This design keeps the surface area small for downstream use while retaining modularity for maintainers.

Configuration is the one area where the current pattern creates unnecessary cognitive load. Defaults and rule-based decisions are currently distributed across multiple mixin modules. To understand how a particular setting is determined, a maintainer must mentally traverse several mixins, locate the appropriate `get_*` methods, and simulate resolution through MRO. This increases maintenance difficulty and makes it harder to evolve PowerCRUD without unintended interactions.

CoreMixin currently mixes configuration attributes with operational behavior such as queryset sorting and list view rendering, so we are mandating the creation of a dedicated `ConfigMixin`. This mixin becomes the sole owner of configuration defaults, rule resolution, and user overrides while still participating in the aggregator so that downstream inheritance does not change.

`ConfigMixin.config()` will leverage the existing `PowerCRUDMixinValidator` from `powercrud/validators.py` to validate incoming attributes, normalize them, and expose a resolved configuration object (or namespace) that other mixins can consume. Relocating the validator-driven logic into one mixin ensures there is a single authoritative code path for every configuration decision.

Once this locus exists, all other mixins will be updated to **read configuration exclusively through `self.config()`** rather than through scattered `get_*` methods or ad-hoc attribute lookups. Behavioural mixins stop performing their own configuration decisions and instead treat config as a resolved, ready-to-use set of values. This shift reduces duplication, lowers the chance of contradictory logic between mixins, and simplifies the mental model for contributors.

AsyncManager remains separate because it is operational rather than behavioural; it is not tied to the view’s inheritance chain and should not participate in the configuration surface.

The overall effect is a cleaner, more predictable architecture:

* **Convention over configuration** for downstream users.
* **Compositional mixins** for maintainers.
* **One coherent configuration module** to eliminate MRO-based tracing and scattered defaults.

## Plan

### Scope
- Introduce a dedicated `ConfigMixin` that encapsulates all configuration defaults, rule evaluation, and validation (powered by `PowerCRUDMixinValidator`) without altering the external `PowerCRUDMixin` inheritance contract.
- Migrate every behavioural mixin (`core`, `async`, `filtering`, `form`, `htmx`, `inline`, `paginate`, `table`, `url`, and `bulk`) to read from the resolved `self.config()` output instead of duplicating configuration decisions.
- Preserve operational components like `AsyncManager` outside of the configuration locus while ensuring documentation/tests reflect the new API.

### Risks
- Regression in default field/property resolution if the extraction to `ConfigMixin` changes evaluation order.
- MRO or initialization conflicts if `ConfigMixin` is inserted improperly relative to existing mixins.
- Validator drift if new configuration attributes are added without updating `powercrud/validators.py`.

### Tasks
1. [X] Establish `ConfigMixin` foundation.
   1.1. [X] Extract configuration attributes/resolution pipeline from `CoreMixin` into `ConfigMixin`, wrapping the existing `PowerCRUDMixinValidator`.
   1.2. [X] Expose `self.config()` (or equivalent namespace) and ensure it is initialized before behavioural mixins rely on it.
2. [X] Update mixins to consume centralized config.
   2.1. [X] Update `core_mixin.py` to pull values from `self.config()`.
   2.2. [X] Update `async_mixin.py` to pull values from `self.config()`.
   2.3. [X] Update `filtering_mixin.py` to pull values from `self.config()`.
   2.4. [X] Update `form_mixin.py` to pull values from `self.config()`.
   2.5. [X] Update `htmx_mixin.py` to pull values from `self.config()`.
   2.6. [X] Update `inline_editing_mixin.py` to pull values from `self.config()`.
   2.7. [X] Update `paginate_mixin.py` to pull values from `self.config()`.
   2.8. [X] Update `table_mixin.py` to pull values from `self.config()`.
   2.9. [X] Update `url_mixin.py` to pull values from `self.config()`.
   2.10. [X] Update bulk-related mixins to pull values from `self.config()`.
   2.11. [X] Introduce shims/tests to confirm existing defaults and overrides behave identically.
3. [X] Strengthen validation, docs, and release prep.
   3.1. [X] Expand `powercrud/validators.py` coverage and tests to reflect any new config fields.
   3.2. [X] Update documentation/changelog to describe the new configuration entry point and migration guidance.

## Migration Notes

- `ConfigMixin` is now the canonical place to declare configuration attributes and expose resolved values. Behavioural mixins should either override `config()` or, preferably, call `resolve_config(self)` to obtain the derived namespace (which provides helper flags such as `use_htmx_enabled`, inline editing toggles, and table CSS metrics).
- `PowerCRUDMixinValidator` has been extended to cover the broader set of configuration knobs (bulk editing flags, dropdown sort hints, table classes, async-manager hooks, etc.) so overrides get validated consistently before reaching mixin logic. Updated unit tests in `tests/test_conf_logging_validators.py` ensure the new restrictions are enforced.
- Downstream projects that rely on legacy `get_*` helpers can migrate incrementally: continue using existing mixins, but prefer reading from the `config` namespace (or `resolve_config`) instead of recomputing rules. This keeps the public API stable while allowing future releases to move more decisions into `ConfigMixin`.
