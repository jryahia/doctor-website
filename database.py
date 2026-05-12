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


# --- Appointment CRUD ---

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


# --- ContactMessage CRUD ---

def create_contact_message(db: Session, data: dict):
    from models import ContactMessage
    msg = ContactMessage(**data)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# --- ChatLog CRUD ---

def create_chat_log(db: Session, session_id: str, question: str, answer: str):
    from models import ChatLog
    log = ChatLog(session_id=session_id, question=question, answer=answer)
    db.add(log)
    db.commit()
