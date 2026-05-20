# Cronometer History Search

## Purpose

Interactive TUI for searching personal food/meal history exported from Cronometer.com.
Cronometer does not provide an API, so the user periodically exports history as CSV and drops it in `input/`.

## Tech Stack

- Python 3.11+
- [textual](https://textual.textualize.io/) — TUI framework
- pandas — CSV loading and grouping
- uv — environment and package management (preferred over pip/venv directly)

## Project Layout

```
cronometer-history-search/
├── input/                      # User drops Cronometer CSV exports here
├── src/
│   └── cronometer_search/
│       ├── __init__.py
│       ├── __main__.py         # Entry point, CLI argument parsing
│       ├── loader.py           # CSV discovery and parsing → structured data
│       ├── search.py           # Search and meal-grouping logic (pure functions, no TUI imports)
│       └── app.py              # textual TUI application
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

### `app.py`
- Textual `App` subclass
- Layout: search `Input` widget at top (always focused on launch), scrollable results `Container` below
- Results update on every keystroke via `on_input_changed`
- Each meal rendered as a distinct visual block showing:
  - Header: `YYYY-MM-DD — Group Name`
  - Food rows: Amount | Food Name | kcal
  - Footer: total kcal for the meal
- Matching food names are highlighted/marked within each meal block

### `__main__.py`
- Parses CLI args with `argparse`
- `--csv PATH` — explicit CSV path, skips auto-discovery
- `--count N` — meals to display (default: `3`)
- Loads data, instantiates and runs the `App`

## Search Behavior

- Matches `Food Name` column only
- Case-insensitive substring match (no fuzzy matching)
- Empty search → show nothing
- Minimum character threshold: constant `MIN_SEARCH_CHARS = 1` in `search.py` — increase if performance is an issue on large CSVs; the full production history CSV is used during development intentionally

## Running the App

```bash
# Auto-discover latest CSV in input/
uv run cronometer-search

# Explicit CSV path
uv run cronometer-search --csv path/to/export.csv

# Show 5 meals instead of default 3
uv run cronometer-search --count 5
```

## Style Guidelines

- Type hints everywhere
- Dataclasses for domain objects (see above)
- `loader.py` and `search.py` must have no `textual` imports — keep logic decoupled from the TUI
- No unit tests (personal tool)
- No comments unless the WHY is non-obvious
- pandas for CSV parsing and grouping; avoid raw `csv` module
