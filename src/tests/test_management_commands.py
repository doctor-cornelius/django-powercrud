from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.management import call_command, CommandError
from django.test import override_settings

from powercrud.management.commands import pcrud_cleanup_async as cleanup_cmd
from powercrud.management.commands import pcrud_extract_tailwind_classes as tailwind_cmd
from powercrud.management.commands import pcrud_mktemplate as mktemplate_cmd


@pytest.mark.django_db
def test_extract_tailwind_writes_file_when_output_dir(tmp_path, monkeypatch):
    out_dir = tmp_path / "safelist"
    css_src = Path(tailwind_cmd.__file__).resolve().parent.parent.parent / "assets" / "django_assets"
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
    monkeypatch.setattr(mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config)

    calls = {}
    monkeypatch.setattr(mktemplate_cmd.Command, "_copy_template_structure", lambda self, td, ad: calls.setdefault("structure", (td, ad)))

    call_command("pcrud_mktemplate", "fake_app", "--all")

    assert "structure" in calls
    target_dir, app_template_dir = calls["structure"]
    assert Path(target_dir) == tmp_path / "templates"
    assert Path(app_template_dir) == tmp_path / "templates" / "fake_app"


def test_mktemplate_handle_calls_single(monkeypatch, tmp_path):
    fake_app_config = SimpleNamespace(path=str(tmp_path), name="fake_app")
    monkeypatch.setattr(mktemplate_cmd.apps, "get_app_config", lambda _: fake_app_config)

    calls = {}
    monkeypatch.setattr(mktemplate_cmd.Command, "_copy_single_template", lambda self, opts, td, ad: calls.setdefault("single", (opts, td, ad)))

    call_command("pcrud_mktemplate", "fake_app.Book", "--list")

    assert "single" in calls
    options, target_dir, app_template_dir = calls["single"]
    assert options["model"] == "Book"
    assert options["role"] == "list"
