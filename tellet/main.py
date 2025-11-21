from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta, timezone, date
from icalendar import Calendar

from pydantic import BaseModel
from pathlib import Path
import tellet
from tellet.radon import plot_radon
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import requests
from loguru import logger
from functools import wraps
from dateutil.rrule import rrulestr
import locale
import hashlib


try:
    locale.setlocale(locale.LC_ALL, "fr_FR.iso88591")  # set French locale
except locale.Error:
    locale.setlocale(locale.LC_ALL, "fr_FR.utf8")


module_dir = Path(tellet.__file__).parent.parent
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
ICAL_URL = ""
ICAL_URL2 = "" 
TODO_FILE = Path(__file__).resolve().parent.parent / "todo"

OPENMETEO_URL = "https://api.open-meteo.com/v1/meteofrance"


@app.get("/proxy-weather")
def proxy_weather(lat: float = 48.8566, lon: float = 2.3522):
    try:
        r = requests.get(
            OPENMETEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "windspeed_unit": "kmh",
            },
            timeout=5,
        )
        data = r.json()
        print(data)
        return JSONResponse(content=data.get("current_weather", {}))
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


class LoginRequestForm(BaseModel):
    username: str
    password: str


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


@app.get("/radon", response_class=HTMLResponse)
async def radon():
    full_html = plot_radon()
    return HTMLResponse(content=full_html)


def get_previous_monday(dt: datetime) -> datetime:
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    days_since_monday = midnight.weekday()
    return midnight - timedelta(days=days_since_monday)


def fix_summary(summary):
    summary = summary.replace("🏓", "🎾")
    # ratio = SequenceMatcher(None, summary, "Cha @ Paris").ratio()
    # if ratio > 0.8:
    #     summary = "✈️ Cha @ Paris"
    if "@ Paris" in summary:
        summary = "✈️ " + summary
    if "chographie" in summary or "Aligier" in summary or "ALIGIER" in summary:
        summary = "🏥 " + summary
    if "ADMR" in summary:
        summary = "🏠 " + summary
    if "Championnat" in summary:
        summary = "🎾 " + summary
    if "Baby" in summary and "Gym" in summary:
        summary = "🏃 " + summary
    if "Baby" in summary and "Cricri" in summary:
        summary = "🌼 " + summary
    return summary


combinations = [
    ["#8c4a6d", "#fce9f3"],
    ["#3f6fa0", "#e6f2fc"],
    ["#7aa37a", "#eef6ee"],
    ["#c57a7a", "#fdeeee"],
    ["#a05c2c", "#f7f0ea"],
    ["#6a5fa3", "#efecfb"],
    ["#aa5275", "#f7e8ef"],
    ["#2f7e7e", "#e3f9f9"],
    ["#b45c8a", "#fae6f3"],
    ["#5778a1", "#e8f0fa"],
    ["#ca7930", "#fff3e6"],
    ["#6b9a6b", "#e9f5ea"],
    ["#a15d5d", "#f8ecec"],
    ["#5a7fa8", "#e4eef9"],
    ["#b35757", "#f6eaea"],
    ["#7c6bb3", "#f0edf9"],
    ["#8a3e5e", "#f7e3ee"],
    ["#4d8c8c", "#e3f6f6"],
    ["#c06363", "#fbecec"],
    ["#5b7f9a", "#e8f2fa"],
]


def hash_to_range(s: str, n: int) -> int:
    """Retourne un entier dans [0, n) à partir d'une chaîne."""
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    # conversion en entier puis modulo n
    return int(h, 16) % n


def get_colors(summary):
    if "Cha @" in summary:
        return ["#872860", "#e3f2fd"]
    if "✈️" in summary:
        return ["burlywood", "black"]
    if "ADMR" in summary:
        return ["#4d71a9", "#e3f2fd"]
    if "🎾" in summary:
        return ["#b52d2d", "#e3f2fd"]
    if "Gym" in summary:
        return ["cadetblue", "#e3f2fd"]
    if "Baby" in summary and "Cricri" in summary:
        return ["#799d74", "#e3f2fd"]
    if summary.isupper():
        return ["#dd6a6a", "e3f2fd"]
    if "Roxane" in summary:
        return ["#ffdddd", "#301c1c"]
    if "Therapixel" in summary:
        return ["#f62ed2", "#e3f2fd"]
    return combinations[hash_to_range(summary, len(combinations))]


def fetch_upcoming_events(ical_url: str):
    response = requests.get(ical_url)
    response.raise_for_status()
    cal = Calendar.from_ical(response.content)

    now = datetime.now(timezone.utc)
    start_window = get_previous_monday(now).astimezone(timezone.utc)
    end_window = start_window + timedelta(weeks=4)

    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        # Skip cancelled instances
        if component.get("STATUS") == "CANCELLED":
            continue

        summary = fix_summary(str(component.get("SUMMARY")))
        colors = get_colors(summary)

        dtstart = component.get("DTSTART").dt
        dtend = component.get("DTEND").dt

        # Normalize datetime
        def normalize(dt):
            if not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
            elif dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt

        dtstart = normalize(dtstart)
        dtend = normalize(dtend)

        # Adjust all-day end dates (optional)
        if dtend.time() == datetime.min.time():
            dtend -= timedelta(microseconds=1)

        duration = dtend - dtstart

        # Handle EXDATE (exceptions)
        exdates = set()
        if component.get("EXDATE"):
            ex_fields = component.get("EXDATE")
            if not isinstance(ex_fields, list):
                ex_fields = [ex_fields]
            for ex in ex_fields:
                for d in ex.dts:
                    ex_dt = normalize(d.dt)
                    exdates.add(ex_dt.date())

        # Handle recurring events
        rrule_prop = component.get("RRULE")
        if rrule_prop:
            rrule_str = rrule_prop.to_ical().decode()
            rule = rrulestr(rrule_str, dtstart=dtstart)

            for occ_start in rule.between(start_window, end_window, inc=True):
                # Skip excluded dates
                if occ_start.date() in exdates:
                    continue
                occ_end = occ_start + duration - timedelta(microseconds=1)
                events.append(
                    {
                        "summary": summary,
                        "color": colors,
                        "start": occ_start,
                        "end": occ_end,
                    }
                )
        else:
            # Non-recurring event, include if inside window
            if dtstart < end_window and dtend > start_window:
                events.append(
                    {
                        "summary": summary,
                        "color": colors,
                        "start": dtstart,
                        "end": dtend,
                    }
                )

    return events, start_window, end_window


