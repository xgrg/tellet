from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from pathlib import Path
import tellet
import pandas as pd
from enum import Enum
from datetime import datetime
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="static")


moduledir = Path(tellet.__file__).parent.parent
fp = moduledir / "data" / "data.csv"

columns = ["when", "who", "what", "where"]
data = pd.DataFrame(columns=columns).set_index("when")

if fp.exists():
    data = pd.read_csv(fp).set_index("when")
else:
    data.to_csv(fp, index=False)


class Entry(BaseModel):
    who: str
    when: str
    what: str


class TableName(str, Enum):
    SHOPPING = "shopping"
    REPORTS = "reports"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/list/{where}")
async def list(where: TableName) -> list[Entry]:
    res = data.query(f"where == '{where.value}'").reset_index()
    res = [Entry(**e) for e in res.to_dict(orient="records")]
    return res


@app.post("/add/")
async def add(what: str, where: TableName):
    who = "grg"
    when = datetime.strftime(datetime.now(), "%Y%m%d-%H%M%S")
    d = {"who": who, "what": what, "where": where.value}

    data.loc[when] = d
    return True


@app.post("/edit/")
async def edit(which: str, what: str, where: TableName):
    return


@app.post("/delete/")
async def delete(which: str, where: TableName):
    return


@app.post("/undo/")
async def undo(where: TableName):
    global data
    data = data.sort_index().iloc[:-1]

    return True


@app.get("/save")
async def save():
    data.to_csv(fp, index=False)
    return True


@app.get("/shopping", response_class=HTMLResponse)
async def shopping(request: Request):
    fp = moduledir / "static" / "html" / "modals" / "fridge.html"
    modals = open(fp).read()
    return templates.TemplateResponse(
        "html/shopping.html", {"request": request, "modals": modals}
    )
