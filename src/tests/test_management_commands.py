from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import warnings

import pytest
from django.core.management import call_command, CommandError
from django.test import override_settings

from powercrud.management.commands import pcrud_cleanup_async as cleanup_cmd
from powercrud.management.commands import pcrud_extract_tailwind_classes as tailwind_cmd
from powercrud.management.commands import pcrud_mktemplate as mktemplate_cmd


@pytest.mark.django_db
def test_extract_tailwind_writes_file_when_output_dir(tmp_path, monkeypatch):
    out_dir = tmp_path / "safelist"
    css_src = (
        Path(tailwind_cmd.__file__).resolve().parent.parent.parent
        / "assets"
        / "django_assets"
    )
    assert any(css_src.glob("*.css")), "expected packaged css asset"

    call_command("pcrud_extract_tailwind_classes", "--output", str(out_dir))

    output_file = out_dir / tailwind_cmd.DEFAULT_FILENAME
    assert output_file.exists()
    copied = output_file.read_text()
    # ensure copied file contains some CSS content
    assert ".table" in copied or copied.strip() != ""


def test_extract_tailwind_requires_config_or_output(monkeypatch):
    with override_settings(POWERCRUD_SETTINGS={}):
        with pytest.raises(CommandError):
            call_command("pcrud_extract_tailwind_classes")


def test_cleanup_async_warns_when_disabled(monkeypatch, capsys):
    with override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": False}):
        call_command("pcrud_cleanup_async")
    out = capsys.readouterr().out
    assert "async features are disabled" in out


def test_cleanup_async_json_output(monkeypatch, capsys):
    fake_summary = {"active_tasks": 1, "cleaned": {"task": {"reason": "done"}}}

    class DummyManager:
        def cleanup_completed_tasks(self):
            return fake_summary

    monkeypatch.setattr(cleanup_cmd, "AsyncManager", lambda: DummyManager())

    with override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": True}):
        call_command("pcrud_cleanup_async", "--json")

    out = capsys.readouterr().out.strip()
    assert json.loads(out) == fake_summary


def test_mktemplate_handle_calls_structure(monkeypatch, tmp_path):
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    calls = {}
    monkeypatch.setattr(
        mktemplate_cmd.Command,
        "_copy_template_structure",
        lambda self, td, ad: calls.setdefault("structure", (td, ad)),
    )

    call_command("pcrud_mktemplate", "fake_app", "--all")

    assert "structure" in calls
    target_dir, app_template_dir = calls["structure"]
    assert Path(target_dir) == tmp_path / "templates"
    assert Path(app_template_dir) == tmp_path / "templates" / "fake_app"