def fetch_simple_events(ical_url: str):
    """
    Fetch events (including recurring ones) from an iCal URL and return
    a list of dicts containing 'summary' and 'day' (ISO date string).
    """
    response = requests.get(ical_url)
    response.raise_for_status()
    cal = Calendar.from_ical(response.content)

    now = datetime.now(timezone.utc)
    start_window = now - timedelta(days=7)  # 1 week before now
    end_window = now + timedelta(weeks=12)  # 3 months ahead

    events = []

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("SUMMARY"))
        dtstart = component.get("DTSTART").dt
        dtend = component.get("DTEND")
        dtend = dtend.dt if dtend else None

        # Normalize datetime values
        def normalize(dt):
            if not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
            elif dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt

        dtstart = normalize(dtstart)
        if dtend:
            dtend = normalize(dtend)

        # Handle recurrence
        rrule_prop = component.get("RRULE")
        if rrule_prop:
            rrule_str = rrule_prop.to_ical().decode()
            rule = rrulestr(rrule_str, dtstart=dtstart)

            # Generate all occurrences within window
            for occ_start in rule.between(start_window, end_window, inc=True):
                events.append({"summary": summary, "day": occ_start.date().isoformat()})
        else:
            # Single (non-recurring) event in window
            if start_window <= dtstart <= end_window:
                events.append({"summary": summary, "day": dtstart.date().isoformat()})

    return events


@app.post("/save-todo")
async def save_todo(content: str = Form(...)):
    # Save textarea content to todo file
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    return RedirectResponse("/", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Read tasks line by line
    tasks = []
    if TODO_FILE.exists():
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            tasks = [line.strip() for line in f if line.strip()]

    events, start_window, _ = fetch_upcoming_events(ICAL_URL)

    days = []
    for i in range(28):  # 4 weeks × 7 days
        day = start_window + timedelta(days=i)

        day_events = []
        for e in events:
            start = e["start"]
            end = e["end"]

            # Detect all-day event (exactly 24h, starting at midnight)
            is_all_day = (
                start.time() == datetime.min.time()
                and end.time() == datetime.min.time()
                and (end - start) == timedelta(days=1)
            )

            if is_all_day:
                if day.date() == start.date():
                    day_events.append(e)
            else:
                if start.date() <= day.date() <= end.date():
                    day_events.append(e)

        days.append({"date": day, "events": day_events})

    weeks = [days[i : i + 7] for i in range(0, 28, 7)]

    events = fetch_simple_events(ICAL_URL2)

    now = datetime.now(timezone.utc)
    # Find next Wednesday (0=Mon, 2=Wed)
    days_ahead = (2 - now.weekday() + 7) % 7
    next_wednesday = now + timedelta(days=days_ahead)

    # Generate next 4 Wednesdays
    upcoming_wednesdays = [next_wednesday + timedelta(weeks=i) for i in range(8)]

    days = []
    for day in upcoming_wednesdays:
        # Convert both sides to date objects for safe comparison
        day_date = day.date()
        day_events = [
            e for e in events if datetime.fromisoformat(e["day"]).date() == day_date
        ]

        days.append({"date": day, "events": day_events})

    # Split into 2×2 structure for the table
    wednesdays = [days[:4], days[4:]]
    print(wednesdays)

    return templates.TemplateResponse(
        "html/index.html",
        {
            "request": request,
            "weeks": weeks,
            "tasks": tasks,
            "wednesdays": wednesdays,
            "current_date": date.today(),
        },
    )


@app.get("/edit")
async def edit_todo(request: Request):
    tasks = []
    if TODO_FILE.exists():
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            tasks = [line.strip() for line in f if line.strip()]

    return templates.TemplateResponse(
        "html/edit.html",
        {
            "request": request,
            "tasks": tasks,
        },
    )


@app.post("/auth/login")
def auth_login(resp: Response, data: LoginRequestForm):
    if data.username != "cha" or data.password != "cha":
        logger.error("Authentication failed.")
        return False
    logger.success("Successful authentication")
    resp.set_cookie(key="username", value=data.username)
    return True


@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        "html/login.html",
        {"request": request},
    )


@app.get("/auth/logout")
@authenticated
async def logout(resp: Response, request: Request):
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("username")
    resp.delete_cookie("workspace")
    return resp


@app.get("/current_user")
async def get_current_user(request: Request):
    username = request.cookies.get("username")
    print(username)
    return username
    return {"username": username}
