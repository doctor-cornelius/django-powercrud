---
date: 2025-11-10
categories:
  - enhancements
---
# Some Ideas for Enhancements

I had a think about possible enhancements. I think the top priorities might be:  
- the **template pack system** (to formalize UI extensibility),  
- **related-model HTMX editing**, and  
- **richer async orchestration with live feedback**.  

<!-- more -->

#### 1. Validation and Business-Logic Hooks
- **Row-level and form-level validators** that can run synchronously or asynchronously (e.g. check unique constraints, inter-field dependencies, or related-model rules).  
- Declarative configuration similar to DRF’s `validate()` pattern, integrated with PowerCRUD’s transaction handling.  
- Enables richer business logic in CRUD operations without custom views.

---

#### 2. Query and Filter Sophistication
- **Saved filters / views:** Let users persist filter and column configurations (per user or session).  
- **Dynamic annotations:** Support declarative calculated fields (e.g. totals, derived statuses) defined directly on the view.  
- **Advanced filters:** Multi-select dropdowns, range sliders, and DaisyUI-native widgets for complex querying.

---

#### 3. Async and Task Orchestration
- Expand Django Q2 usage for:
  - **Background exports/imports** (CSV, XLSX).  
  - **Async audit or “simulate changes”** tasks.  
  - **Progress reporting API** so HTMX can poll job status (e.g. modal progress bar).  
- Reinforces PowerCRUD as the CRUD framework that scales beyond synchronous request-response.

---

#### 4. Declarative Relationships
- Syntax for inlining related models — editable child tables from a parent view (like `InlineFormSetMixin` but with HTMX partials).  
- First-class “related CRUD” handling for real-world relational data.

---

#### 5. UI Layer Enhancements
- **Async feedback for bulk edit and delete:** Show modal progress or toast updates while jobs run.  
- **Per-user column configuration:** Save visible/hidden fields per user via localStorage or DB.  
- **Field rendering polish:** DaisyUI badges, progress bars, and tag components for status or category fields.

---

#### 6. Template Pack System
- **Pluggable template architecture** inspired by Crispy Forms’ template packs.  
- Define a clear interface for CRUD templates (list, form, modal, row) so UI packs can be swapped cleanly.  
- Start with a modernized **DaisyUI pack** as default; later reintroduce a Bootstrap 5 pack using the same interface.  
- Keeps presentation concerns fully isolated and encourages community contributions for new UI frameworks.  
- Simplifies long-term maintenance — one template contract, multiple aesthetic options.

---

#### 7. Developer Ergonomics
- **CLI scaffolder:** `python manage.py powercrud scaffold app.Model` to auto-generate CRUD view classes and URL wiring.  
- **Plugin discovery:** Allow external packages to register hooks or template partials via entrypoints (e.g. “PowerCRUD Charts”, “PowerCRUD Audit”).  
- **Test utilities:** Pytest fixtures to spin up CRUD instances easily for downstream projects.  
- Makes PowerCRUD faster to adopt, easier to extend, and simpler to test.

---

#### 8. Docs and Introspection
- **Live schema explorer:** Optional dev-only view showing how PowerCRUD interprets a model (field mappings, async actions, etc.).  
- **Debug overlay:** Development banner displaying CRUD metadata (model, async flags, template pack).  
- **Autodoc tooling:** Generate documentation from registered CRUD classes, keeping docs and code in sync.  
- Helps developers understand behavior instantly without diving into source.

