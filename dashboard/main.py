from __future__ import annotations

import json
import pathlib
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

_ROOT   = pathlib.Path(__file__).parent.parent
_OUTPUT = _ROOT / "output" / "trajectory.json"
_CLI    = _ROOT / "build" / "cli" / "kinematrix_cli"
_STATIC = pathlib.Path(__file__).parent / "static"


class RunRequest(BaseModel):
    input: str = "data/sample_path.csv"
    density: int = 100


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.get("/api/trajectory")
def get_trajectory() -> JSONResponse:
    if not _OUTPUT.exists():
        raise HTTPException(
            status_code=404,
            detail="No trajectory file. POST /api/run first.",
        )
    return JSONResponse(json.loads(_OUTPUT.read_text()))


@app.post("/api/run")
def run_engine(req: RunRequest) -> dict:
    result = subprocess.run(
        [str(_CLI), str(_ROOT / req.input), str(_OUTPUT),
         "--density", str(req.density)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr)
    data = json.loads(_OUTPUT.read_text())
    return {
        "duration_us": data["meta"]["duration_us"],
        "count":       data["meta"]["count"],
    }


app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
