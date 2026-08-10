import argparse
import re
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from cronometer_search.loader import Meal, discover_csv, load_meals
from cronometer_search.search import search_meals

_csv_path: Path | None = None
_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _highlight(text: str, query: str) -> Markup:
    if not query:
        return Markup(escape(text))
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return Markup(pattern.sub(lambda m: f"<mark>{escape(m.group())}</mark>", escape(text)))


_templates.env.filters["highlight"] = _highlight


@asynccontextmanager
async def _lifespan(app: FastAPI):
    app.state.meals = load_meals(_csv_path) if _csv_path else []
    yield


app = FastAPI(lifespan=_lifespan)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _templates.TemplateResponse(request, "index.html")


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", count: int = 3) -> HTMLResponse:
    results = search_meals(request.app.state.meals, q, count)
    return _templates.TemplateResponse(
        request,
        "results.html",
        {"meals": results, "query": q},
    )


@app.post("/reload", response_class=HTMLResponse)
async def reload(request: Request) -> HTMLResponse:
    if not _csv_path:
        return HTMLResponse("No CSV loaded — upload one first")
    request.app.state.meals = load_meals(_csv_path)
    return HTMLResponse(f"Loaded {len(request.app.state.meals)} meals")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile | None = File(None)) -> HTMLResponse:
    global _csv_path
    # htmx swallows non-2xx responses, so failures are reported as 200 text instead
    if file is None:
        return HTMLResponse("No file received")
    parent = _csv_path.parent if _csv_path else Path.cwd() / "input"
    dest = parent / (file.filename or "upload.csv")
    # staged under a dot-name so a rejected upload can never be picked up by discover_csv
    tmp = parent / f".{dest.name}.incoming"
    try:
        parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(await file.read())
        meals = load_meals(tmp)
        tmp.replace(dest)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        return HTMLResponse(f"Upload failed: {type(exc).__name__}: {exc}")
    _csv_path = dest
    request.app.state.meals = meals
    return HTMLResponse(f"Loaded {len(meals)} meals")


def main() -> None:
    global _csv_path
    parser = argparse.ArgumentParser(
        description="Serve Cronometer history search over HTTP",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--csv",
        type=Path,
        metavar="PATH",
        help="path to Cronometer CSV export (default: auto-discover in ./input/)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="PORT",
        help="port to listen on",
    )
    args = parser.parse_args()
    if args.csv:
        _csv_path = args.csv
    else:
        input_dir = Path.cwd() / "input"
        input_dir.mkdir(exist_ok=True)
        try:
            _csv_path = discover_csv(input_dir)
        except FileNotFoundError:
            _csv_path = None
    uvicorn.run(app, host="0.0.0.0", port=args.port)
