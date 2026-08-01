from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base

DB_PATH = Path(__file__).parent / "data" / "doctor.db"
DB_PATH.parent.mkdir(exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Doctor CRUD ────────────────────────────────────────────────────

def get_doctor(db: Session, doctor_id: int):
    from models import Doctor
    return db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()


def get_all_doctors(db: Session):
    from models import Doctor
    return db.query(Doctor).filter(Doctor.is_active == True).all()


def get_default_doctor(db: Session):
    """Return the first active doctor (used when no doctor_id is provided)."""
    from models import Doctor
    return db.query(Doctor).filter(Doctor.is_active == True).order_by(Doctor.id).first()


def init_doctors():
    """Seed the database with 3 Italian doctors if the table is empty."""
    from models import Doctor
    db = SessionLocal()
    try:
        existing = db.query(Doctor).count()
        if existing > 0:
            return  # already seeded

        doctors_data = [
            {
                "name": "Dr. Mario Rossi",
                "title": "Medico Chirurgo",
                "specializations": "Medicina Generale, Cardiologia",
                "address": "Via Roma 1, 00100 Roma",
                "phone": "+39 06 12345678",
                "email": "mario.rossi@studiomedico.it",
                "work_hours": "Lun-Ven: 09:00-13:00, 15:00-19:00",
                "languages": "Italiano, English",
                "description": (
                    "Il Dott. Mario Rossi è un medico chirurgo con oltre 20 anni di esperienza "
                    "nel campo della medicina generale e della cardiologia. Laureato con lode "
                    "presso l'Università La Sapienza di Roma, ha conseguito specializzazioni in "
                    "Cardiologia e Medicina Interna. Il suo approccio è centrato sul paziente: "
                    "ascolto, diagnosi precisa e cura personalizzata."
                ),
                "latitude": 41.9028,
                "longitude": 12.4964,
                "years_experience": 20,
                "patients_count": 5000,
                "photo_url": None,
                "color_theme": "#2563eb",
                "is_active": True,
            },
            {
                "name": "Dr.ssa Laura Bianchi",
                "title": "Medico Chirurgo - Dermatologa",
                "specializations": "Dermatologia, Pediatria, Medicina Estetica",
                "address": "Via Garibaldi 45, 00100 Roma",
                "phone": "+39 06 98765432",
                "email": "laura.bianchi@studiomedico.it",
                "work_hours": "Lun-Mer-Ven: 09:00-17:00, Mar-Gio: 14:00-19:00",
                "languages": "Italiano, English, Français",
                "description": (
                    "La Dott.ssa Laura Bianchi è una dermatologa e pediatra con 15 anni di "
                    "esperienza. Laureata all'Università di Milano, si è specializzata in "
                    "Dermatologia Clinica e Pediatrica presso l'Ospedale San Raffaele. Offre "
                    "un'attenzione particolare ai pazienti più piccoli e alle problematiche "
                    "cutanee di ogni tipo, dalla dermatologia generale alla medicina estetica "
                    "non invasiva."
                ),
                "latitude": 41.8950,
                "longitude": 12.4780,
                "years_experience": 15,
                "patients_count": 3800,
                "photo_url": None,
                "color_theme": "#ec4899",
                "is_active": True,
            },
            {
                "name": "Dr. Giovanni Verdi",
                "title": "Medico Chirurgo - Ortopedico",
                "specializations": "Ortopedia, Fisioterapia, Traumatologia",
                "address": "Via Nazionale 120, 00100 Roma",
                "phone": "+39 06 55667788",
                "email": "giovanni.verdi@studiomedico.it",
                "work_hours": "Lun-Ven: 08:00-12:00, 14:00-18:00",
                "languages": "Italiano, English, Español",
                "description": (
                    "Il Dott. Giovanni Verdi è un ortopedico e traumatologo con 18 anni di "
                    "esperienza, specializzato nella diagnosi e trattamento di patologie "
                    "muscolo-scheletriche. Laureato all'Università di Bologna, ha perfezionato "
                    "le sue competenze in chirurgia ortopedica mini-invasiva e riabilitazione "
                    "post-operatoria. Collabora con i migliori centri di fisioterapia per "
                    "garantire un percorso di cura completo."
                ),
                "latitude": 41.9010,
                "longitude": 12.5030,
                "years_experience": 18,
                "patients_count": 4200,
                "photo_url": None,
                "color_theme": "#059669",
                "is_active": True,
            },
        ]

        for data in doctors_data:
            doctor = Doctor(**data)
            db.add(doctor)

        db.commit()
        print("✅ Seeded 3 doctors into the database.")
    finally:
        db.close()


# ─── Appointment CRUD ───────────────────────────────────────────────

def create_appointment(db: Session, data: dict):
    from models import Appointment
    appt = Appointment(**data)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


def get_appointment(db: Session, appointment_id: int):
    from models import Appointment
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


# ─── ContactMessage CRUD ────────────────────────────────────────────

def create_contact_message(db: Session, data: dict):
    from models import ContactMessage
    msg = ContactMessage(**data)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ─── ChatLog CRUD ───────────────────────────────────────────────────

def create_chat_log(db: Session, session_id: str, question: str, answer: str):
    from models import ChatLog
    log = ChatLog(session_id=session_id, question=question, answer=answer)
    db.add(log)
    db.commit()
