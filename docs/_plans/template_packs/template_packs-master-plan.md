# Template Packs Master Plan

## Status

Active planning folder created from the archived modular template-pack proposal.

## Source

This plan promotes the archived working proposal in [`docs/archive/blog/posts/20251120_template_packs.md`](../../archive/blog/posts/20251120_template_packs.md) into `docs/_plans/` so the work can be resumed as an engineering project.

## Objective

Enable PowerCRUD to support multiple frontend presentation layers by decoupling core CRUD behavior from visual framework implementation details.

## Sequence

The safe sequence is:

```text
contract -> extract JS -> extract CSS -> refactor DaisyUI -> add tests -> only then build new packs
```

## Roadmap

1. [x] Phase 1: Define the template, JavaScript, style, packaging, and discovery contract from the archived proposal.
2. [ ] Phase 2: Implement the core-vs-template-pack JavaScript split.
3. [ ] Phase 3: Turn the existing DaisyUI implementation into the first template pack.
4. [ ] Phase 4: Add template-pack selection and discovery.
5. [ ] Phase 5: Add contract, unit, asset, and browser validation.
6. [ ] Phase 6: Promote stable documentation and author guidance into `docs/mkdocs/`.
7. [ ] Phase 7: Dogfood the contract with a Bootstrap 5 template pack.

