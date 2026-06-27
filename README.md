# Cronometer History Search

Search personal food/meal history exported from [Cronometer](https://cronometer.com). Available as a terminal TUI or a local web interface.

## Setup

```bash
uv sync
```

## Usage

**TUI** (terminal) — requires a CSV in `input/` first

```bash
uv run cronometer-search                   # auto-discover latest CSV in input/
uv run cronometer-search --csv path/to.csv --count 5
```

**Web** (browser at `http://localhost:8000`)

```bash
uv run cronometer-websearch                # auto-discover, port 8000
uv run cronometer-websearch --csv path/to.csv --port 8080
```

The web server starts without a CSV — use **Upload CSV** in the browser settings panel to load one. To pick up a new CSV without restarting, use **Upload CSV** or drop a file in `input/` and click **Reload CSV**.

Both interfaces perform a case-insensitive substring search on food names and display the most recent matching meals. An empty query returns no results.

## Security

The web server has no authentication, authorization, or HTTPS. It is designed for **local/LAN use only** — run it on a trusted network and do not expose it to the public internet.

## Stack

- [Textual](https://textual.textualize.io/) — TUI
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — web server
- [htmx](https://htmx.org/) + [Pico CSS](https://picocss.com/) — browser UI
- pandas — CSV parsing
