from fastapi import FastAPI, Request, Response, Cookie
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from pathlib import Path
import tellet
import pandas as pd
from enum import Enum
from datetime import datetime
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from loguru import logger
import json
from functools import wraps

from fastapi.responses import RedirectResponse


module_dir = Path(tellet.__file__).parent.parent
fp = module_dir / "data" / "data.csv"
static_dir = module_dir / "static"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class LoginRequestForm(BaseModel):
    username: str
    workspace: str


def authenticated(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = await get_current_user(kwargs["request"])
        logger.warning(f"{current_user=}")
        if current_user is None:
            resp = RedirectResponse(url="/login", status_code=302)
            return resp
        return await func(*args, **kwargs)

    return wrapper


@app.get("/list/{where}")
async def list(where: TableName) -> list[Entry]:
    res = data.query(f"where == '{where.value}'").reset_index()
    res = [Entry(**e) for e in res.to_dict(orient="records")]
    return res


@app.post("/add/")
async def add(entry: AddingEntry, username: str = Cookie()) -> Entry:
    global data
    current_user = username

    when = datetime.strftime(datetime.now(), "entry%Y%m%d%H%M%S")
    d = {"who": current_user, "what": entry.what, "where": entry.where.value}

    data.loc[when] = d
    data.to_csv(fp)

    return Entry(who=d["who"], what=d["what"], when=when)


@app.post("/edit/")
async def edit(entry: EditingEntry, username: str = Cookie()) -> Entry:
    global data
    current_user = username

    d = {"who": current_user, "what": entry.what, "where": entry.where.value}

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


@app.get("/")
@authenticated
async def landing_page(request: Request):
    current_user = await get_current_user(request)
    workspace = await get_current_workspace(request)
    print(current_user)
    args = {
        "request": request,
        "username": current_user,
        "version": "v2.0",
        "ws": workspace,
    }
    return templates.TemplateResponse("html/index.html", args)


@app.get("/shopping")
@authenticated
async def shopping(request: Request):
    modals = open(static_dir / "html" / "modals" / "fridge.html").read()
    return templates.TemplateResponse(
        "html/shopping.html", {"request": request, "modals": modals}
    )


@app.get("/reports")
@authenticated
async def reports(request: Request):
    current_user = get_current_user(request)
    workspace = get_current_workspace(request)
    logger.info(f"*** {current_user} is reporting.")

    j = json.load(open(module_dir / "data" / "users.json"))
    default_reports = j["default"]
    rep = j[workspace].get("reports", [])

    rep.extend(default_reports)

    tpl2 = """<p><div class="col-md-6">{buttons}</div></p>"""
    tpl = """<button type="button" class="btn btn-secondary">
                <img id="{id}" data-description="{desc}" data-value="{value}" width=75 src="/static/data/icons/{id}.png">
                </button> """

    reports = [tpl.format(id=id, desc=desc, value=value) for desc, id, value in rep]

    html_reports = ""
    i = 0
    while i < len(reports):
        html_reports += tpl2.format(buttons="".join(reports[i : i + 3]))
        i += 3

    return templates.TemplateResponse(
        "html/reports.html", {"request": request, "reports": html_reports}
    )


@app.post("/auth/login")
def auth_login(resp: Response, data: LoginRequestForm):
    logger.success("Successful authentication")
    resp.set_cookie(key="username", value=data.username)
    resp.set_cookie(key="workspace", value=data.workspace)
    return True


@app.get("/login")
async def login(request: Request, ws: str = None):
    if ws is None:
        logger.error(f"{ws=}")
        return

    users = json.load(open(module_dir / "data" / "users.json"))
    users.pop("default")

    return templates.TemplateResponse(
        "html/login.html",
        {"request": request, "ws": ws, "users": json.dumps(users)},
    )


@app.get("/auth/logout")
@authenticated
async def logout(resp: Response, request: Request):
    resp = RedirectResponse(
        url="/login?ws=cha", status_code=302
    )  # status.HTTP_302_FOUND)
    resp.delete_cookie("username")
    resp.delete_cookie("workspace")
    return resp


@app.get("/current_user")
async def get_current_user(request: Request):
    username = request.cookies.get("username")
    print(username)
    return username
    return {"username": username}


@app.get("/current_workspace")
async def get_current_workspace(request: Request):
    workspace = request.cookies.get("workspace")

    return workspace
    return {"workspace": workspace}
