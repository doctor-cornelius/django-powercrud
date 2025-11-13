---
date: 2025-11-13
categories:
  - styles
  - inline
---
# Make Inline Multi-Select Single Row Height

When there is a M2M field, we get a multiple select element that makes the row taller. I dont want that. I want the element to stay single row height (like with regular dropdowns) but allow picking multiple options from a dropdown list. This post looks at 2 options: (a) roll your own; and (b) use [Tom Select](https://tom-select.js.org/).

<!-- more -->

## The Tom Select Option

If we use Tom Select, we would need to:

- vendor it with the package so downstream users don't have to separately install it (we could do that but it seems extra fiddly). We would keep the version updated with `renovate` and use `new_release.sh` to run `npm build`.
- ensure the element in the row does not expand either height or width. To restrict width we could change the display from chips to just show `n` selected.

If this works, it might be an advantage if it's CSS framework independent. Whereas "roll your own" may  require reworking with each new template pack. 

Here is what works in CodePen.

=== "html"

    ```html
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/css/tom-select.default.min.css">
    <script src="https://cdn.jsdelivr.net/npm/tom-select@2.3.1/dist/js/tom-select.complete.min.js"></script>

    <div class="p-4 inline-picker" id="state-picker">
        <span class="picker-summary" data-ts-summary>Select a state…</span>
        <select id="select-state" name="state[]" multiple autocomplete="off">
            <option value="AL">Alabama</option>
            <option value="AK">Alaska</option>
            <option value="AZ">Arizona</option>
            <option value="AR">Arkansas</option>
            <option value="CA" selected>California</option>
            <option value="CO">Colorado</option>
            <option value="CT">Connecticut</option>
            <option value="DE">Delaware</option>
            <option value="DC">District of Columbia</option>
            <option value="FL">Florida</option>
            <option value="GA">Georgia</option>
            <option value="HI">Hawaii</option>
            <option value="ID">Idaho</option>
            <option value="IL">Illinois</option>
            <option value="IN">Indiana</option>
            <option value="IA">Iowa</option>
            <option value="KS">Kansas</option>
            <option value="KY">Kentucky</option>
            <option value="LA">Louisiana</option>
            <option value="ME">Maine</option>
            <option value="MD">Maryland</option>
            <option value="MA">Massachusetts</option>
            <option value="MI">Michigan</option>
            <option value="MN">Minnesota</option>
            <option value="MS">Mississippi</option>
            <option value="MO">Missouri</option>
            <option value="MT">Montana</option>
            <option value="NE">Nebraska</option>
            <option value="NV">Nevada</option>
            <option value="NH">New Hampshire</option>
            <option value="NJ">New Jersey</option>
            <option value="NM">New Mexico</option>
            <option value="NY">New York</option>
            <option value="NC">North Carolina</option>
            <option value="ND">North Dakota</option>
            <option value="OH">Ohio</option>
            <option value="OK">Oklahoma</option>
            <option value="OR">Oregon</option>
            <option value="PA">Pennsylvania</option>
            <option value="RI">Rhode Island</option>
            <option value="SC">South Carolina</option>
            <option value="SD">South Dakota</option>
            <option value="TN">Tennessee</option>
            <option value="TX">Texas</option>
            <option value="UT">Utah</option>
            <option value="VT">Vermont</option>
            <option value="VA">Virginia</option>
            <option value="WA">Washington</option>
            <option value="WV">West Virginia</option>
            <option value="WI">Wisconsin</option>
            <option value="WY" selected>Wyoming</option>
        </select>
    </div>
    ```

=== "css"

    ```css
    .inline-picker {
    position: relative;
    max-width: 320px;
    font-family: system-ui, sans-serif;
    }

    .picker-label {
    display: block;
    margin-bottom: 0.15rem;
    font-size: 0.85rem;
    color: #374151;
    }

    .picker-summary {
    position: absolute;
    top: 50%;
    left: 20%;
    transform: translate(-50%, -50%);
    pointer-events: none;
    color: #111827;
    font-size: 0.9rem;
    font-weight: 500;
    transition: color 0.15s ease;
    z-index: 10;
    }

    .picker-summary.is-empty {
    color: #9ca3af; /* lighter text when zero selected */
    }

    .ts-wrapper {
    width: 100%;
    }

    .ts-wrapper.multi .ts-control {
    min-height: 42px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    overflow: hidden;
    }

    .ts-wrapper.multi .ts-control .item {
    display: none;            /* hide the chips so height stays single-line */
    }

    .ts-wrapper.multi .ts-control input {
    width: 0;
    flex: 0 0 auto;
    padding: 0;
    margin: 0;
    }

    .ts-dropdown {
    max-height: 240px;
    overflow-y: auto;
    }
    .inline-picker {
    position: relative;
    max-width: 320px;
    font-family: system-ui, sans-serif;
    }

    .picker-label {
    display: block;
    margin-bottom: 0.15rem;
    font-size: 0.85rem;
    color: #374151;
    }

    .picker-summary {
    position: absolute;
    top: 38px;
    left: 14px;
    pointer-events: none;
    color: #111827;
    font-size: 0.9rem;
    font-weight: 500;
    transition: color 0.15s ease;
    z-index: 10;  /* Ensure it stays on top */
    }

    .picker-summary.is-empty {
    color: #9ca3af; /* lighter text when zero selected */
    }

    .ts-wrapper {
    width: 100%;
    }

    .ts-wrapper.multi .ts-control {
    min-height: 42px;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    overflow: hidden;
    background: white;  /* Ensure visible background */
    border: 1px solid #d1d5db;  /* Add border for button-like appearance */
    border-radius: 0.375rem;
    cursor: pointer;
    }

    .ts-wrapper.multi .ts-control .item {
    display: none;  /* Hide chips */
    }

    .ts-wrapper.multi .ts-control input {
    width: 0;
    flex: 0 0 auto;
    padding: 0;
    margin: 0;
    opacity: 0;  /* Make input invisible */
    position: absolute;  /* Remove from layout */
    pointer-events: none;  /* Prevent interaction */
    }

    .ts-wrapper.multi .ts-control::after {
    content: '▼';  /* Add dropdown arrow */
    position: absolute;
    right: 10px;
    color: #6b7280;
    pointer-events: none;
    }

    .ts-dropdown {
    max-height: 240px;
    overflow-y: auto;
    }
    ```

=== "js"

    ```js
    const summaryEl = document.querySelector('[data-ts-summary]');

    function updateSummary(instance) {
    const count = instance.getValue().length;
    summaryEl.textContent = `Selected: ${count}`;
    summaryEl.classList.toggle('is-empty', count === 0);
    }

    const pickerConfig = {
    plugins: ['checkbox_options', 'remove_button'],
    persist: false,
    closeAfterSelect: false,
    onInitialize() {
        updateSummary(this);
    },
    onItemAdd() {
        updateSummary(this);
    },
    onItemRemove() {
        updateSummary(this);
    }
    };

    const ts = new TomSelect('#select-state', pickerConfig);

    ```

## Roll Your Own

### TLDR;

This works in CodePen (NB no CSS needed). It detects last row and makes the dropdown actually drop **up**.

=== "html"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DaisyUI Table with Roll-Your-Own Multi-Select</title>
        <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="p-4 bg-base-200">
        <div class="container mx-auto">
            <h1 class="text-2xl font-bold mb-4">Books Table</h1>
            <table class="table table-zebra w-full">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Genres</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>The Mystery of the Old Mill</td>
                        <td>Enid Blyton</td>
                        <td>
                            <div class="dropdown dropdown-bottom">
                                <div tabindex="0" role="button" class="btn btn-sm btn-outline w-32 text-left" onclick="toggleDropdown('genres-1')">
                                    <span id="summary-1">Selected: 2</span>
                                </div>
                                <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow hidden" id="dropdown-1">
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="1" checked onchange="updateSummary('genres-1', 1)"> Fiction</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="2" checked onchange="updateSummary('genres-1', 1)"> Mystery</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="3" onchange="updateSummary('genres-1', 1)"> Adventure</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="4" onchange="updateSummary('genres-1', 1)"> Children</label></li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>Pride and Prejudice</td>
                        <td>Jane Austen</td>
                        <td>
                            <div class="dropdown dropdown-bottom">
                                <div tabindex="0" role="button" class="btn btn-sm btn-outline w-32 text-left" onclick="toggleDropdown('genres-2')">
                                    <span id="summary-2">Selected: 1</span>
                                </div>
                                <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow hidden" id="dropdown-2">
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="1" onchange="updateSummary('genres-2', 2)"> Fiction</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="5" checked onchange="updateSummary('genres-2', 2)"> Romance</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="6" onchange="updateSummary('genres-2', 2)"> Classic</label></li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>The Hobbit</td>
                        <td>J.R.R. Tolkien</td>
                        <td>
                            <div class="dropdown dropdown-top">
                                <div tabindex="0" role="button" class="btn btn-sm btn-outline w-32 text-left" onclick="toggleDropdown('genres-3')">
                                    <span id="summary-3">Selected: 3</span>
                                </div>
                                <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow hidden" id="dropdown-3">
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="1" checked onchange="updateSummary('genres-3', 3)"> Fiction</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="3" checked onchange="updateSummary('genres-3', 3)"> Adventure</label></li>
                                    <li><label class="cursor-pointer"><input type="checkbox" class="checkbox checkbox-sm" value="7" checked onchange="updateSummary('genres-3', 3)"> Fantasy</label></li>
                                </ul>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </body>
    </html>

    ```

=== "js"

    ```js
    function toggleDropdown(id) {
        const dropdown = document.getElementById('dropdown-' + id.split('-')[1]);
        dropdown.classList.toggle('hidden');
    }

    function updateSummary(prefix, rowId) {
        const checkboxes = document.querySelectorAll(`#dropdown-${rowId} input[type="checkbox"]`);
        const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
        document.getElementById(`summary-${rowId}`).textContent = `Selected: ${checkedCount}`;
    }

    ```

Design goals below:

### Goal
Replace a tall `<select multiple>` with a single-line dropdown that expands downward to allow multiple selections — **without using external libraries** like Tom Select or Alpine.js.

---

### UX Description
- In normal state, show a single compact line displaying selected items (e.g. `Fiction, Mystery, RomCom`).
- When clicked, open a dropdown below that lists all possible items with checkboxes.
- User ticks or unticks as desired.
- Clicking **Save** posts the full selection to the server (not each change).
- Dropdown closes and the summary line updates.

---

### Technical Structure
- Built with **DaisyUI/Tailwind** for styling.
- Uses a **form with checkboxes**, each named `genres` and carrying the genre ID.
- Wrapped in an HTMX form:

```html
<form hx-post="{% url 'book-update-genres' book.id %}"
      hx-target="#genre-picker"
      hx-swap="outerHTML">
```

- “Save” button triggers one `hx-post` sending all checked values (`genres=1&genres=3&genres=4`).

---

### Interaction Logic
- Dropdown visibility toggled with a single line of Hyperscript or vanilla JS (`toggle .hidden`).
- No JS dependencies required.
- Optional partial re-render via HTMX swaps updated summary markup.

---

### View Handling
Django receives the same payload as a standard multi-select form.

Example view:

```python
def book_update_genres(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        ids = request.POST.getlist("genres")
        book.genres.set(ids)
    return render(request, "partials/_genre_picker.html", {
        "book": book,
        "all_genres": Genre.objects.all(),
    })
```

---

### Key Principles
- **No external JS** — only optional inline toggle for dropdown.
- **Compact UX** — single line at rest, dropdown on demand.
- **Multi-select** via native checkboxes.
- **Clean Django integration** — standard POST semantics, works in full or partial render contexts.
