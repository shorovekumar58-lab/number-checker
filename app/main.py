from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from .db import Base, engine, SessionLocal
from .models import NumberEntry
from .utils import process_numbers, normalize_number

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_FOLDER = os.path.join(PROJECT_DIR, "data")
TEXT_BACKUP_FILE = os.path.join(DATA_FOLDER, "saved_numbers.txt")
SHARED_NUMBER_FILE = os.path.join(DATA_FOLDER, "shared_number.txt")

os.makedirs(DATA_FOLDER, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def read_shared_number():
    if os.path.exists(SHARED_NUMBER_FILE):
        with open(SHARED_NUMBER_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def write_shared_number(number: str):
    with open(SHARED_NUMBER_FILE, "w", encoding="utf-8") as f:
        f.write(number.strip())


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    total_db = db.query(NumberEntry).count()
    shared_number = read_shared_number()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "numbers": [],
            "count": 0,
            "total_pasted": 0,
            "duplicate_count": 0,
            "total_db": total_db,
            "shared_number": shared_number,
            "message": ""
        }
    )


@app.post("/process", response_class=HTMLResponse)
def process(request: Request, text: str = Form(...), db: Session = Depends(get_db)):
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    total_pasted = len(raw_lines)

    pasted_numbers = process_numbers(text)

    existing_rows = db.query(NumberEntry.normalized_number).filter(
        NumberEntry.normalized_number.in_(pasted_numbers)
    ).all()

    existing_numbers = {row[0] for row in existing_rows}
    new_numbers = [num for num in pasted_numbers if num not in existing_numbers]

    duplicate_count = len(pasted_numbers) - len(new_numbers)

    for num in new_numbers:
        db.add(NumberEntry(normalized_number=num, submitted_by="user"))

    db.commit()

    if new_numbers:
        with open(TEXT_BACKUP_FILE, "a", encoding="utf-8") as f:
            for num in new_numbers:
                f.write(num + "\n")

    if total_pasted == 0:
        message = "কিছু paste করা হয়নি।"
    elif len(new_numbers) == 0:
        message = "নতুন কোনো number save হয়নি। সব number duplicate বা invalid হতে পারে।"
    else:
        message = f"{len(new_numbers)} টি নতুন number save হয়েছে।"

    total_db = db.query(NumberEntry).count()
    shared_number = read_shared_number()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "numbers": new_numbers,
            "count": len(new_numbers),
            "total_pasted": total_pasted,
            "duplicate_count": duplicate_count,
            "total_db": total_db,
            "shared_number": shared_number,
            "message": message
        }
    )


@app.post("/set-shared-number")
def set_shared_number(shared_input: str = Form(...)):
    number = normalize_number(shared_input)

    if number:
        write_shared_number(number)
    else:
        write_shared_number(shared_input.strip())

    return RedirectResponse(url="/", status_code=303)


@app.post("/clear-shared-number")
def clear_shared_number():
    write_shared_number("")
    return RedirectResponse(url="/", status_code=303)