def test_mktemplate_handle_calls_single(monkeypatch, tmp_path):
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    calls = {}
    monkeypatch.setattr(
        mktemplate_cmd.Command,
        "_copy_single_template",
        lambda self, opts, td, ad: calls.setdefault("single", (opts, td, ad)),
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--list")

    assert "single" in calls
    options, target_dir, app_template_dir = calls["single"]
    assert options["model"] == "Book"
    assert options["role"] == "list"


def test_mktemplate_copies_focused_pagination_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy the model-scoped pagination override."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        call_command("pcrud_mktemplate", "fake_app.Book", "--component", "pagination")

    copied_file = tmp_path / "templates" / "fake_app" / "book_pagination.html"
    assert copied_file.exists(), (
        "The pagination component should be copied into the model-specific template location."
    )
    assert 'data-powercrud-pagination="true"' in copied_file.read_text(), (
        "The copied pagination component should retain its runtime semantic hook."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "object_list.html#pagination" in output, (
        "The command should explain automatic selection and the retained legacy fragment."
    )


def test_mktemplate_copies_focused_page_size_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy the model-scoped page-size override."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "page-size")

    copied_file = (
        tmp_path / "templates" / "fake_app" / "book_page_size_selector.html"
    )
    assert copied_file.exists(), (
        "The page-size component should be copied into the model-specific template location."
    )
    assert 'data-powercrud-page-size-select="true"' in copied_file.read_text(), (
        "The copied page-size component should retain its runtime semantic hook."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "#page-size-form" in output, (
        "The command should explain automatic selection and the required page-size form hook."
    )


def test_mktemplate_copies_focused_list_actions_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy model-scoped list actions."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "list-actions")

    copied_file = tmp_path / "templates" / "fake_app" / "book_list_actions.html"
    assert copied_file.exists(), (
        "The list-actions component should be copied into the model-specific template location."
    )
    assert "{% extra_buttons view %}" in copied_file.read_text(), (
        "The copied list-actions component should retain PowerCRUD's extra-action renderer."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "data-powercrud-action-controls" in output, (
        "The command should explain automatic selection and the surrounding toolbar contract."
    )


def test_mktemplate_copies_focused_filter_trigger_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped filter trigger."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "filter-toggle")

    copied_file = tmp_path / "templates" / "fake_app" / "book_filter_trigger.html"
    assert copied_file.exists(), (
        "The filter-trigger component should be copied into the model-specific template location."
    )
    assert "data-powercrud-filter-toggle" in copied_file.read_text(), (
        "The copied filter trigger should retain its runtime semantic hook."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "filterCollapse" in output, (
        "The command should explain automatic selection and the required filter-panel target."
    )


def test_mktemplate_copies_focused_filter_panel_actions_component(
    monkeypatch, tmp_path, capsys
):
    """The focused component command should copy model-scoped filter-panel actions."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command(
        "pcrud_mktemplate", "fake_app.Book", "--component", "filter-panel-actions"
    )

    copied_file = (
        tmp_path / "templates" / "fake_app" / "book_filter_panel_actions.html"
    )
    assert copied_file.exists(), (
        "The filter-panel-actions component should be copied into the model-specific template location."
    )
    assert "data-powercrud-add-filter-container" in copied_file.read_text(), (
        "The copied filter-panel actions should retain the add-filter container hook."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "form=filter-form" in output, (
        "The command should explain automatic selection and the external filter-form relationship."
    )


def test_mktemplate_copies_focused_filter_form_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped filter form."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "filter-form")

    copied_file = tmp_path / "templates" / "fake_app" / "book_filter_form.html"
    assert copied_file.exists(), (
        "The filter-form component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert 'id="filter-form"' in copied_content and 'data-powercrud-visible-filters-state' in copied_content, (
        "The copied filter form should retain its form and optional-filter visibility hooks."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "visible_filter_fields" in output, (
        "The command should explain automatic selection and the required filter-form context."
    )


def test_mktemplate_copies_focused_list_columns_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped column chooser."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "list-columns")

    copied_file = tmp_path / "templates" / "fake_app" / "book_list_columns.html"
    assert copied_file.exists(), (
        "The list-column component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert 'data-powercrud-list-columns="true"' in copied_content and 'data-powercrud-list-column-checkbox="true"' in copied_content, (
        "The copied chooser should retain its container and checkbox runtime hooks."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "list_column_state" in output and "surrounding list toolbar" in output, (
        "The command should explain automatic selection, required context, and toolbar ownership."
    )


def test_mktemplate_copies_focused_row_actions_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy model-scoped row actions."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "row-actions")

    copied_file = tmp_path / "templates" / "fake_app" / "book_row_actions.html"
    assert copied_file.exists(), (
        "The row-actions component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert "data-inline-action" in copied_content and "data-powercrud-row-actions-trigger" in copied_content, (
        "The copied row-actions component should retain action and dropdown runtime hooks."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "resolved row_actions" in output and "do not repeat permission" in output, (
        "The command should explain automatic selection and the presentation-only context boundary."
    )
    assert "action_links()" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy API bridge and shared JavaScript ownership."
    )


def test_mktemplate_copies_focused_table_header_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped table header."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "table-header")

    copied_file = tmp_path / "templates" / "fake_app" / "book_table_header.html"
    assert copied_file.exists(), (
        "The table-header component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert "X-Filter-Sort-Request" in copied_content and "bulk_selection_controls_template_paths" in copied_content, (
        "The copied table header should retain sorting and focused selection-control delegation."
    )
    assert 'selection_control="select_all"' in copied_content, (
        "The copied table header should retain its select-all control mode."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "current_sort" in output and "semantic help triggers" in output, (
        "The command should explain automatic selection and required table-header context."
    )
    assert "Legacy partial/list.html" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy façade and shared JavaScript ownership."
    )


def test_mktemplate_copies_focused_table_row_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped table row."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "table-row")

    copied_file = tmp_path / "templates" / "fake_app" / "book_table_row.html"
    assert copied_file.exists(), (
        "The table-row component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert "inline_row_display_template_paths" in copied_content and "inline_row_display.html" in copied_content, (
        "The copied table-row façade should retain focused display-row delegation."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "inline_edit" in output and "cell link" in output, (
        "The command should explain automatic selection and required table-row context."
    )
    assert "compatibility façade over inline-row-display" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the canonical display-row bridge and shared JavaScript ownership."
    )


def test_mktemplate_copies_focused_inline_row_display_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy the canonical inline display row."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command(
        "pcrud_mktemplate", "fake_app.Book", "--component", "inline-row-display"
    )

    copied_file = (
        tmp_path / "templates" / "fake_app" / "book_inline_row_display.html"
    )
    assert copied_file.exists(), (
        "Inline display rows should use the model-specific destination."
    )
    copied_content = copied_file.read_text()
    assert 'data-inline-row="true"' in copied_content and "bulk_selection_controls_template_paths" in copied_content, (
        "The copied row should retain identity and focused selection delegation."
    )
    assert 'data-inline-dependent-field="{{ cell.name }}"' in copied_content and 'data-inline-actions="true"' in copied_content, (
        "The copied row should retain dependency and aligned action hooks."
    )
    output = capsys.readouterr().out
    assert "partial/list.html#inline_row_display" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy fragment and package-owned lifecycle."
    )


def test_mktemplate_copies_focused_inline_row_form_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy the active inline form row."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "inline-row-form")

    copied_file = tmp_path / "templates" / "fake_app" / "book_inline_row_form.html"
    assert copied_file.exists(), "Inline form rows should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert 'data-inline-active="true"' in copied_content and "inline_hidden_fields" in copied_content, (
        "The copied form row should retain active state and preserved hidden fields."
    )
    assert "data-inline-save" in copied_content and "data-inline-cancel" in copied_content and "row-select-checkbox" in copied_content, (
        "The copied form row should retain action and selection-column hooks."
    )
    output = capsys.readouterr().out
    assert "inline_hidden_fields" in output and "action_button_classes" in output, (
        "The command should explain the required form-row context."
    )
    assert "partial/list.html#inline_row_form" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy fragment and package-owned lifecycle."
    )


def test_mktemplate_copies_focused_inline_field_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy the dependency replacement widget."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "inline-field")

    copied_file = tmp_path / "templates" / "fake_app" / "book_inline_field.html"
    assert copied_file.exists(), "Inline fields should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert 'class="inline-field-widget w-full"' in copied_content and 'data-inline-field="{{ field_name }}"' in copied_content, (
        "The copied field should retain its stable replacement root and marker."
    )
    assert "field_dependency.depends_on" in copied_content and "dependency_endpoint_url" in copied_content, (
        "The copied field should retain dependency metadata and endpoint fallback."
    )
    output = capsys.readouterr().out
    assert "field, field_name" in output and "partial/inline_field.html" in output, (
        "The command should explain field context and the direct legacy path."
    )
    assert "searchable-select reinitialization" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned replacement lifecycle."
    )


def test_mktemplate_copies_focused_table_shell_component(monkeypatch, tmp_path, capsys):
    """The focused component command should copy a model-scoped table shell."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "table-shell")

    copied_file = tmp_path / "templates" / "fake_app" / "book_table_shell.html"
    assert copied_file.exists(), (
        "The table-shell component should be copied into the model-specific template location."
    )
    copied_content = copied_file.read_text()
    assert "table-max-height" in copied_content and "data-inline-enabled" in copied_content and "data-selection-key" in copied_content, (
        "The copied shell should retain geometry, inline, and selection metadata."
    )
    output = capsys.readouterr().out
    assert "selected automatically" in output and "table_header_template_paths" in output and "object_list" in output, (
        "The command should explain automatic selection and the nested shell context."
    )
    assert "retains table and inline styles plus direct inline fragments" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy style/fragment façade and shared JavaScript ownership."
    )


def test_mktemplate_copies_focused_bulk_selection_status_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy model-scoped bulk-selection status."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command(
        "pcrud_mktemplate",
        "fake_app.Book",
        "--component",
        "bulk-selection-status",
    )

    copied_file = (
        tmp_path
        / "templates"
        / "fake_app"
        / "book_bulk_selection_status.html"
    )
    assert copied_file.exists(), (
        "The bulk-selection-status component should be copied to the model-specific location."
    )
    copied_content = copied_file.read_text()
    assert 'id="bulk-actions-container"' in copied_content and 'id="selected-items-counter"' in copied_content, (
        "The copied status component should retain its container and count hooks."
    )
    assert "data-powercrud-clear-selection" in copied_content and "data-powercrud-modal-trigger" in copied_content, (
        "The copied status component should retain clear-selection and modal hooks."
    )
    output = capsys.readouterr().out
    assert "selected_count" in output and "#bulk-actions-container" in output, (
        "The command should explain required status context and hooks."
    )
    assert "object_list.html#bulk_selection_status" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy fragment and shared JavaScript ownership."
    )


def test_mktemplate_copies_focused_bulk_selection_controls_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy all three selection-control modes."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command(
        "pcrud_mktemplate",
        "fake_app.Book",
        "--component",
        "bulk-selection-controls",
    )

    copied_file = (
        tmp_path
        / "templates"
        / "fake_app"
        / "book_bulk_selection_controls.html"
    )
    assert copied_file.exists(), (
        "The three-mode selection-controls component should be copied to the model-specific location."
    )
    copied_content = copied_file.read_text()
    assert all(
        mode in copied_content for mode in ('"matching"', '"select_all"', '"row"')
    ), "The copied component should implement matching, select-all, and row modes."
    assert "data-powercrud-select-all" in copied_content and "data-powercrud-row-select" in copied_content, (
        "The copied component should retain header and row selection hooks."
    )
    output = capsys.readouterr().out
    assert "three-mode renderer" in output and "all_selected" in output and "selected_ids" in output, (
        "The command should explain the component modes and their context."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned selection behavior."
    )


@pytest.mark.parametrize(
    ("component", "filename", "content_hook", "guidance"),
    [
        ("bulk-form", "book_bulk_form.html", 'id="bulk-edit-form"', "bulk_fields_template_paths"),
        ("bulk-fields", "book_bulk_fields.html", 'name="fields_to_update"', "field_info"),
    ],
)
def test_mktemplate_copies_focused_bulk_form_components(
    component, filename, content_hook, guidance, monkeypatch, tmp_path, capsys
):
    """Bulk form components should copy script-free model-scoped templates."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", component)

    copied_file = tmp_path / "templates" / "fake_app" / filename
    assert copied_file.exists(), "The focused bulk component should use its model-specific destination."
    copied_content = copied_file.read_text()
    assert content_hook in copied_content, "The copied bulk component should retain its defining form hook."
    assert "<script" not in copied_content, "Focused bulk component copies should not contain functional scripts."
    output = capsys.readouterr().out
    assert guidance in output and "bulk_edit_form.html#full_form" in output, (
        "The command should explain focused context and the legacy full-form façade."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned bulk behavior."
    )


def test_mktemplate_copies_focused_bulk_outcomes_component(
    monkeypatch, tmp_path, capsys
):
    """The focused command should copy every script-free outcome mode."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command(
        "pcrud_mktemplate", "fake_app.Book", "--component", "bulk-outcomes"
    )

    copied_file = tmp_path / "templates" / "fake_app" / "book_bulk_outcomes.html"
    assert copied_file.exists(), "Bulk outcomes should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert all(mode in copied_content for mode in ("operation_errors", "error", "conflict", "queued")), (
        "The copied component should contain all four outcome modes."
    )
    assert "<script" not in copied_content, "Focused outcome copies should not contain functional scripts."
    output = capsys.readouterr().out
    assert "bulk_outcome" in output and "Legacy bulk form and bulk-edit error fragments" in output, (
        "The command should explain mode context and legacy fragment bridges."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned outcome behavior."
    )


