# Background task coordination roadmap

This roadmap captures the full direction agreed on 2026-11-04. The executable [plan](0_async_hardening-plan.md) in this folder covers **steps 1, 2a, and 2b**, including standalone package extraction and PowerCRUD integration. Additional execution backends remain future work. See the [notes](0_async_hardening-notes.md) for decisions, findings, and scope boundaries.

- 🔳 Step 1: Harden optional async setup, configuration, task lifecycle, locking, status reporting, and cleanup within PowerCRUD.
- ✅ Step 2a: Establish strict internal separation between reusable task coordination, q2 execution, and PowerCRUD integration ([Phase B handoff](0_async_hardening-notes.md#phase-b-completion-and-handoff)).
- 🔳 Step 2b: Extract a complete standalone package, provisionally `django-task-coordinator` / `TaskCoordinator`, and make PowerCRUD an optional consumer.
- ✅ Phase A: contracts settled, findings/sample scenarios audited, and test suites separated and verified ([handoff](0_async_hardening-notes.md#phase-a-completion-and-handoff)).
- 🔳 Phases C–D maintain verified PowerCRUD async examples across supported presentations; phases E–F add and verify a standalone package example.
- 🔳 Step 3a (future): Add an optional Django Tasks adapter, using the explicit `django-tasks` backport for Django 5.2 and evaluating an existing backend such as django-ox for the first proof.
- 🔳 Step 3b (future): Assess or contribute a q2 backend for Django Tasks, starting with upstream PR #315, and then reconsider the direct q2 adapter.
- 🔳 Step 3c (future, only with a demonstrated need): Consider integration with another task framework.

Delivery order for the current scope: **internal boundary → hardening → separation verification → package extraction → installed-package integration verification**. Step 1 and step 2a overlap; extraction follows after both are complete. django-q2 remains the only execution backend throughout.
