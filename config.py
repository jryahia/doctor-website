from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DOCTOR_NAME: str = "Dr. Mario Rossi"
    DOCTOR_TITLE: str = "Medico Chirurgo"
    SPECIALIZATIONS: str = "Medicina Generale, Cardiologia"
    ADDRESS: str = "Via Roma 1, 00100 Roma"
    PHONE: str = "+39 06 12345678"
    EMAIL: str = "info@dottore.it"
    WORK_HOURS: str = "Lun-Ven: 09:00-13:00, 15:00-19:00"
    LANGUAGES: str = "Italiano, English"
    DESCRIPTION: str = (
        "Il Dott. Mario Rossi è un medico chirurgo con oltre 20 anni di esperienza "
        "nel campo della medicina generale e della cardiologia. Si è laureato con lode "
        "presso l'Università La Sapienza di Roma e ha conseguito specializzazioni in "
        "Cardiologia e Medicina Interna. Nel corso della sua carriera ha trattato migliaia "
        "di pazienti con professionalità, dedizione e umanità. Il suo approccio è centrato "
        "sul paziente: ascolto, diagnosi precisa e cura personalizzata."
    )
    LATITUDE: float = 41.9028
    LONGITUDE: float = 12.4964
    OPENAI_API_KEY: Optional[str] = None
    CHAT_MODEL: str = "gpt-4o-mini"
    SITE_TITLE: str = "Studio Medico Dott. Rossi"
    YEARS_EXPERIENCE: int = 20
    PATIENTS_COUNT: int = 5000
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def specializations_list(self) -> list[str]:
        return [s.strip() for s in self.SPECIALIZATIONS.split(",")]

    def to_doctor_info_dict(self) -> dict:
        return {
            "name": self.DOCTOR_NAME,
            "title": self.DOCTOR_TITLE,
            "specializations": self.specializations_list,
            "address": self.ADDRESS,
            "phone": self.PHONE,
            "email": self.EMAIL,
            "work_hours": self.WORK_HOURS,
            "languages": self.LANGUAGES,
            "description": self.DESCRIPTION,
            "years_experience": self.YEARS_EXPERIENCE,
            "patients_count": self.PATIENTS_COUNT,
            "site_title": self.SITE_TITLE,
        }


settings = Settings()