def test_mktemplate_copies_focused_modal_shell_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy the model-scoped dialog shell."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "modal-shell")

    copied_file = tmp_path / "templates" / "fake_app" / "book_modal_shell.html"
    assert copied_file.exists(), "The modal shell should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert "data-powercrud-modal" in copied_content and "data-powercrud-modal-box" in copied_content, (
        "The copied shell should retain dialog and box hooks."
    )
    assert "modal-backdrop" in copied_content and 'aria-label="Close modal"' in copied_content, (
        "The copied shell should retain close and backdrop behavior."
    )
    output = capsys.readouterr().out
    assert "modal_id" in output and "partial/modal.html direct target" in output, (
        "The command should explain modal context and the legacy direct target."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned modal behavior."
    )


def test_mktemplate_copies_focused_modal_content_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy the empty model-scoped modal target."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "modal-content")

    copied_file = tmp_path / "templates" / "fake_app" / "book_modal_content.html"
    assert copied_file.exists(), "Modal content should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert 'id="{{ modal_target }}"' in copied_content and "modal_body_classes" in copied_content, (
        "The copied content host should retain configured target and body classes."
    )
    output = capsys.readouterr().out
    assert "empty host" in output and "partial/modal.html direct target" in output, (
        "The command should explain the host boundary and legacy direct target."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain package-owned modal lifecycle behavior."
    )


