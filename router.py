import uuid
import json
from datetime import date
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from config import settings
from database import get_db, create_appointment, get_appointment, create_contact_message, create_chat_log
from chat_engine import DoctorChat

router = APIRouter()

_doctor_chat = DoctorChat(
    api_key=settings.OPENAI_API_KEY,
    model=settings.CHAT_MODEL,
)

SERVICES_DATA = [
    {"id": 1, "name": "Visita Generale", "price": 50, "duration": 30, "description": "Visita medica generale di routine con controllo dei parametri vitali."},
    {"id": 2, "name": "Visita Specialistica", "price": 80, "duration": 45, "description": "Visita specialistica approfondita con diagnosi e piano terapeutico."},
    {"id": 3, "name": "Checkup Completo", "price": 120, "duration": 60, "description": "Pacchetto checkup completo con analisi e screening generale."},
    {"id": 4, "name": "Visita Cardiologica", "price": 100, "duration": 45, "description": "Valutazione cardiologica con elettrocardiogramma."},
    {"id": 5, "name": "Certificato Medico", "price": 35, "duration": 15, "description": "Certificato medico per attività sportiva o lavorativa."},
    {"id": 6, "name": "Consulenza Online", "price": 40, "duration": 20, "description": "Consulenza medica tramite videochiamata."},
]

AVAILABLE_TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:00", "18:30",
]

# ── API Routes (for React SPA) ──────────────────────────────────────

@router.get("/api/home")
async def api_home():
    return {
        "doctor_name": settings.DOCTOR_NAME,
        "doctor_title": settings.DOCTOR_TITLE,
        "specializations": settings.specializations_list,
        "description": settings.DESCRIPTION,
        "years_experience": settings.YEARS_EXPERIENCE,
        "patients_count": settings.PATIENTS_COUNT,
        "address": settings.ADDRESS,
        "phone": settings.PHONE,
        "email": settings.EMAIL,
        "work_hours": settings.WORK_HOURS,
        "site_title": settings.SITE_TITLE,
    }


@router.get("/api/about")
async def api_about():
    return {
        "doctor_name": settings.DOCTOR_NAME,
        "doctor_title": settings.DOCTOR_TITLE,
        "description": settings.DESCRIPTION,
        "languages": settings.LANGUAGES,
        "years_experience": settings.YEARS_EXPERIENCE,
        "patients_count": settings.PATIENTS_COUNT,
        "specializations": settings.specializations_list,
        "phone": settings.PHONE,
        "email": settings.EMAIL,
        "credentials": [
            {"year": 2000, "title": "Laurea in Medicina e Chirurgia", "institution": "Università La Sapienza di Roma"},
            {"year": 2005, "title": "Specializzazione in Cardiologia", "institution": "Università La Sapienza di Roma"},
            {"year": 2008, "title": "Specializzazione in Medicina Interna", "institution": "Università Cattolica del Sacro Cuore"},
            {"year": 2012, "title": "Master in Ecocardiografia", "institution": "Università di Bologna"},
            {"year": 2018, "title": "Fellowship in Cardiologia Interventistica", "institution": "University of Oxford"},
        ],
        "timeline": [
            {"year": 2010, "event": "Apertura dello studio medico a Roma"},
            {"year": 2013, "event": "Riconoscimento come miglior specialista dell'anno"},
            {"year": 2015, "event": "Pubblicazione su riviste internazionali di cardiologia"},
            {"year": 2019, "event": "Oltre 5000 pazienti trattati con successo"},
            {"year": 2023, "event": "Introduzione della telemedicina e consulenze online"},
        ],
    }


@router.get("/api/services")
async def api_services():
    return {"services": SERVICES_DATA}


@router.post("/api/booking")
async def api_booking(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    try:
        appt_date = date.fromisoformat(body["date"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Data non valida")

    appt = create_appointment(db, {
        "patient_name": body["name"],
        "patient_email": body["email"],
        "patient_phone": body["phone"],
        "appointment_date": appt_date,
        "appointment_time": body["time"],
        "service": body.get("service", ""),
        "reason": body.get("notes", ""),
        "status": "confirmed",
    })
    return {"success": True, "appointment_id": appt.id, "date": body["date"], "time": body["time"]}


@router.post("/api/contact")
async def api_contact(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    create_contact_message(db, {
        "name": body["name"],
        "email": body["email"],
        "subject": body.get("subject", ""),
        "message": body["message"],
    })
    return {"success": True}


@router.post("/api/chat")
async def api_chat(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    question = body.get("message", "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())

    if not question:
        return {"answer": "Per favore inserisca una domanda.", "session_id": session_id}

    doctor_info = settings.to_doctor_info_dict()
    answer = await _doctor_chat.answer(question, session_id, doctor_info)

    create_chat_log(db, session_id, question, answer)
    return {"answer": answer, "session_id": session_id}


@router.get("/api/booking/check")
async def api_booking_check(date: str, db: Session = Depends(get_db)):
    return {"available_times": AVAILABLE_TIMES}


# ── SPA Catch-All (serve React index.html for all non-API, non-static routes) ──

INDEX_PATH = Path("static/index.html")


@router.get("/{full_path:path}")
async def spa_catch_all(full_path: str, request: Request):
    # Don't interfere with /api/* or /static/* routes
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not found")

    index_file = Path("static/index.html")
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    # Fallback simple page if React hasn't been built yet
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>{settings.SITE_TITLE}</title></head>
    <body>
      <div style="text-align:center;padding:100px 20px;font-family:sans-serif;">
        <h1>🏗️ {settings.SITE_TITLE}</h1>
        <p>Il sito è in manutenzione. Torneremo tra poco.</p>
      </div>
    </body>
    </html>
    """)
