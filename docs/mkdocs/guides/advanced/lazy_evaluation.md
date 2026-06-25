# Lazy Evaluation For Expensive UI State

PowerCRUD normally resolves list UI state while rendering the page. That is the right default for simple callbacks.

Use lazy evaluation when a callback is accurate but too expensive to run for every visible row during list rendering.

Lazy UI state is always opt-in. It is also display-only. Mutation endpoints must still validate server-side before changing data.

## API Styles

The Base API is the underlying contract. It uses ordinary dictionaries on the view.

The Structured API is a helper layer that compiles to the same Base API shape.

For lazy features, both styles support the same capability:

- Base API exposes the primitive keys directly.
- Structured API exposes matching constructor options.
- Existing eager behavior remains the default when the lazy mode option is omitted.

## Lazy Row-Action Disabled State

Use lazy row-action state when a dropdown row action is visible, but the exact disabled reason is expensive to calculate.

=== "Base API"

    ```python
    extra_actions_mode = "dropdown"
    extra_actions = [
        {
            "text": "Description Preview",
            "url_name": "sample:book-description-preview",
            "display_modal": True,
            "hidden_if": "should_hide_description_preview",
            "disabled_state": "get_description_preview_disabled_state",
            "disabled_state_mode": "lazy",
        },
    ]
    ```

=== "Structured API"

    ```python
    extra_actions_mode = "dropdown"
    extra_actions = [
        PowerAction(
            text="Description Preview",
            url_name="sample:book-description-preview",
            display_modal=True,
            hidden_if="should_hide_description_preview",
            disabled_state="get_description_preview_disabled_state",
            disabled_state_mode="lazy",
        ),
    ]
    ```

PowerCRUD still evaluates permission checks and `hidden_if` during list rendering. It defers only `disabled_state`, then resolves it when the row `More` menu opens.

Lazy row-action state is supported only for dropdown row actions. Visible button-mode row actions stay eager.

## Lazy Cell Tooltips

Use lazy cell tooltips when the tooltip text is useful, but the tooltip hook is too expensive to run for every visible cell during list rendering.

=== "Base API"

    ```python
    list_cell_tooltip_fields = {
        "pages": {
            "hook": "get_pages_tooltip",
            "mode": "lazy",
        },
    }
    ```

=== "Structured API"

    ```python
    power_fields = [
        PowerField(
            "pages",
            default_list=True,
            tooltip_hook="get_pages_tooltip",
            tooltip_mode="lazy",
        ),
    ]
    ```

PowerCRUD renders the cell with lazy tooltip metadata, but does not call the hook during list rendering. The hook runs when the user hovers or focuses the rendered cell.

Return plain text for the tooltip. Return `None` or a blank string when no tooltip should be shown for that row.

## Choosing Eager Or Lazy

Keep callbacks eager when they are cheap, needed for the initial visible state, or important for layout stability.

Use lazy mode when:

- the callback calls services or other expensive app logic
- the callback summarizes related or child records
- the callback builds a detailed reason most users will not inspect
- the list page is slow because the same hook runs for every visible row

Do not use lazy tooltip content as validation, permission, or workflow authority. It is presentation content only.

## Sample App

The sample book list demonstrates both lazy features:

- `/sample/bigbook/` uses lazy row-action disabled state on `Description Preview`.
- `/sample/bigbook/` uses lazy cell tooltip content on the default-visible `pages` column.
- `/sample/powerfield-book/` demonstrates the same tooltip behavior through `PowerField(..., tooltip_mode="lazy")`.