def test_mktemplate_copies_focused_form_shell_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy a composable model-scoped form shell."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "form-shell")

    copied_file = tmp_path / "templates" / "fake_app" / "book_form_shell.html"
    assert copied_file.exists(), "The form shell should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert 'data-powercrud-form="object"' in copied_content and "form_fields_template_paths" in copied_content, (
        "The copied shell should retain its runtime hook and nested field delegation."
    )
    assert "form_actions_template_paths" in copied_content and "X-Redisplay-Object-List" in copied_content, (
        "The copied shell should retain nested actions and HTMX list-redisplay semantics."
    )
    output = capsys.readouterr().out
    assert "form_display_items" in output and "object_form.html#normal_content" in output, (
        "The command should explain shell context and legacy fragments."
    )
    assert "nested field/action delegation" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain future composition and package-owned behavior."
    )


def test_mktemplate_copies_focused_form_fields_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy both declared field-rendering paths."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "form-fields")

    copied_file = tmp_path / "templates" / "fake_app" / "book_form_fields.html"
    assert copied_file.exists(), "Form fields should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert "use_crispy" in copied_content and "crispy_partials.html#crispy_form" in copied_content, (
        "The copied fields should retain native and crispy rendering branches."
    )
    output = capsys.readouterr().out
    assert "form, use_crispy" in output and "crispy_partials.html#load_tags" in output, (
        "The command should explain fields context and both legacy crispy fragments."
    )
    assert "selected pack's crispy rendering" in output, (
        "The command guidance should not hardcode a different pack's crispy integration."
    )
    assert "crispy-tailwind" not in output, (
        "The selected-pack command guidance must remain framework-neutral."
    )
    assert "form shell owns CSRF" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the shell boundary and package-owned behavior."
    )


