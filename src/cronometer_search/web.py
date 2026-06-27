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

_csv_path: Path
_templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _highlight(text: str, query: str) -> Markup:
    if not query:
        return Markup(escape(text))
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    return Markup(pattern.sub(lambda m: f"<mark>{escape(m.group())}</mark>", escape(text)))


_templates.env.filters["highlight"] = _highlight


@asynccontextmanager
async def _lifespan(app: FastAPI):
    app.state.meals = load_meals(_csv_path)
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
    request.app.state.meals = load_meals(_csv_path)
    return HTMLResponse(f"Loaded {len(request.app.state.meals)} meals")


@app.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)) -> HTMLResponse:
    global _csv_path
    dest = _csv_path.parent / (file.filename or "upload.csv")
    dest.write_bytes(await file.read())
    _csv_path = dest
    request.app.state.meals = load_meals(_csv_path)
    return HTMLResponse(f"Loaded {len(request.app.state.meals)} meals")


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
    _csv_path = args.csv if args.csv else discover_csv(Path.cwd() / "input")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
