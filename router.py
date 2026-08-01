import uuid
import json
from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from config import settings
from database import get_db, create_appointment, get_appointment, create_contact_message, create_chat_log
from database import get_doctor, get_all_doctors, get_default_doctor
from chat_engine import DoctorChat

router = APIRouter()

_doctor_chat = DoctorChat(
    api_key=settings.DEEPSEEK_API_KEY,
    model=settings.DEEPSEEK_MODEL,
)

# ── Per-doctor services ─────────────────────────────────────────────

DOCTOR_SERVICES = {
    1: [
        {"id": 1, "name": "Visita Generale", "price": 50, "duration": 30, "description": "Visita medica generale di routine con controllo dei parametri vitali."},
        {"id": 2, "name": "Visita Specialistica", "price": 80, "duration": 45, "description": "Visita specialistica approfondita con diagnosi e piano terapeutico."},
        {"id": 3, "name": "Checkup Completo", "price": 120, "duration": 60, "description": "Pacchetto checkup completo con analisi e screening generale."},
        {"id": 4, "name": "Visita Cardiologica", "price": 100, "duration": 45, "description": "Valutazione cardiologica con elettrocardiogramma."},
        {"id": 5, "name": "Certificato Medico", "price": 35, "duration": 15, "description": "Certificato medico per attivita sportiva o lavorativa."},
        {"id": 6, "name": "Consulenza Online", "price": 40, "duration": 20, "description": "Consulenza medica tramite videochiamata."},
    ],
    2: [
        {"id": 1, "name": "Visita Dermatologica", "price": 70, "duration": 40, "description": "Visita dermatologica completa con mappatura dei nei."},
        {"id": 2, "name": "Checkup Pediatrico", "price": 60, "duration": 35, "description": "Controllo pediatrico completo per bambini e adolescenti."},
        {"id": 3, "name": "Medicina Estetica", "price": 150, "duration": 45, "description": "Trattamenti di medicina estetica non invasiva."},
        {"id": 4, "name": "Patch Test Allergici", "price": 90, "duration": 50, "description": "Test allergologici per dermatiti da contatto."},
        {"id": 5, "name": "Consulenza Online", "price": 40, "duration": 20, "description": "Consulenza dermatologica tramite videochiamata."},
    ],
    3: [
        {"id": 1, "name": "Visita Ortopedica", "price": 70, "duration": 40, "description": "Valutazione ortopedica completa con esame obiettivo."},
        {"id": 2, "name": "Seduta di Fisioterapia", "price": 45, "duration": 50, "description": "Seduta di fisioterapia manuale e strumentale."},
        {"id": 3, "name": "Traumatologia", "price": 80, "duration": 45, "description": "Diagnosi e trattamento di traumi e infortuni."},
        {"id": 4, "name": "Terapia Riabilitativa", "price": 55, "duration": 60, "description": "Percorso riabilitativo personalizzato post-operatorio."},
        {"id": 5, "name": "Certificato Sportivo", "price": 40, "duration": 20, "description": "Certificato medico per attivita sportiva agonistica."},
        {"id": 6, "name": "Consulenza Online", "price": 40, "duration": 20, "description": "Consulenza ortopedica tramite videochiamata."},
    ],
}

DEFAULT_SERVICES = DOCTOR_SERVICES[1]

AVAILABLE_TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:00", "18:30",
]

# ── Doctor profiles with credentials/timeline ───────────────────────