def test_mktemplate_copies_focused_form_actions_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy the model-scoped save control."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "form-actions")

    copied_file = tmp_path / "templates" / "fake_app" / "book_form_actions.html"
    assert copied_file.exists(), "Form actions should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert 'type="submit"' in copied_content and "data-form-save" in copied_content, (
        "The copied action should retain submit and package spinner semantics."
    )
    output = capsys.readouterr().out
    assert "requires no template context" in output and "data-form-save" in output, (
        "The command should explain the minimal context and runtime hook."
    )
    assert "object_form.html#normal_content" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the legacy shell boundary and package-owned behavior."
    )


def test_mktemplate_copies_focused_form_conflict_component(monkeypatch, tmp_path, capsys):
    """The focused command should copy all existing conflict presentation modes."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", "form-conflict")

    copied_file = tmp_path / "templates" / "fake_app" / "book_form_conflict.html"
    assert copied_file.exists(), "Form conflict should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert "Edit Conflict" in copied_content and "conflict_message" in copied_content, (
        "The copied conflict should retain its heading and message context."
    )
    assert "use_modal" in copied_content and "hx-target" in copied_content, (
        "The copied conflict should retain modal suppression and HTMX return hooks."
    )
    output = capsys.readouterr().out
    assert "conflict_message, object" in output and "object_form.html#conflict_detected" in output, (
        "The command should explain conflict context and the direct legacy fragment."
    )
    assert "plain 409" in output and "no copied PowerCRUD JavaScript is required" in output, (
        "The command should explain the non-HTMX boundary and package-owned behavior."
    )


@pytest.mark.parametrize(
    ("component", "destination", "content_hook", "guidance"),
    [
        (
            "detail-shell",
            "book_detail_shell.html",
            "object_detail object view",
            "object_detail.html#pcrud_content",
        ),
        (
            "detail-content",
            "book_detail_content.html",
            'class="table w-full',
            "partial/detail.html",
        ),
    ],
)
def test_mktemplate_copies_focused_detail_components(
    monkeypatch, tmp_path, capsys, component, destination, content_hook, guidance
):
    """Focused detail commands should copy each model-scoped presentation layer."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", component)

    copied_file = tmp_path / "templates" / "fake_app" / destination
    assert copied_file.exists(), f"{component} should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert content_hook in copied_content, (
        f"The copied {component} should retain its defining composition hook."
    )
    output = capsys.readouterr().out
    assert guidance in output, (
        f"The {component} guidance should name its legacy compatibility façade."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        f"The {component} guidance should explain package-owned runtime behavior."
    )


