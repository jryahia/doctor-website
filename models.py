from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=False)
    specializations = Column(Text, nullable=False)  # comma-separated
    address = Column(String(300), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(200), nullable=False)
    work_hours = Column(String(200), nullable=False)
    languages = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    years_experience = Column(Integer, default=0)
    patients_count = Column(Integer, default=0)
    photo_url = Column(String(500), nullable=True)
    color_theme = Column(String(20), default="#2563eb")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="doctor")

    @property
    def specializations_list(self) -> list[str]:
        return [s.strip() for s in self.specializations.split(",")]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "specializations": self.specializations_list,
            "description": self.description,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "work_hours": self.work_hours,
            "languages": self.languages,
            "years_experience": self.years_experience,
            "patients_count": self.patients_count,
            "photo_url": self.photo_url,
            "color_theme": self.color_theme,
            "is_active": self.is_active,
        }

    def to_doctor_info_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "specializations": self.specializations_list,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "work_hours": self.work_hours,
            "languages": self.languages,
            "description": self.description,
            "years_experience": self.years_experience,
            "patients_count": self.patients_count,
        }


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    patient_name = Column(String(200), nullable=False)
    patient_email = Column(String(200), nullable=False)
    patient_phone = Column(String(50), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(10), nullable=False)
    service = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    doctor = relationship("Doctor", back_populates="appointments")


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
