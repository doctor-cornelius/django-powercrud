import shutil
from importlib.resources import files
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps

from powercrud.template_packs import (
    TemplatePack,
    get_configured_template_pack,
    get_template_pack_template_namespace,
    resolve_template_pack,
)


class Command(BaseCommand):
    help = "Bootstrap CRUD templates, either individual templates or the complete framework structure."

    project_template_pack_selectors = {
        "daisyui": "daisyui",
        "bootstrap5": "powercrud.contrib.bootstrap5:template_pack",
    }
    project_core_template_names = (
        "object_list.html",
        "object_detail.html",
        "object_form.html",
        "object_confirm_delete.html",
    )
    project_root_template_names = {
        "list": "object_list.html",
        "detail": "object_detail.html",
        "form": "object_form.html",
        "delete": "object_confirm_delete.html",
    }
    asset_copy_ignored_names = ("AGENTS.md", "README.md")

    focused_components = {
        "pagination": "pagination",
        "page-size": "page_size_selector",
        "list-actions": "list_actions",
        "filter-toggle": "filter_trigger",
        "filter-panel-actions": "filter_panel_actions",
        "filter-form": "filter_form",
        "list-columns": "list_columns",
        "row-actions": "row_actions",
        "table-header": "table_header",
        "table-row": "table_row",
        "table-shell": "table_shell",
        "bulk-selection-status": "bulk_selection_status",
        "bulk-selection-controls": "bulk_selection_controls",
        "bulk-form": "bulk_form",
        "bulk-fields": "bulk_fields",
        "bulk-outcomes": "bulk_outcomes",
        "modal-shell": "modal_shell",
        "modal-content": "modal_content",
        "form-shell": "form_shell",
        "form-fields": "form_fields",
        "form-actions": "form_actions",
        "form-conflict": "form_conflict",
        "detail-shell": "detail_shell",
        "detail-content": "detail_content",
        "delete-shell": "delete_shell",
        "delete-content": "delete_content",
        "delete-actions": "delete_actions",
        "delete-conflict": "delete_conflict",
        "inline-row-display": "inline_row_display",
        "inline-row-form": "inline_row_form",
        "inline-field": "inline_field",
    }

    @property
    def template_prefix(self) -> str:
        """Return the selected namespace at command invocation time."""
        return get_template_pack_template_namespace()

    def get_template_source_dir(self, template_pack: TemplatePack | None = None) -> Path:
        """Return a template pack's package-resource source directory."""
        template_pack = template_pack or get_configured_template_pack()
        if template_pack is None:
            package_name = "powercrud"
            resource_root = f"templates/{self.template_prefix}"
        else:
            package_name = template_pack.template_package
            resource_root = template_pack.template_resource_root
        source_dir = files(package_name).joinpath(*Path(resource_root).parts)
        return Path(source_dir)

    def get_project_asset_sources(
        self, template_pack: TemplatePack
    ) -> tuple[tuple[Path, Path], ...]:
        """Return package-owned asset trees and their app-static destinations."""
        package_root = Path(files("powercrud"))
        shared_assets = package_root / "static" / "powercrud"
        sources = (
            (shared_assets / "css", Path("css")),
            (shared_assets / "js", Path("js")),
        )
        if template_pack.identity != "bootstrap5":
            return sources

        bootstrap_assets = (
            package_root
            / "contrib"
            / "bootstrap5"
            / "static"
            / "powercrud"
            / "contrib"
            / "bootstrap5"
        )
        return (
            *sources,
            (bootstrap_assets / "css", Path("contrib/bootstrap5/css")),
            (bootstrap_assets / "js", Path("contrib/bootstrap5/js")),
        )

    def add_arguments(self, parser):
        # Main argument group
        parser.add_argument(
            "target",
            type=str,
            help="The target app name, or app.Model for templates",
        )

        # Mutually exclusive group for template selection. A plain app target
        # without a scope copies the four project-level root templates.
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--core",
            action="store_true",
            help="Copy the four main CRUD templates for a plain app target.",
        )
        group.add_argument(
            "--all",
            action="store_true",
            help=(
                "Copy all four model CRUD templates for app.Model, or the full "
                "selected source pack for a plain app target."
            ),
        )
        group.add_argument(
            "-l",
            "--list",
            action="store_const",
            const="list",
            dest="role",
            help="List template",
        )
        group.add_argument(
            "-d",
            "--detail",
            action="store_const",
            const="detail",
            dest="role",
            help="Detail template",
        )
        group.add_argument(
            "-c",
            "--create",
            action="store_const",
            const="form",
            dest="role",
            help="Create template",
        )
        group.add_argument(
            "-u",
            "--update",
            action="store_const",
            const="form",
            dest="role",
            help="Update template",
        )
        group.add_argument(
            "-f",
            "--form",
            action="store_const",
            const="form",
            dest="role",
            help="Form template",
        )
        group.add_argument(
            "--delete",
            action="store_const",
            const="delete",
            dest="role",
            help="Delete template",
        )
        group.add_argument(
            "--component",
            metavar="NAME",
            help=(
                "Copy one focused component override (currently: "
                f"{', '.join(self.focused_components)})"
            ),
        )

        # Optional model name for single template operations
        parser.add_argument(
            "model",
            nargs="?",
            type=str,
            help="The ModelName to bootstrap a template for (required except with --all).",
        )
        parser.add_argument(
            "--source-template-pack",
            choices=tuple(self.project_template_pack_selectors),
            default=None,
            help=(
                "Source pack for a plain app copy: daisyui (default) or bootstrap5. "
                "The copied pack must match the pack selected at runtime."
            ),
        )
        parser.add_argument(
            "--assets",
            action="store_true",
            help=(
                "Copy the selected pack's PowerCRUD-owned CSS and JavaScript "
                "as an app-level manual-static snapshot."
            ),
        )

    def handle(self, *args, **options):
        try:
            # Try to split as app.Model
            app_name, model_name = options["target"].split(".")
            is_model_specific = True
        except ValueError:
            # If no dot, treat as app name only
            app_name = options["target"]
            model_name = None
            is_model_specific = False

        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            raise CommandError(f"App '{app_name}' not found. Is it in INSTALLED_APPS?")

        # Determine target directory
        target_dir = Path(app_config.path) / "templates"
        app_template_dir = target_dir / app_name

        if not is_model_specific:
            if options["component"]:
                raise CommandError(
                    "A model target is required for a focused component "
                    "(for example, 'sample.Book --component pagination')."
                )
            source_template_pack = self._get_project_source_template_pack(
                options["source_template_pack"] or "daisyui"
            )
            scope = "all" if options["all"] else options["role"] or "core"
            self._copy_project_template_pack(
                source_template_pack, target_dir, app_template_dir, app_name, scope
            )
            if options["assets"]:
                self._copy_project_assets(
                    source_template_pack, Path(app_config.path), app_name
                )
            return

        if options["assets"]:
            raise CommandError("--assets is only available with a plain app target.")
        if options["core"]:
            raise CommandError("--core is only available with a plain app target.")
        if options["source_template_pack"]:
            raise CommandError(
                "--source-template-pack is only available with a plain app target."
            )
        if options["all"]:
            self._copy_all_model_templates(model_name, target_dir, app_template_dir)
            return
        if not options["role"] and not options["component"]:
            raise CommandError(
                "A model target requires --all, a role option, or --component."
            )

        options["model"] = model_name
        if options["component"]:
            self._copy_focused_component(options, target_dir, app_template_dir)
        else:
            self._copy_single_template(options, target_dir, app_template_dir)

    def _copy_focused_component(self, options, target_dir, app_template_dir):
        """Copy one focused component into the model-specific override location."""
        component = options["component"]
        template_component = self.focused_components.get(component)
        if template_component is None:
            available = ", ".join(sorted(self.focused_components))
            raise CommandError(
                f"Unsupported focused component '{component}'. Available components: {available}."
            )

        model = options["model"]
        source_path = self.get_template_source_dir() / "partial" / f"{template_component}.html"
        if not source_path.exists():
            raise CommandError(f"Template component not found: {source_path}")

        target_dir.mkdir(exist_ok=True)
        app_template_dir.mkdir(exist_ok=True)
        target_path = app_template_dir / f"{model.lower()}_{template_component}.html"
        shutil.copy2(source_path, target_path)

        if component == "pagination":
            contract_guidance = (
                "Keep the paginator, page_obj, request, use_htmx, and original_target "
                "context; preserve data-powercrud-pagination and the existing HTMX page links.\n"
                "The legacy object_list.html#pagination fragment remains available through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "page-size":
            contract_guidance = (
                "Keep page_size_options, default_page_size, page_size_all_enabled, and request "
                "context; preserve #page-size-form, #page-size-select, name=page_size, "
                "data-powercrud-page-size-select, and the Rows per page tooltip.\n"
                "The legacy object_list.html#page_size_selector fragment remains available through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "list-actions":
            contract_guidance = (
                "Keep create_view_url, use_htmx, htmx_target, modal_id, object_verbose_name, "
                "and view context; preserve the Create link and the extra_buttons tag.\n"
                "The surrounding data-powercrud-action-controls wrapper and bulk-selection bridge "
                "remain owned by the legacy object_list.html#list_actions fragment through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "filter-toggle":
            contract_guidance = (
                "Keep view context and preserve #filterToggleBtn, aria-controls=filterCollapse, "
                "data-powercrud-filter-toggle, semantic tooltip metadata, and both filter icon hooks.\n"
                "The filter panel and its #filterCollapse target remain owned by the legacy "
                "object_list.html#filter_trigger fragment through 0.x; no copied PowerCRUD JavaScript is required."
            )
        elif component == "filter-panel-actions":
            contract_guidance = (
                "Keep addable_filter_choices, use_htmx, view, and original_target context; preserve "
                "data-powercrud-add-filter-container, the add-filter select, reset link, and form=filter-form.\n"
                "The filter form and its visible fields remain owned by the legacy "
                "object_list.html#filter_panel_actions fragment through 0.x; no copied PowerCRUD JavaScript is required."
            )
        elif component == "filter-form":
            contract_guidance = (
                "Keep request, visible_filter_fields, persisted_optional_filter_names, and "
                "visible_filter_param_name context; preserve #filter-form, its HTMX attributes, "
                "visible-filter state, and optional-filter remove hooks.\n"
                "Filter-panel actions and the surrounding filter shell remain owned by the legacy "
                "object_list.html#filter_form fragment through 0.x; no copied PowerCRUD JavaScript is required."
            )
        elif component == "list-columns":
            contract_guidance = (
                "Keep view, list_column_state, list_options_url, list_view_url, use_htmx, "
                "original_target, and request context; preserve the list-column trigger, hidden "
                "template, panel, checkbox, query-state, Save, and Reset hooks.\n"
                "The feature guard and surrounding list toolbar remain owned by the legacy "
                "object_list.html#list_columns fragment through 0.x; no copied PowerCRUD JavaScript is required."
            )
        elif component == "row-actions":
            contract_guidance = (
                "Keep object and resolved row_actions context; do not repeat permission, state-hook, "
                "or URL decisions in the template. Preserve action, dropdown, lazy-state, disabled-tooltip, "
                "HTMX, modal, and modal-close-refresh hooks.\n"
                "Legacy action_links(), row.actions, and row.has_actions remain available through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "table-header":
            contract_guidance = (
                "Keep headers, current_sort, filter_params, use_htmx, request, has_row_actions, "
                "enable_selection_controls, and the existing selection-state context. Preserve sorting "
                "URLs and HTMX attributes, semantic help triggers, the conditional Actions heading, "
                "and the select-all compatibility hooks.\n"
                "Legacy partial/list.html remains the 0.x facade; no copied PowerCRUD JavaScript is required."
            )
        elif component == "table-row":
            contract_guidance = (
                "Keep row, inline_edit, enable_selection_controls, selected_ids, list_view_url, "
                "has_row_actions, and inline_row_display_template_paths context. Preserve focused display-row delegation "
                "and keep row, selection, inline-display, dependency, "
                "cell link, tooltip, and row-action hooks.\n"
                "The built-in table-row is a compatibility façade over inline-row-display; custom table-row overrides remain supported, "
                "and the legacy partial/list.html inline fragments remain through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "table-shell":
            contract_guidance = (
                "Keep inline_edit, table_classes, enable_selection_controls, keyBase, "
                "selection_key_suffix, table_header_template_paths, table_row_template_paths, "
                "and object_list context. Preserve wrapper/table geometry, selection-key and "
                "inline-enabled attributes, focused header/row delegation, and the row loop.\n"
                "Legacy partial/list.html retains table and inline styles plus direct inline fragments through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "bulk-selection-status":
            contract_guidance = (
                "Keep selected_count, enable_bulk_edit, list_view_url, view, modal_target, "
                "modal_id, and bulk_modal_box_classes context. Preserve #bulk-actions-container, "
                "#selected-items-counter, data-powercrud-bulk-actions, data-powercrud-clear-selection, "
                "the existing HTMX outer-swap endpoints, and modal trigger metadata.\n"
                "The legacy object_list.html#bulk_selection_status fragment remains available through 0.x; "
                "selection state and request behavior remain package-owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "bulk-selection-controls":
            contract_guidance = (
                "This component is a three-mode renderer selected with selection_control=matching, "
                "select_all, or row. Keep the matching-record state, request, and list_view_url context; "
                "all_selected and some_selected for select_all; and row, selected_ids, and list_view_url for row. "
                "Preserve select-all, row-select, initial-state, matching-action, HTMX target, and outer-swap hooks.\n"
                "The results wrapper, table header, table row, and legacy fragments remain owned by their existing façades through 0.x; "
                "selection state remains server-session and package-runtime owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "bulk-form":
            contract_guidance = (
                "Keep request, selected_ids, selected_count, model_name_plural, enable_bulk_update, "
                "enable_bulk_delete, modal_target, field_info, and bulk_fields_template_paths context. "
                "Preserve #bulk-edit-form, CSRF, bulk_submit, selected_ids[], main/delete sections, "
                "data-powercrud-form=bulk, data-form-save, and delete HTMX metadata.\n"
                "Continue delegating to bulk_fields_template_paths when focused field overrides should remain active. "
                "The legacy bulk_edit_form.html#full_form façade remains through 0.x and retains package-owned behavior; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "bulk-fields":
            contract_guidance = (
                "Keep field_info context and preserve fields_to_update, exact field input names, "
                "field-input-container, relationship and choice values, searchable-select metadata, "
                "and <field>_action controls for many-to-many fields.\n"
                "The bulk form shell, submit/delete controls, and legacy bulk_edit_form.html#full_form façade remain separate through 0.x; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "bulk-outcomes":
            contract_guidance = (
                "This component renders bulk_outcome=operation_errors, error, conflict, or queued. "
                "Keep errors; error; conflict_message with selected_count and model_name_plural; "
                "or task_name, progress_url, modal_id, and message for the selected mode context. Preserve "
                "bulk outcome, polling, progress, modal, and HTMX event hooks.\n"
                "Legacy bulk form and bulk-edit error fragments remain server-addressable through 0.x and retain package-owned behavior; "
                "no copied PowerCRUD JavaScript is required."
            )
        elif component == "modal-shell":
            contract_guidance = (
                "Keep modal_id, modal_target, modal_classes, modal_box_classes, modal_body_classes, "
                "modal_presentation_attrs, bulk_modal_presentation_attrs, and modal_uses_legacy_classes context. "
                "Preserve the dialog and target IDs, data-powercrud-modal, data-powercrud-modal-box, "
                "data-powercrud-default-modal-box-classes, HTML dialog close controls, backdrop, and retained viewport/scroll classes.\n"
                "Continue delegating to modal_content_template_paths if focused content overrides should remain active. "
                "Modal triggers and returned content remain separately owned; the legacy partial/modal.html direct target remains through 0.x, "
                "and no copied PowerCRUD JavaScript is required."
            )
        elif component == "modal-content":
            contract_guidance = (
                "Keep modal_target, modal_body_classes, modal_presentation_attrs, and modal_uses_legacy_classes context. "
                "Preserve the configured target ID and body classes, "
                "and keep this component as the empty host for HTMX inner-content replacement.\n"
                "The dialog, modal box, close/backdrop controls, triggers, returned CRUD/bulk content, and lifecycle remain separately owned; "
                "the legacy partial/modal.html direct target remains through 0.x, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "form-shell":
            contract_guidance = (
                "Keep request, form, object, object_verbose_name, form_display_items, create_view_url, "
                "update_view_url, use_htmx, use_modal, original_target, form_fields_template_paths, "
                "and form_actions_template_paths context. Preserve the heading/context display, POST action, "
                "multipart and CSRF handling, retained query inputs, data-powercrud-form=object, and HTMX attributes.\n"
                "Continue nested field/action delegation when those focused overrides should remain active. "
                "Legacy object_form.html#normal_content and #pcrud_content remain through 0.x; no copied PowerCRUD JavaScript is required."
            )
        elif component == "form-fields":
            contract_guidance = (
                "Keep form, use_crispy, and framework_template_path context. Preserve native Django form rendering "
                "and the selected pack's crispy rendering through crispy_partials.html#crispy_form without adding a nested form tag.\n"
                "Legacy crispy_partials.html#load_tags and #crispy_form remain through 0.x; the form shell owns CSRF and transport, "
                "and no copied PowerCRUD JavaScript is required."
            )
        elif component == "form-actions":
            contract_guidance = (
                "This component requires no template context. Keep a submit control inside the surrounding form, "
                "preserve data-form-save for package-owned spinner behavior, and retain an accessible Save label.\n"
                "The form shell owns action URLs, CSRF, multipart, HTMX, and modal behavior; legacy object_form.html#normal_content "
                "and #pcrud_content remain through 0.x, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "form-conflict":
            contract_guidance = (
                "Keep conflict_message, object, use_modal, use_htmx, list_view_url, request, filter_params, "
                "and original_target context. Preserve the Edit Conflict presentation, modal return suppression, "
                "normal return link, and HTMX return target/history/query hooks.\n"
                "Legacy object_form.html#conflict_detected and #pcrud_content remain server-addressable through 0.x; "
                "the non-HTMX conflict response remains a plain 409, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "detail-shell":
            contract_guidance = (
                "Keep object and view context. Preserve the detail card and object heading, and retain the object_detail tag "
                "when the separately focused detail-content override should remain active.\n"
                "Legacy object_detail.html#pcrud_content remains the normal, HTMX, and modal response façade through 0.x; "
                "permissions and modal lifecycle remain separately owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "detail-content":
            contract_guidance = (
                "Keep the formatted object iterable of (label, value) pairs as context. Preserve field order, labels, values, table rows, "
                "and normal template autoescaping for the presentation you retain.\n"
                "Legacy partial/detail.html remains the object_detail inclusion-tag façade through 0.x; field/relation/property formatting "
                "remains tag-owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "delete-shell":
            contract_guidance = (
                "Keep delete_content_template_paths context. Preserve the normal delete card and continue nested content delegation "
                "when the separately focused delete-content override should remain active.\n"
                "Legacy object_confirm_delete.html#pcrud_content routes normal and conflict responses through 0.x; permissions, guards, "
                "response handling, and modal lifecycle remain separately owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "delete-content":
            contract_guidance = (
                "Keep request, object_verbose_name, object, delete_errors, delete_view_url, use_htmx, original_target, form, "
                "and delete_actions_template_paths context. Preserve confirmation/errors, POST and HTMX transport, CSRF, repeated retained "
                "query inputs, form rendering, and nested action delegation.\n"
                "Legacy object_confirm_delete.html#normal_content remains directly addressable through 0.x; deletion decisions and modal/error "
                "responses remain Python-owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "delete-actions":
            contract_guidance = (
                "This component requires no template context. Keep a destructive submit control inside the surrounding delete form "
                "and retain an accessible Delete label.\n"
                "The delete-content component owns action URL, CSRF, retained state, and HTMX/modal behavior; legacy "
                "object_confirm_delete.html#normal_content remains through 0.x, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "delete-conflict":
            contract_guidance = (
                "Full GET context includes conflict_message, object, use_modal, use_htmx, list_view_url, request, default_page_size, "
                "and original_target. Preserve the conflict body, modal return suppression, normal list link, and HTMX page-size/target/history hooks.\n"
                "Legacy object_confirm_delete.html#conflict_detected and #pcrud_content remain server-addressable through 0.x; direct HTMX POST "
                "conflicts retain their historically minimal context, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "inline-row-display":
            contract_guidance = (
                "Keep row, inline_edit, enable_selection_controls, selected_ids, list_view_url, has_row_actions, and "
                "bulk_selection_controls_template_paths context. Preserve row identity/status/URL, selection delegation, field/dependency "
                "metadata, editable and blocked affordances, links, tooltips, and aligned actions.\n"
                "Legacy partial/list.html#inline_row_display and the built-in table-row façade remain through 0.x; inline lifecycle and events "
                "remain package-owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "inline-row-form":
            contract_guidance = (
                "Keep row, form, inline_hidden_fields, inline_config, inline_save_url, inline_cancel_url, enable_selection_controls, "
                "selected_ids, list_view_url, and action_button_classes context. Preserve active-row identity/URL, bound fields and labels, "
                "dependency/error metadata, hidden preserved fields, CSRF, action alignment, and exact Save/Cancel HTMX hooks.\n"
                "Legacy partial/list.html#inline_row_form remains server-addressable through 0.x; inline-field dependency responses have their "
                "own focused boundary, while initial and invalid-save validation remain owned by inline-row-form. Lifecycle JavaScript remains "
                "package-owned, and no copied PowerCRUD JavaScript is required."
            )
        elif component == "inline-field":
            contract_guidance = (
                "Keep field, field_name, field_dependency, and dependency_endpoint_url context. Preserve one stable inline-field-widget root, "
                "data-inline-field, dependency parent/endpoint metadata, and the rendered bound field with its widget-supplied hooks.\n"
                "The legacy direct partial/inline_field.html path remains available through 0.x; inline-row-form owns save validation, while outerHTML "
                "replacement, dependencies, and searchable-select reinitialization remain package-owned, and no copied PowerCRUD JavaScript is required."
            )
        else:
            raise CommandError(
                f"Focused component '{component}' is registered without contract guidance."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully copied focused {component} component:\n"
                f"From: {source_path}\n"
                f"To: {target_path}\n"
                "The copied component is selected automatically for this model where the focused component is rendered.\n"
                f"{contract_guidance}"
            )
        )

    def _copy_project_assets(
        self,
        template_pack: TemplatePack,
        app_path: Path,
        app_name: str,
    ) -> None:
        """Copy a complete package-owned manual-static runtime snapshot for one app."""
        destination_root = app_path / "static" / app_name / "powercrud"
        copied_paths: list[tuple[Path, Path]] = []

        try:
            for source_dir, destination_relative_path in self.get_project_asset_sources(
                template_pack
            ):
                if not source_dir.exists():
                    raise CommandError(f"Pack asset directory not found: {source_dir}")
                destination_dir = destination_root / destination_relative_path
                shutil.copytree(
                    source_dir,
                    destination_dir,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(*self.asset_copy_ignored_names),
                )
                copied_paths.append((source_dir, destination_dir))
        except CommandError:
            raise
        except OSError as exc:
            raise CommandError(f"Failed to copy project assets: {exc}") from exc

        css_path, script_path, dependency_guidance = self._get_asset_activation_guidance(
            template_pack, app_name
        )
        source_selector = self.project_template_pack_selectors[template_pack.identity]
        copied_lines = "\n".join(
            f"From: {source_path}\nTo: {destination_path}"
            for source_path, destination_path in copied_paths
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Copied the {template_pack.identity} manual-static asset snapshot.\n"
                f"{copied_lines}\n\n"
                "Replace the package-owned PowerCRUD asset tags in your base template; "
                "do not load both entries because the first runtime loaded wins.\n"
                "Load the selected pack's required vendor dependencies before this entry:\n"
                f"{dependency_guidance}\n\n"
                "Add these application-owned asset tags:\n"
                "{% load static %}\n"
                f"<link rel=\"stylesheet\" href=\"{{% static '{css_path}' %}}\">\n"
                f"<script type=\"module\" src=\"{{% static '{script_path}' %}}\"></script>\n\n"
                "This snapshot has no file-by-file fallback to package assets. Keep the "
                "copied files needed by the selected entry. It supports manual-static "
                "loading only; do not combine it with PowerCRUD's packaged Vite entry.\n"
                "Use this matching runtime setting:\n"
                "POWERCRUD_SETTINGS = {\n"
                f"    \"POWERCRUD_TEMPLATE_PACK\": \"{source_selector}\",\n"
                "}"
            )
        )

    def _get_asset_activation_guidance(
        self, template_pack: TemplatePack, app_name: str
    ) -> tuple[str, str, str]:
        """Return pack-specific manual-static paths and dependency guidance."""
        if template_pack.identity == "bootstrap5":
            return (
                f"{app_name}/powercrud/contrib/bootstrap5/css/bootstrap5.css",
                f"{app_name}/powercrud/contrib/bootstrap5/js/bootstrap5.js",
                "Bootstrap CSS and bootstrap.bundle, HTMX, and Tom Select.",
            )
        return (
            f"{app_name}/powercrud/css/powercrud.css",
            f"{app_name}/powercrud/js/powercrud.js",
            "your DaisyUI/Tailwind assets, HTMX, Tom Select, and Tippy.",
        )

    def _get_project_source_template_pack(self, pack_name: str) -> TemplatePack:
        """Resolve one first-party pack supported by project-level copying."""
        selector = self.project_template_pack_selectors[pack_name]
        try:
            return resolve_template_pack(selector)
        except Exception as exc:
            raise CommandError(
                f"Could not load source template pack '{pack_name}': {exc}"
            ) from exc

    def _copy_project_template_pack(
        self,
        template_pack: TemplatePack,
        target_dir: Path,
        app_template_dir: Path,
        app_name: str,
        scope: str,
    ) -> None:
        """Copy selected first-party pack templates into a project override root."""
        source_dir = self.get_template_source_dir(template_pack)
        if not source_dir.exists():
            raise CommandError(
                f"Could not find template directory: {source_dir}. "
                "Make sure powercrud is installed correctly and templates are available."
            )

        target_dir.mkdir(exist_ok=True)
        app_template_dir.mkdir(exist_ok=True)
        destination_dir = app_template_dir / "powercrud" / template_pack.identity

        try:
            if scope == "all":
                shutil.copytree(source_dir, destination_dir, dirs_exist_ok=True)
                copied_description = "the complete template pack, including components"
                copied_source = source_dir
                copied_destination = destination_dir
            elif scope == "core":
                destination_dir.mkdir(parents=True, exist_ok=True)
                for template_name in self.project_core_template_names:
                    source_path = source_dir / template_name
                    if not source_path.exists():
                        raise CommandError(f"Template not found: {source_path}")
                    shutil.copy2(source_path, destination_dir / template_name)
                copied_description = "the four main CRUD templates"
                copied_source = source_dir
                copied_destination = destination_dir
            else:
                template_name = self.project_root_template_names.get(scope)
                if template_name is None:
                    raise CommandError(f"Unsupported project template scope: {scope}")
                source_path = source_dir / template_name
                if not source_path.exists():
                    raise CommandError(f"Template not found: {source_path}")
                destination_dir.mkdir(parents=True, exist_ok=True)
                destination_path = destination_dir / template_name
                shutil.copy2(source_path, destination_path)
                copied_description = f"the {scope} root template ({template_name})"
                copied_source = source_path
                copied_destination = destination_path
        except CommandError:
            raise
        except OSError as exc:
            raise CommandError(f"Failed to copy project templates: {exc}") from exc

        config_path = f"{app_name}/powercrud/{template_pack.identity}"
        complete_override_setting = (
            "    template_override_complete = True\n" if scope == "all" else ""
        )
        pack_guidance = (
            "Keep POWERCRUD_TEMPLATE_PACK set to the same source pack so the "
            "project copy and runtime assets stay aligned."
            if scope == "all"
            else "Keep POWERCRUD_TEMPLATE_PACK set to the same source pack so missing "
            "templates and components continue to fall back to that pack."
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Copied {copied_description} from the {template_pack.identity} pack.\n"
                f"From: {copied_source}\n"
                f"To: {copied_destination}\n\n"
                "Configure the views that should use these project overrides:\n"
                f'    template_override_path = "{config_path}"\n'
                f"{complete_override_setting}\n"
                f"{pack_guidance}"
            )
        )

    def _copy_single_template(self, options, target_dir, app_template_dir):
        """Copy a single template file."""
        model = options["model"]
        role = options["role"]

        if role == "list":
            suffix = "_list.html"
        elif role == "detail":
            suffix = "_detail.html"
        elif role == "form":
            suffix = "_form.html"
        elif role == "delete":
            suffix = "_confirm_delete.html"

        template_name = f"{model.lower()}{suffix}"

        try:
            source_path = self.get_template_source_dir() / f"object{suffix}"

            if not source_path.exists():
                raise CommandError(f"Template not found: {source_path}")

            # Create target directories if they don't exist
            target_dir.mkdir(exist_ok=True)
            app_template_dir.mkdir(exist_ok=True)

            # Copy the template
            target_path = app_template_dir / template_name
            shutil.copy2(source_path, target_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully copied template:\n"
                    f"From: {source_path}\n"
                    f"To: {target_path}"
                )
            )
        except Exception as e:
            raise CommandError(f"Failed to copy template: {str(e)}")

    def _copy_all_model_templates(self, model_name, target_dir, app_template_dir):
        """Copy all CRUD templates for a specific model."""
        templates = {
            "list": "_list.html",
            "detail": "_detail.html",
            "form": "_form.html",
            "delete": "_confirm_delete.html",
        }

        # Create target directories if they don't exist
        target_dir.mkdir(exist_ok=True)
        app_template_dir.mkdir(exist_ok=True)

        for template_type, suffix in templates.items():
            try:
                source_path = self.get_template_source_dir() / f"object{suffix}"

                if not source_path.exists():
                    self.stdout.write(
                        self.style.WARNING(f"Template not found: {source_path}")
                    )
                    continue

                template_name = f"{model_name.lower()}{suffix}"
                target_path = app_template_dir / template_name

                shutil.copy2(source_path, target_path)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully copied {template_type} template:\n"
                        f"From: {source_path}\n"
                        f"To: {target_path}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to copy {template_type} template: {str(e)}"
                    )
                )