@pytest.mark.parametrize(
    ("component", "destination", "content_hook", "guidance"),
    [
        (
            "delete-shell",
            "book_delete_shell.html",
            "delete_content_template_paths",
            "object_confirm_delete.html#pcrud_content",
        ),
        (
            "delete-content",
            "book_delete_content.html",
            "delete_actions_template_paths",
            "object_confirm_delete.html#normal_content",
        ),
    ],
)
def test_mktemplate_copies_focused_delete_shell_and_content(
    monkeypatch, tmp_path, capsys, component, destination, content_hook, guidance
):
    """Focused delete commands should copy each released presentation layer."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", component)

    copied_file = tmp_path / "templates" / "fake_app" / destination
    assert copied_file.exists(), f"{component} should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert content_hook in copied_content, (
        f"The copied {component} should retain its defining composition hook."
    )
    output = capsys.readouterr().out
    assert guidance in output, (
        f"The {component} guidance should name its legacy compatibility façade."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        f"The {component} guidance should explain package-owned runtime behavior."
    )


@pytest.mark.parametrize(
    ("component", "destination", "content_hook", "guidance"),
    [
        (
            "delete-actions",
            "book_delete_actions.html",
            'type="submit"',
            "object_confirm_delete.html#normal_content",
        ),
        (
            "delete-conflict",
            "book_delete_conflict.html",
            "hx-vals",
            "object_confirm_delete.html#conflict_detected",
        ),
    ],
)
def test_mktemplate_copies_focused_delete_actions_and_conflict(
    monkeypatch, tmp_path, capsys, component, destination, content_hook, guidance
):
    """Focused delete commands should copy actions and conflict presentation."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    call_command("pcrud_mktemplate", "fake_app.Book", "--component", component)

    copied_file = tmp_path / "templates" / "fake_app" / destination
    assert copied_file.exists(), f"{component} should use the model-specific destination."
    copied_content = copied_file.read_text()
    assert content_hook in copied_content, (
        f"The copied {component} should retain its defining semantic hook."
    )
    output = capsys.readouterr().out
    assert guidance in output, (
        f"The {component} guidance should name its legacy compatibility façade."
    )
    assert "no copied PowerCRUD JavaScript is required" in output, (
        f"The {component} guidance should explain package-owned runtime behavior."
    )


