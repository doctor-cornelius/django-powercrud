---
date: 2025-07-30
categories:
  - architecture
---
# Some Thoughts About Open Source "Opinionated" Extensions

I was thinking about the difference between opinionated and non-opinionated packages, and what principles might guide the design of opinionated extensions like this one so they don't become so narrow that they're unusable. 
<!-- more -->

## 1. Opinionated vs. Non-Opinionated Design

### Understanding Opinionated Packages:

- **Enforce specific workflows** based on strong conventions
- Provide **prescriptive defaults** (like `daisyUI` in PowerCRUD)
- Make **integrated technology choices** (eg HTMX,  Crispy Forms)
- **Reduce flexibility** but improve consistency and developer experience
- Follow **convention over configuration**
- **Guide users toward best practices** with sensible defaults

### Understanding Non-Opinionated Packages:

- Provide **flexible building blocks** with minimal assumptions
- Are **highly configurable** with few defaults
- Remain **neutral to technology choices**
- Require users to make more decisions but support broader use cases
- **Focus on core functionality** without aesthetic/UX decisions

### Positioning The Package:

- Clearly state in documentation whether your package is opinionated
- Provide **escape hatches** for users who need customization
- Consider **progressive enhancement** where opinionated features can be disabled

## 2. Architecture for Extensions

### Respect the Base Package:

- Extend rather than replace (like PowerCRUD uses mixins with neapolitan)
- Maintain compatibility with the parent package's API
- Follow Django's "explicit is better than implicit" philosophy

### Progressive Enhancement:

- Features gracefully degrade (like HTMX features only activating if HTMX is available)
- Provide sensible fallbacks (like using form_class if create_form_class isn't specified)
- Layer opinionated features so they can be individually adopted or discarded

### Maintainability & Extensibility:

- Keep core functionality minimal, with hooks or APIs to allow extension
- Provide **clear extension points** through well-documented mixins and hooks
- Allow overriding through configuration

## 3. API & Integration Design

### Consistent API:

- Follow the conventions of the ecosystem (Django-style settings, class-based APIs)
- Ensure naming is predictable and meaningful
- Avoid surprising behavior (e.g., modifying global state without warning)

### Compatibility & Integration:

- Support the latest stable versions of dependencies while maintaining backwards compatibility
- Make integration points clear—where can users plug in their own logic?
- If overriding framework behavior, be explicit about it

## 4. Documentation & Error Handling

### Clear Documentation:

- **Document your opinions** explicitly
- Provide a "Why?" section explaining the package's purpose and design decisions
- Include quickstart guides and real-world examples
- Show how to override defaults when needed

### Error Handling & Debugging:

- Provide helpful error messages with actionable suggestions
- Log warnings instead of failing silently
- Consider exposing debug tools or settings for advanced users

## 5. Finding the Right Balance

- Make opinions clear in documentation
- Provide escape hatches for those who need something different
- Consider isolating opinions into separate components/modules
- Understand your target audience and their common needs
- Make sure opinions solve real problems and reduce boilerplate