DOCTOR_ABOUT_DATA = {
    1: {
        "credentials": [
            {"year": 2000, "title": "Laurea in Medicina e Chirurgia", "institution": "Universita La Sapienza di Roma"},
            {"year": 2005, "title": "Specializzazione in Cardiologia", "institution": "Universita La Sapienza di Roma"},
            {"year": 2008, "title": "Specializzazione in Medicina Interna", "institution": "Universita Cattolica del Sacro Cuore"},
            {"year": 2012, "title": "Master in Ecocardiografia", "institution": "Universita di Bologna"},
            {"year": 2018, "title": "Fellowship in Cardiologia Interventistica", "institution": "University of Oxford"},
        ],
        "timeline": [
            {"year": 2010, "event": "Apertura dello studio medico a Roma"},
            {"year": 2013, "event": "Riconoscimento come miglior specialista dell'anno"},
            {"year": 2015, "event": "Pubblicazione su riviste internazionali di cardiologia"},
            {"year": 2019, "event": "Oltre 5000 pazienti trattati con successo"},
            {"year": 2023, "event": "Introduzione della telemedicina e consulenze online"},
        ],
    },
    2: {
        "credentials": [
            {"year": 2005, "title": "Laurea in Medicina e Chirurgia", "institution": "Universita degli Studi di Milano"},
            {"year": 2009, "title": "Specializzazione in Dermatologia", "institution": "Ospedale San Raffaele di Milano"},
            {"year": 2012, "title": "Specializzazione in Pediatria", "institution": "Ospedale Bambino Gesu di Roma"},
            {"year": 2015, "title": "Master in Medicina Estetica", "institution": "Universita di Pavia"},
        ],
        "timeline": [
            {"year": 2012, "event": "Inizio attivita presso l'Ospedale Pediatrico di Roma"},
            {"year": 2015, "event": "Apertura del proprio studio di dermatologia"},
            {"year": 2018, "event": "Pubblicazione di ricerche sulla dermatite atopica infantile"},
            {"year": 2021, "event": "Oltre 3000 piccoli pazienti trattati"},
            {"year": 2024, "event": "Certificazione in dermatoscopia digitale"},
        ],
    },
    3: {
        "credentials": [
            {"year": 2002, "title": "Laurea in Medicina e Chirurgia", "institution": "Universita di Bologna"},
            {"year": 2007, "title": "Specializzazione in Ortopedia e Traumatologia", "institution": "Universita di Bologna"},
            {"year": 2010, "title": "Master in Chirurgia Artroscopica", "institution": "Universita di Modena e Reggio Emilia"},
            {"year": 2014, "title": "Fellowship in Chirurgia Protestica", "institution": "Charite - Universitatsmedizin Berlin"},
        ],
        "timeline": [
            {"year": 2008, "event": "Inizio attivita presso l'Ospedale Rizzoli di Bologna"},
            {"year": 2013, "event": "Trasferimento a Roma e apertura studio ortopedico"},
            {"year": 2016, "event": "Certificazione in chirurgia mini-invasiva"},
            {"year": 2020, "event": "Oltre 4000 pazienti trattati"},
            {"year": 2024, "event": "Introduzione della riabilitazione digitale assistita"},
        ],
    },
}

# ── Helper to get doctor from query param ───────────────────────────

def _resolve_doctor(db: Session, doctor_id: int | None = None):
    """Return (doctor_instance, doctor_dict). Falls back to default doctor."""
    if doctor_id is not None:
        doctor = get_doctor(db, doctor_id)
        if doctor is not None:
            return doctor, doctor.to_dict()
    doctor = get_default_doctor(db)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Nessun medico disponibile")
    return doctor, doctor.to_dict()


# ── API Routes (for React SPA) ──────────────────────────────────────


@router.get("/api/doctors")
async def api_doctors(db: Session = Depends(get_db)):
    """Return list of all active doctors (for the doctor selector)."""
    doctors = get_all_doctors(db)
    return {
        "doctors": [
            {
                "id": d.id,
                "name": d.name,
                "title": d.title,
                "specializations": d.specializations_list,
                "photo_url": d.photo_url,
                "color_theme": d.color_theme,
                "years_experience": d.years_experience,
                "patients_count": d.patients_count,
            }
            for d in doctors
        ]
    }


@router.get("/api/home")
async def api_home(doctor_id: int | None = Query(None), db: Session = Depends(get_db)):
    doctor, info = _resolve_doctor(db, doctor_id)
    return {
        "doctor_name": info["name"],
        "doctor_title": info["title"],
        "specializations": info["specializations"],
        "description": info["description"],
        "years_experience": info["years_experience"],
        "patients_count": info["patients_count"],
        "address": info["address"],
        "phone": info["phone"],
        "email": info["email"],
        "work_hours": info["work_hours"],
        "site_title": settings.SITE_TITLE,
    }