def test_mktemplate_rejects_unknown_focused_component(monkeypatch, tmp_path):
    """Focused-copy requests should name a component that PowerCRUD supports."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )

    with pytest.raises(CommandError, match="Unsupported focused component 'table'"):
        call_command("pcrud_mktemplate", "fake_app.Book", "--component", "table")


def test_mktemplate_registry_copies_every_script_free_component(
    monkeypatch, tmp_path, capsys
):
    """Every registered focused component should have one complete copy contract."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )
    command = mktemplate_cmd.Command()
    source_dir = (
        Path(mktemplate_cmd.__file__).resolve().parents[2]
        / "templates"
        / command.template_prefix
        / "partial"
    )

    assert len(command.focused_components) == 31, (
        "The final Phase 2 registry should contain every shipped focused component exactly once."
    )
    for component, template_component in command.focused_components.items():
        source_path = source_dir / f"{template_component}.html"
        target_path = (
            tmp_path
            / "templates"
            / "fake_app"
            / f"book_{template_component}.html"
        )

        call_command(
            "pcrud_mktemplate", "fake_app.Book", "--component", component
        )

        assert source_path.exists(), f"{component} should have a packaged focused source."
        assert target_path.read_bytes() == source_path.read_bytes(), (
            f"{component} should copy the packaged source unchanged to its model destination."
        )
        assert "<script" not in target_path.read_text(encoding="utf-8").lower(), (
            f"{component} should remain a script-free focused copy."
        )
        output = capsys.readouterr().out
        assert f"From: {source_path}" in output and f"To: {target_path}" in output, (
            f"{component} should print its exact source and destination."
        )
        assert "selected automatically for this model where" in output, (
            f"{component} should explain model-first automatic selection without assuming a list surface."
        )
        output_lower = output.lower()
        assert "context" in output_lower and (
            "preserve" in output_lower or "keep" in output_lower
        ), (
            f"{component} should identify its context and semantic hooks."
        )
        assert "0.x" in output and "legacy" in output_lower, (
            f"{component} should identify its retained legacy compatibility boundary."
        )
        assert "no copied PowerCRUD JavaScript is required" in output, (
            f"{component} should explain package-owned runtime behavior."
        )


def test_mktemplate_component_option_is_mutually_exclusive():
    """Focused copying must not combine with legacy root-template copy modes."""
    with pytest.raises(CommandError, match="not allowed with argument"):
        call_command(
            "pcrud_mktemplate",
            "fake_app.Book",
            "--component",
            "pagination",
            "--list",
        )


@pytest.mark.django_db
def test_cleanup_async_plain_output(monkeypatch, capsys):
    dummy_summary = {
        "active_tasks": 2,
        "cleaned": {
            "task-1": {
                "reason": "expired",
                "conflict_lock_keys": 1,
                "progress_entries": 3,
                "dashboard_records": 2,
            },
        },
        "skipped": {"task-2": "still running"},
    }

    class DummyManager:
        def cleanup_completed_tasks(self):
            return dummy_summary

    monkeypatch.setattr(cleanup_cmd, "AsyncManager", lambda: DummyManager())

    with override_settings(POWERCRUD_SETTINGS={"ASYNC_ENABLED": True}):
        call_command("pcrud_cleanup_async")

    out = capsys.readouterr().out
    assert "PowerCRUD Async Cleanup Summary" in out
    assert "Cleaned 1 task(s)" in out
    assert "Skipped 1 active task(s)" in out


