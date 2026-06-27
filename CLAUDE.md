# Cronometer History Search

## Purpose

Interactive TUI and web interface for searching personal food/meal history exported from Cronometer.com.
Cronometer does not provide an API, so the user periodically exports history as CSV and drops it in `input/`.

## Tech Stack

- Python 3.11+
- [textual](https://textual.textualize.io/) — TUI framework
- [FastAPI](https://fastapi.tiangolo.com/) + [uvicorn](https://www.uvicorn.org/) — web server
- [Jinja2](https://jinja.palletsprojects.com/) — HTML templates
- [htmx](https://htmx.org/) (CDN) — live search in browser without a JS framework
- [Pico CSS](https://picocss.com/) v2 (CDN) — minimal styling, dark mode via `data-theme="dark"`
- pandas — CSV loading and grouping
- uv — environment and package management (preferred over pip/venv directly)

## Project Layout

```
cronometer-history-search/
├── input/                      # User drops Cronometer CSV exports here
├── src/
│   └── cronometer_search/
│       ├── __init__.py
│       ├── __main__.py         # TUI entry point, CLI argument parsing
│       ├── loader.py           # CSV discovery and parsing → structured data
│       ├── search.py           # Search logic (pure functions, no TUI/web imports)
│       ├── app.py              # textual TUI application
│       ├── web.py              # FastAPI web application
│       └── templates/
│           ├── index.html      # Full page (search input, count control, reload button)
│           └── results.html    # htmx partial — meal cards only
├── pyproject.toml
└── CLAUDE.md
```

## Data Model

### CSV Format

Cronometer exports one row per food item logged. Key columns (all others are ignored):

| Column | Type | Notes |
|---|---|---|
| `Day` | string | Date in `YYYY-MM-DD` format |
| `Group` | string | Meal group name — user-defined, not hardcoded |
| `Food Name` | string | Name of the food item |
| `Amount` | string | Quantity with units (e.g., `200.00 ml`, `1.00 Serving 2/3 cup`) — display as-is |
| `Energy (kcal)` | float | Calories; may be NaN for some entries — treat as 0.0 |

### Meal Definition

A **meal** is the unique combination of `Day` + `Group`. Group names are derived dynamically from the CSV — never hardcode group names like "Breakfast" or "Dinner". This ensures the app works with any user's data, including custom group names.

### Internal Data Structures

Use dataclasses:

```python
@dataclass
class FoodEntry:
    food_name: str
    amount: str       # display as-is
    kcal: float

@dataclass
class Meal:
    day: str          # YYYY-MM-DD
    group: str
    foods: list[FoodEntry]

    @property
    def total_kcal(self) -> float:
        return sum(f.kcal for f in self.foods)
```

## Module Responsibilities

### `loader.py`
- `discover_csv(input_dir: Path) -> Path` — finds the most recently modified `*.csv` in the given directory; raises `FileNotFoundError` if none found
- `load_meals(csv_path: Path) -> list[Meal]` — parses the CSV with pandas, groups rows by `(Day, Group)` preserving CSV order within each group, returns meals sorted newest-first by `Day`

### `search.py`
- `search_meals(meals: list[Meal], query: str, count: int) -> list[Meal]` — case-insensitive substring match on `Food Name` only; returns up to `count` most recent meals (already newest-first from loader) that contain at least one matching food; empty query returns empty list

### `app.py` (TUI)
- Textual `App` subclass
- Layout: search `Input` widget at top (always focused on launch), scrollable results `Container` below
- Results update on every keystroke via `on_input_changed`
- Each meal rendered as a Rich `Panel` containing a `Table` showing:
  - Header: `YYYY-MM-DD — Group Name`
  - Food rows: Amount | Food Name | kcal
  - Footer: total kcal for the meal
- Matching food names highlighted in bold yellow via Rich `Text.stylize`

### `web.py` (Web)
- FastAPI `app` with a Jinja2 `templates` instance pointed at `templates/` inside the package
- `_csv_path: Path | None` — module-level; `None` when no CSV exists at startup
- Meals loaded once at startup via `lifespan`; stored in `app.state.meals` (empty list when `_csv_path` is `None`)
- `_highlight(text, query) -> Markup` — server-side function registered as a Jinja2 filter; returns HTML-escaped text with case-insensitive matches wrapped in `<mark>`
- Routes:
  - `GET /` — renders `index.html` (full page)
  - `GET /search?q=&count=3` — renders `results.html` partial; htmx swaps `#results`
  - `POST /reload` — calls `load_meals`, updates `app.state.meals`, returns plain-text meal count; returns error message if `_csv_path` is `None`; htmx swaps `#reload-msg`
  - `POST /upload` — accepts `multipart/form-data` file upload (`python-multipart` required); saves to `_csv_path.parent` (or `./input/`, creating it if needed), updates `_csv_path` and `app.state.meals`, returns meal count; htmx swaps `#reload-msg`
- `main()` — argparse entry point; creates `./input/` if absent; sets `_csv_path` via `discover_csv` or `None` if no CSV found; runs uvicorn

### `__main__.py` (TUI entry point)
- Parses CLI args with `argparse`
- `--csv PATH` — explicit CSV path, skips auto-discovery
- `--count N` — meals to display (default: `3`)
- Loads data, instantiates and runs the textual `App`

## Search Behavior (both interfaces)

- Matches `Food Name` column only
- Case-insensitive substring match (no fuzzy matching)
- Empty search → show nothing
- Minimum character threshold: constant `MIN_SEARCH_CHARS = 1` in `search.py` — increase if performance is an issue on large CSVs; the full production history CSV is used during development intentionally

## Web Interface Details

### Templates
- `index.html` — Pico CSS v2 and htmx loaded from CDN; `data-theme="dark"` on `<html>`; search `<input>` with `hx-get="/search" hx-trigger="input changed delay:150ms"` and `hx-include="[name='count']"`; count `<input type="number">` with `hx-get="/search" hx-trigger="change"` and `hx-include="[name='q']"`; Reload CSV `<button>` with `hx-post="/reload"`; Upload CSV `<label>` (styled as button) wrapping a hidden `<input type="file">` — uses `hx-post="/upload"`, `hx-encoding="multipart/form-data"`, `hx-trigger="change from:input[type='file']"` to auto-upload on file selection with no JS
- `results.html` — one Pico `<article>` per meal with header, `<table>` of food rows, and a `<tfoot>` total row; food names passed through the `highlight` Jinja2 filter

### Highlighting
Implemented server-side in `web.py` as a Jinja2 filter, not in the template logic, to keep escaping correct:
```python
def _highlight(text: str, query: str) -> Markup:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return Markup(pattern.sub(lambda m: f"<mark>{escape(m.group())}</mark>", escape(text)))
```

### CSV Reload / Upload
The web server starts without a CSV (`app.state.meals = []`). Use **Upload CSV** in the settings panel to load one via the browser — it POSTs as multipart, saves to `./input/` (creating it if needed), and reloads meals. **Reload CSV** re-reads from the current `_csv_path` (for when a file is dropped manually). Both swap `#reload-msg` with the meal count and trigger a search refresh.

## Running

```bash
# TUI — auto-discover latest CSV in input/
uv run cronometer-search

# TUI — explicit CSV, custom count
uv run cronometer-search --csv path/to/export.csv --count 5

# Web — auto-discover, default port 8000
uv run cronometer-websearch

# Web — explicit CSV and port
uv run cronometer-websearch --csv path/to/export.csv --port 8080
```

## Style Guidelines

- Type hints everywhere
- Dataclasses for domain objects (see above)
- `loader.py` and `search.py` must have no `textual` or `fastapi` imports — keep logic decoupled
- No unit tests (personal tool)
- No comments unless the WHY is non-obvious
- pandas for CSV parsing and grouping; avoid raw `csv` module
