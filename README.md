# Cronometer History Search

Search personal food/meal history exported from [Cronometer](https://cronometer.com). Available as a terminal TUI or a local web interface.

## Setup

```bash
uv sync
```

Drop one or more Cronometer CSV exports into `input/`.

## Usage

**TUI** (terminal)

```bash
uv run cronometer-search                   # auto-discover latest CSV in input/
uv run cronometer-search --csv path/to.csv --count 5
```

**Web** (browser at `http://localhost:8000`)

```bash
uv run cronometer-websearch                # auto-discover, port 8000
uv run cronometer-websearch --csv path/to.csv --port 8080
```

Both interfaces perform a case-insensitive substring search on food names and display the most recent matching meals. An empty query returns no results.

To pick up a new CSV without restarting the web server, click **Reload CSV** in the browser.

## Security

The web server has no authentication, authorization, or HTTPS. It is designed for **local/LAN use only** — run it on a trusted network and do not expose it to the public internet.

## Stack

- [Textual](https://textual.textualize.io/) — TUI
- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) — web server
- [htmx](https://htmx.org/) + [Pico CSS](https://picocss.com/) — browser UI
- pandas — CSV parsing