def test_mktemplate_app_all_copies_complete_framework_tree_with_deprecation_warning(
    monkeypatch, tmp_path, capsys
):
    """App-wide copying should preserve the 0.x tree while warning of v1.0 removal."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )
    command = mktemplate_cmd.Command()
    source_dir = command.get_template_source_dir()
    target_dir = (
        tmp_path
        / "templates"
        / "fake_app"
        / mktemplate_cmd.get_template_pack_copy_destination()
    )
    target_dir.mkdir(parents=True)
    retained_file = target_dir / "application_only.html"
    retained_file.write_text("retain me", encoding="utf-8")
    first_source = next(path for path in source_dir.rglob("*") if path.is_file())
    first_target = target_dir / first_source.relative_to(source_dir)
    first_target.parent.mkdir(parents=True, exist_ok=True)
    first_target.write_text("overwrite me", encoding="utf-8")

    with pytest.warns(FutureWarning, match="whole-tree template copying.*v1.0"):
        call_command("pcrud_mktemplate", "fake_app", "--all")

    source_files = [path for path in source_dir.rglob("*") if path.is_file()]
    assert source_files, "The packaged framework tree should contain template files."
    for source_path in source_files:
        target_path = target_dir / source_path.relative_to(source_dir)
        assert target_path.read_bytes() == source_path.read_bytes(), (
            f"Whole-tree copy should preserve {source_path.relative_to(source_dir)} exactly."
        )
    assert retained_file.read_text(encoding="utf-8") == "retain me", (
        "Whole-tree copy should retain destination-only files for 0.x compatibility."
    )
    output = capsys.readouterr().out
    assert "Files will be overwritten" in output, (
        "An existing framework destination should retain the overwrite warning."
    )
    assert f"From: {source_dir}" in output and f"To: {target_dir}" in output, (
        "Whole-tree output should identify the exact source and destination."
    )


@pytest.mark.parametrize(
    ("option", "suffix"),
    [
        ("--list", "_list.html"),
        ("--detail", "_detail.html"),
        ("--create", "_form.html"),
        ("--update", "_form.html"),
        ("--form", "_form.html"),
        ("--delete", "_confirm_delete.html"),
    ],
)
def test_mktemplate_root_selectors_copy_exact_packaged_template(
    monkeypatch, tmp_path, capsys, option, suffix
):
    """Every legacy root selector should retain its exact source and destination."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )
    command = mktemplate_cmd.Command()
    source_path = (
        Path(mktemplate_cmd.__file__).resolve().parents[2]
        / "templates"
        / command.template_prefix
        / f"object{suffix}"
    )
    target_path = tmp_path / "templates" / "fake_app" / f"book{suffix}"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("overwrite me", encoding="utf-8")

    call_command("pcrud_mktemplate", "fake_app.Book", option)

    assert target_path.read_bytes() == source_path.read_bytes(), (
        f"{option} should copy and overwrite with the exact packaged root template."
    )
    output = capsys.readouterr().out
    assert f"From: {source_path}" in output and f"To: {target_path}" in output, (
        f"{option} should report its exact legacy source and destination."
    )


def test_mktemplate_model_all_copies_exact_four_root_templates(
    monkeypatch, tmp_path, capsys
):
    """Model-wide copying should retain the four established root overrides."""
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(
        mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config
    )
    command = mktemplate_cmd.Command()
    source_dir = (
        Path(mktemplate_cmd.__file__).resolve().parents[2]
        / "templates"
        / command.template_prefix
    )
    target_dir = tmp_path / "templates" / "fake_app"
    expected = {
        "book_list.html": source_dir / "object_list.html",
        "book_detail.html": source_dir / "object_detail.html",
        "book_form.html": source_dir / "object_form.html",
        "book_confirm_delete.html": source_dir / "object_confirm_delete.html",
    }

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        call_command("pcrud_mktemplate", "fake_app.Book", "--all")

    assert {path.name for path in target_dir.iterdir()} == set(expected), (
        "Model --all should create exactly the four established root override names."
    )
    output = capsys.readouterr().out
    for target_name, source_path in expected.items():
        target_path = target_dir / target_name
        assert target_path.read_bytes() == source_path.read_bytes(), (
            f"Model --all should copy {source_path.name} without modification."
        )
        assert f"From: {source_path}" in output and f"To: {target_path}" in output, (
            f"Model --all should report the paths for {target_name}."
        )
