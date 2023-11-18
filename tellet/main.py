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
from loguru import logger

module_dir = Path(tellet.__file__).parent.parent
fp = module_dir / "data" / "data.csv"
static_dir = module_dir / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=static_dir)

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


class AddingEntry(BaseModel):
    what: str
    where: TableName


class EditingEntry(BaseModel):
    when: str
    what: str
    where: TableName


class DeletingEntry(BaseModel):
    when: str


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/list/{where}")
async def list(where: TableName) -> list[Entry]:
    res = data.query(f"where == '{where.value}'").reset_index()
    res = [Entry(**e) for e in res.to_dict(orient="records")]
    return res


@app.post("/add/")
async def add(entry: AddingEntry) -> Entry:
    global data
    who = "grg"
    when = datetime.strftime(datetime.now(), "entry%Y%m%d%H%M%S")
    d = {"who": who, "what": entry.what, "where": entry.where.value}

    data.loc[when] = d
    data.to_csv(fp)

    return Entry(who=d["who"], what=d["what"], when=when)


@app.post("/edit/")
async def edit(entry: EditingEntry) -> Entry:
    global data
    who = "grg"
    d = {"who": who, "what": entry.what, "where": entry.where.value}

    data.loc[entry.when] = d
    data.to_csv(fp)
    return Entry(who=d["who"], what=d["what"], when=entry.when)


@app.post("/delete/")
async def delete(entry: DeletingEntry) -> DeletingEntry:
    global data
    data = data.drop(entry.when)
    data.to_csv(fp)
    return DeletingEntry(when=entry.when)


@app.post("/undo/")
async def undo(where: TableName):
    global data
    data = data.sort_index().iloc[:-1]

    return True


@app.get("/save")
async def save():
    data.to_csv(fp)
    return True


@app.get("/shopping", response_class=HTMLResponse)
async def shopping(request: Request):
    modals = open(static_dir / "html" / "modals" / "fridge.html").read()
    return templates.TemplateResponse(
        "html/shopping.html", {"request": request, "modals": modals}
    )


@app.get("/reports", response_class=HTMLResponse)
async def reports(request: Request):
    global username, session_name
    username = "grg"
    logger.info(f"*** {username} is reporting.")
    # users = get_users()[self.session["ws"]]
    rep = {}  # users.get("reports", [])
    default_reports = [
        ("Passer le pavé", "cleaning", "pavé"),
        ("Passer l'aspirateur", "vacuum", "aspirateur"),
        ("Faire une lessive", "washingmachine", "lessive"),
        ("Piscine", "swimmingpool", "piscine"),
        ("Nettoyer la douche", "shower", "douche"),
        ("Nettoyer une surface", "cleaningsurface", "nettoyer"),
        ("Sortir poubelles", "trashout", "poubelles"),
        ("(D)étendre le linge", "hangingclothes", "linge"),
        ("Vider le lave-vaisselle", "dishwasher", "lavevaisselle"),
        ("Nettoyer WC", "toilet", "wc"),
        ("Préparer le repas", "cooking", "cuisine"),
        ("Arroser les plantes", "waterplants", "plantes"),
    ]

    rep.extend(default_reports)
    tpl2 = """<p><div class="col-md-6">{buttons}</div></p>"""
    tpl = """<button type="button" class="btn btn-secondary">
                <img id="{id}" data-description="{desc}" data-value="{value}" width=75 src="/static/data/icons/{id}.png">
                </button> """
    reports = []
    for desc, id, value in rep:
        reports.append(tpl.format(id=id, desc=desc, value=value))

    html_reports = ""
    i = 0
    while i < len(reports):
        html_reports += tpl2.format(buttons="".join(reports[i : i + 3]))
        i += 3
    return templates.TemplateResponse(
        "html/reports.html", {"request": request, "reports": reports}
    )