@router.get("/api/about")
async def api_about(doctor_id: int | None = Query(None), db: Session = Depends(get_db)):
    doctor, info = _resolve_doctor(db, doctor_id)
    about_data = DOCTOR_ABOUT_DATA.get(doctor.id, DOCTOR_ABOUT_DATA.get(1, {"credentials": [], "timeline": []}))
    return {
        "doctor_name": info["name"],
        "doctor_title": info["title"],
        "description": info["description"],
        "languages": info["languages"],
        "years_experience": info["years_experience"],
        "patients_count": info["patients_count"],
        "specializations": info["specializations"],
        "phone": info["phone"],
        "email": info["email"],
        **about_data,
    }


@router.get("/api/services")
async def api_services(doctor_id: int | None = Query(None), db: Session = Depends(get_db)):
    doctor, info = _resolve_doctor(db, doctor_id)
    services = DOCTOR_SERVICES.get(doctor.id, DEFAULT_SERVICES)
    return {"services": services}


@router.post("/api/booking")
async def api_booking(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    try:
        appt_date = date.fromisoformat(body["date"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Data non valida")

    appt = create_appointment(db, {
        "doctor_id": body.get("doctor_id"),
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
    doctor_id = body.get("doctor_id")

    if not question:
        return {"answer": "Per favore inserisca una domanda.", "session_id": session_id}

    doctor, info = _resolve_doctor(db, doctor_id)
    doctor_info = doctor.to_doctor_info_dict()

    answer = await _doctor_chat.answer(question, session_id, doctor_info)

    q_count = _doctor_chat._session_questions.get(session_id, 1)
    remaining = max(0, _doctor_chat.MAX_QUESTIONS - q_count)

    create_chat_log(db, session_id, question, answer)
    return {
        "answer": answer,
        "session_id": session_id,
        "remaining_questions": remaining,
        "max_questions": _doctor_chat.MAX_QUESTIONS,
    }


@router.get("/api/booking/check")
async def api_booking_check(date: str, db: Session = Depends(get_db)):
    return {"available_times": AVAILABLE_TIMES}


# ── Doctor selection page ───────────────────────────────────────────

SELECT_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Seleziona il tuo medico - {SITE_TITLE}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Space Grotesk', sans-serif;
      background: #0A0F0A;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      overflow-x: hidden;
      position: relative;
    }
    ::selection { background: rgba(45,125,70,0.3); color: #fff; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0A0F0A; }
    ::-webkit-scrollbar-thumb { background: #2D7D46; border-radius: 3px; }
    #three-bg {
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      z-index: 0;
      pointer-events: none;
    }
    .bg-glow {
      position: fixed;
      border-radius: 50%;
      filter: blur(80px);
      opacity: 0.15;
      pointer-events: none;
      z-index: 0;
    }
    .bg-glow-1 {
      width: 500px; height: 500px;
      background: #2D7D46;
      top: -10%; left: -10%;
      animation: floatGlow 8s ease-in-out infinite;
    }
    .bg-glow-2 {
      width: 400px; height: 400px;
      background: #E8803A;
      bottom: -15%; right: -10%;
      animation: floatGlow 10s ease-in-out infinite 2s;
    }
    .bg-glow-3 {
      width: 300px; height: 300px;
      background: #1A6B3A;
      bottom: 30%; right: 40%;
      animation: floatGlow 12s ease-in-out infinite 4s;
    }
    @keyframes floatGlow {
      0%, 100% { transform: translate(0, 0) scale(1); }
      33% { transform: translate(30px, -30px) scale(1.1); }
      66% { transform: translate(-20px, 20px) scale(0.9); }
    }

    .container {
      max-width: 1100px;
      width: 100%;
      text-align: center;
      position: relative;
      z-index: 1;
    }

    /* ── Logo / Brand ── */
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 2rem;
      animation: fadeUp 0.8s ease-out;
    }
    .brand-cross {
      width: 28px; height: 28px;
      position: relative;
      display: inline-block;
    }
    .brand-cross::before, .brand-cross::after {
      content: '';
      position: absolute;
      background: linear-gradient(135deg, #2D7D46, #E8803A);
      border-radius: 3px;
    }
    .brand-cross::before { width: 3px; height: 100%; left: 50%; transform: translateX(-50%); }
    .brand-cross::after { width: 100%; height: 3px; top: 50%; transform: translateY(-50%); }
    .brand-label {
      font-family: 'Playfair Display', serif;
      font-size: 0.9rem;
      color: rgba(240,245,240,0.4);
      letter-spacing: 3px;
      text-transform: uppercase;
    }

    /* ── Header ── */
    .header {
      margin-bottom: 3.5rem;
      animation: fadeUp 0.8s ease-out 0.15s both;
    }
    .header h1 {
      font-family: 'Playfair Display', serif;
      font-size: clamp(2rem, 4vw, 3rem);
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 1rem;
    }
    .header h1 .gradient-text {
      background: linear-gradient(135deg, #2D7D46 0%, #4CAF50 40%, #E8803A 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .header h1 .gradient-text-orange {
      background: linear-gradient(135deg, #E8803A 0%, #f0a050 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .subtitle {
      font-size: 1.05rem;
      color: rgba(240,245,240,0.5);
      font-weight: 300;
      max-width: 500px;
      margin: 0 auto;
      line-height: 1.6;
    }
    .subtitle-ornament {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-top: 16px;
    }
    .subtitle-ornament::before, .subtitle-ornament::after {
      content: '';
      width: 40px; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(45,125,70,0.4));
    }
    .subtitle-ornament::after {
      background: linear-gradient(90deg, rgba(232,128,58,0.4), transparent);
    }
    .subtitle-ornament span { color: rgba(240,245,240,0.2); font-size: 0.5rem; }

    /* ── Grid ── */
    .doctors-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 28px;
      margin-top: 0.5rem;
      animation: fadeUp 0.8s ease-out 0.3s both;
    }

    /* ── Card ── */
    .doctor-card {
      background: rgba(18,24,18,0.5);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 24px;
      padding: 36px 28px 28px;
      cursor: pointer;
      transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
      text-align: left;
      position: relative;
      overflow: hidden;
      animation: cardFloat 0.8s ease-out backwards;
    }
    .doctor-card:nth-child(1) { animation-delay: 0.1s; }
    .doctor-card:nth-child(2) { animation-delay: 0.25s; }
    .doctor-card:nth-child(3) { animation-delay: 0.4s; }

    @keyframes cardFloat {
      from { opacity: 0; transform: translateY(50px) scale(0.97); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .doctor-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #2D7D46, #E8803A, transparent);
      opacity: 0;
      transition: opacity 0.5s ease;
    }
    .doctor-card::after {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: 24px;
      padding: 1px;
      background: linear-gradient(135deg, rgba(45,125,70,0.1), transparent 40%, transparent 60%, rgba(232,128,58,0.1));
      -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
      -webkit-mask-composite: xor;
      mask-composite: exclude;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.5s ease;
    }
    .doctor-card:hover::after { opacity: 1; }

    .doctor-card:hover {
      transform: translateY(-10px) scale(1.01);
      border-color: rgba(45,125,70,0.2);
      box-shadow:
        0 24px 80px rgba(0,0,0,0.4),
        0 0 40px rgba(45,125,70,0.08);
    }
    .doctor-card:hover::before { opacity: 1; }

    /* Card shimmer hover effect */
    .doctor-card .card-shimmer {
      position: absolute;
      top: 0; left: -100%;
      width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.02), transparent);
      transition: left 0.8s ease;
      pointer-events: none;
    }
    .doctor-card:hover .card-shimmer { left: 100%; }

    /* ── Avatar ── */
    .avatar-wrapper {
      width: 100px; height: 100px;
      border-radius: 50%;
      padding: 3px;
      background: linear-gradient(135deg, #2D7D46, #E8803A);
      margin-bottom: 20px;
      position: relative;
      transition: transform 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    }
    .doctor-card:hover .avatar-wrapper {
      transform: scale(1.05);
    }
    .avatar-wrapper::before {
      content: '';
      position: absolute;
      inset: -4px;
      border-radius: 50%;
      background: linear-gradient(135deg, #2D7D46, transparent, #E8803A);
      opacity: 0;
      animation: avatarPulse 3s ease-in-out infinite;
    }
    .doctor-card:hover .avatar-wrapper::before { opacity: 0.3; }
    @keyframes avatarPulse {
      0%, 100% { transform: scale(1); opacity: 0.3; }
      50% { transform: scale(1.08); opacity: 0.15; }
    }
    .avatar {
      width: 100%; height: 100%;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Playfair Display', serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: white;
      position: relative;
      z-index: 1;
      transition: all 0.5s ease;
    }
    .doctor-card:hover .avatar { filter: brightness(1.15); }

    /* ── Card Content ── */
    .doctor-card h3 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #F0F5F0;
      margin-bottom: 3px;
      transition: color 0.3s ease;
    }
    .doctor-card:hover h3 {
      background: linear-gradient(135deg, #F0F5F0, #2D7D46);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .doctor-card .title {
      color: rgba(240,245,240,0.4);
      font-size: 0.85rem;
      font-weight: 400;
      margin-bottom: 16px;
    }
    .specs {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 18px;
    }
    .spec-tag {
      background: rgba(45,125,70,0.1);
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 0.75rem;
      color: #4CAF50;
      border: 1px solid rgba(45,125,70,0.15);
      transition: all 0.3s ease;
      letter-spacing: 0.3px;
    }
    .doctor-card:hover .spec-tag {
      background: rgba(45,125,70,0.18);
      border-color: rgba(45,125,70,0.3);
    }
    .spec-tag.orange {
      background: rgba(232,128,58,0.08);
      color: #E8803A;
      border-color: rgba(232,128,58,0.15);
    }
    .doctor-card:hover .spec-tag.orange {
      background: rgba(232,128,58,0.15);
      border-color: rgba(232,128,58,0.3);
    }

    /* ── Stats / Divider ── */
    .card-divider {
      width: 100%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
      margin-bottom: 16px;
    }
    .stats {
      display: flex;
      gap: 20px;
      font-size: 0.82rem;
      color: rgba(240,245,240,0.4);
      font-weight: 400;
    }
    .stats span {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .stats .stat-icon { font-size: 0.9rem; }
    .stats .stat-value {
      color: rgba(240,245,240,0.7);
      font-weight: 500;
    }

    /* ── Loading ── */
    .loading {
      grid-column: 1 / -1;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 20px;
      padding: 80px;
      color: rgba(240,245,240,0.4);
      font-size: 0.9rem;
      font-weight: 300;
    }
    .loading-dots {
      display: flex;
      gap: 8px;
    }
    .loading-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: #2D7D46;
      animation: dotBounce 1.2s ease-in-out infinite;
    }
    .loading-dot:nth-child(2) { animation-delay: 0.15s; background: #4CAF50; }
    .loading-dot:nth-child(3) { animation-delay: 0.3s; background: #E8803A; }
    @keyframes dotBounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
      40% { transform: scale(1); opacity: 1; }
    }

    /* ── Footer ── */
    .footer {
      margin-top: 4rem;
      font-size: 0.8rem;
      color: rgba(240,245,240,0.15);
      animation: fadeUp 0.8s ease-out 0.6s both;
    }
    .footer a {
      color: rgba(45,125,70,0.5);
      text-decoration: none;
      transition: color 0.3s ease;
    }
    .footer a:hover { color: #2D7D46; }

    /* ── Floating decorative lines ── */
    .deco-line {
      position: fixed;
      z-index: 0;
      pointer-events: none;
      opacity: 0.03;
    }
    .deco-line-1 {
      top: 0; left: 60px;
      width: 1px; height: 100%;
      background: linear-gradient(to bottom, transparent, #2D7D46, transparent);
      animation: decoPulse 4s ease-in-out infinite;
    }
    .deco-line-2 {
      top: 0; right: 80px;
      width: 1px; height: 100%;
      background: linear-gradient(to bottom, transparent, #E8803A, transparent);
      animation: decoPulse 5s ease-in-out infinite 1s;
    }
    @keyframes decoPulse {
      0%, 100% { opacity: 0.03; }
      50% { opacity: 0.08; }
    }

    /* ── Animations ── */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(30px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* ── Responsive ── */
    @media (max-width: 640px) {
      body { padding: 16px; align-items: flex-start; padding-top: 60px; }
      .container { padding: 0; }
      .header h1 { font-size: 1.6rem; }
      .subtitle { font-size: 0.9rem; }
      .doctors-grid { grid-template-columns: 1fr; gap: 20px; }
      .doctor-card { padding: 28px 20px 20px; }
      .avatar-wrapper { width: 80px; height: 80px; }
      .avatar { font-size: 1.8rem; }
      .stats { flex-direction: column; gap: 8px; }
      .deco-line { display: none; }
    }
    @media (min-width: 641px) and (max-width: 1024px) {
      .doctors-grid { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <div id="three-bg"></div>
  <div class="bg-glow bg-glow-1"></div>
  <div class="bg-glow bg-glow-2"></div>
  <div class="bg-glow bg-glow-3"></div>
  <div class="deco-line deco-line-1"></div>
  <div class="deco-line deco-line-2"></div>

  <div class="container">
    <div class="brand">
      <span class="brand-cross"></span>
      <span class="brand-label">Studio Medico</span>
    </div>

    <div class="header">
      <h1>
        Scegli il tuo<br>
        <span class="gradient-text">medico di fiducia</span>
      </h1>
      <p class="subtitle">
        Ogni professionista del nostro team &egrave; pronto ad offrirti cure
        personalizzate e attenzione dedicata.
      </p>
      <div class="subtitle-ornament"><span>&#10015;</span></div>
    </div>

    <div class="doctors-grid" id="doctors-grid">
      <div class="loading">
        <div class="loading-dots">
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
          <div class="loading-dot"></div>
        </div>
        <span>Caricamento medici...</span>
      </div>
    </div>

    <div class="footer">
      &copy; <span id="year"></span> {SITE_TITLE} &mdash; Tutti i diritti riservati
    </div>
  </div>

  <script>
    // ── Three.js Ambient Background ──────────────────────────────────
    (function initThree() {
      var container = document.getElementById('three-bg');
      var scene = new THREE.Scene();
      var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
      var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);

      var count = 150;
      var positions = new Float32Array(count * 3);
      var sizes = new Float32Array(count);
      var colors = new Float32Array(count * 3);

      var green = new THREE.Color('#2D7D46');
      var orange = new THREE.Color('#E8803A');
      var teal = new THREE.Color('#1A6B3A');

      for (var i = 0; i < count; i++) {
        positions[i*3] = (Math.random() - 0.5) * 30;
        positions[i*3+1] = (Math.random() - 0.5) * 30;
        positions[i*3+2] = (Math.random() - 0.5) * 20;
        sizes[i] = Math.random() * 6 + 1.5;
        var mix = Math.random();
        var c = green.clone().lerp(orange, mix);
        colors[i*3] = c.r;
        colors[i*3+1] = c.g;
        colors[i*3+2] = c.b;
      }

      var particlesGeo = new THREE.BufferGeometry();
      particlesGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      particlesGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
      particlesGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

      var textureCanvas = document.createElement('canvas');
      textureCanvas.width = 64; textureCanvas.height = 64;
      var ctx = textureCanvas.getContext('2d');
      var gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
      gradient.addColorStop(0, 'rgba(255,255,255,1)');
      gradient.addColorStop(0.2, 'rgba(255,255,255,0.7)');
      gradient.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 64, 64);
      var texture = new THREE.CanvasTexture(textureCanvas);

      var material = new THREE.PointsMaterial({
        size: 0.2,
        map: texture,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        transparent: true,
        vertexColors: true,
        opacity: 0.6,
      });

      var particles = new THREE.Points(particlesGeo, material);
      scene.add(particles);

      camera.position.z = 12;

      var mouseX = 0, mouseY = 0, targetX = 0, targetY = 0;
      document.addEventListener('mousemove', function(e) {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
      });

      function animate() {
        requestAnimationFrame(animate);
        targetX += (mouseX * 0.03 - targetX) * 0.02;
        targetY += (mouseY * 0.03 - targetY) * 0.02;
        particles.rotation.y += 0.0006;
        particles.rotation.x = targetY * 0.1;
        particles.rotation.y += targetX * 0.02;
        renderer.render(scene, camera);
      }
      animate();

      window.addEventListener('resize', function() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      });
    })();

    // ── Set year ──────────────────────────────────────────────────
    document.getElementById('year').textContent = new Date().getFullYear();

    // ── Fetch and render doctors ─────────────────────────────────
    fetch('/api/doctors')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var grid = document.getElementById('doctors-grid');
        grid.innerHTML = '';
        data.doctors.forEach(function(doc, idx) {
          var initials = doc.name.split(' ').map(function(w) { return w[0]; }).join('').slice(0, 2);
          var card = document.createElement('div');
          card.className = 'doctor-card';
          card.style.animationDelay = (0.1 + idx * 0.15) + 's';

          var specsHtml = '';
          doc.specializations.forEach(function(s, si) {
            var cls = si % 2 === 0 ? 'spec-tag' : 'spec-tag orange';
            specsHtml += '<span class="' + cls + '">' + s + '</span>';
          });

          card.innerHTML =
            '<div class="card-shimmer"></div>' +
            '<div class="avatar-wrapper"><div class="avatar" style="background:' + doc.color_theme + ';">' + initials + '</div></div>' +
            '<h3>' + doc.name + '</h3>' +
            '<div class="title">' + doc.title + '</div>' +
            '<div class="specs">' + specsHtml + '</div>' +
            '<div class="card-divider"></div>' +
            '<div class="stats">' +
              '<span><span class="stat-icon">&#9733;</span> <span class="stat-value">' + doc.years_experience + '</span> anni di esperienza</span>' +
              '<span><span class="stat-icon">&#128100;</span> <span class="stat-value">' + doc.patients_count.toLocaleString() + '</span> pazienti</span>' +
            '</div>';

          card.addEventListener('click', function() {
            // Animate out before redirect
            card.style.transform = 'scale(0.95)';
            card.style.opacity = '0.5';
            card.style.transition = 'all 0.3s ease';
            setTimeout(function() {
              sessionStorage.setItem('doctor_id', doc.id);
              window.location.href = '/?doctor=' + doc.id;
            }, 200);
          });

          // Entrance stagger
          grid.appendChild(card);
        });
      })
      .catch(function() {
        document.getElementById('doctors-grid').innerHTML =
          '<div style="color:rgba(240,245,240,0.4);padding:60px;font-weight:300;">Impossibile caricare i medici. Riprova pi&ugrave; tardi.</div>';
      });
  </script>
</body>
</html>"""


@router.get("/select")
async def doctor_select(request: Request):
    return HTMLResponse(
        SELECT_PAGE_HTML.replace("{SITE_TITLE}", settings.SITE_TITLE)
    )


# ── SPA Catch-All ──
# Note: static/index.html is fully self-contained — it reads the doctor_id from the
# URL / sessionStorage and loads /static/chat-widget.js on its own, so no server-side
# script injection is needed here.


@router.get("/{full_path:path}")
async def spa_catch_all(full_path: str, request: Request):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not found")
    index_file = Path("static/index.html")
    if index_file.exists():
        html = index_file.read_text(encoding="utf-8")
        return HTMLResponse(content=html)
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>{settings.SITE_TITLE}</title></head>
    <body>
      <div style="text-align:center;padding:100px 20px;font-family:sans-serif;">
        <h1>&#x1f3d7;&#xfe0f; {settings.SITE_TITLE}</h1>
        <p>Il sito e in manutenzione. Torneremo tra poco.</p>
      </div>
    </body>
    </html>
    """)
