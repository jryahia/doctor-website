import uuid
from typing import Optional


class DoctorChat:
    def __init__(self, api_key: Optional[str], model: str = "gpt-4o-mini"):
        self.model = model
        self._api_key = api_key
        self._client = None

    async def _get_client(self):
        if self._client is not None:
            return self._client
        if self._api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError:
                pass
            except TypeError:
                # Version compatibility fallback
                try:
                    import httpx
                    from openai import AsyncOpenAI
                    self._client = AsyncOpenAI(api_key=self._api_key, http_client=httpx.AsyncClient())
                except Exception:
                    pass
        return self._client

    def _build_system_prompt(self, doctor_info: dict) -> str:
        specs = ", ".join(doctor_info.get("specializations", []))
        return f"""Sei un assistente virtuale per lo studio medico di {doctor_info['name']}.
Rispondi SOLO basandoti sulle informazioni fornite qui sotto. Se non conosci la risposta,
dì gentilmente che non hai queste informazioni e invita l'utente a contattare lo studio
telefonicamente o via email. Non inventare mai informazioni mediche.

INFORMAZIONI STUDIO:
- Nome: {doctor_info['name']}, {doctor_info['title']}
- Specializzazioni: {specs}
- Indirizzo: {doctor_info['address']}
- Telefono: {doctor_info['phone']}
- Email: {doctor_info['email']}
- Orari: {doctor_info['work_hours']}
- Lingue parlate: {doctor_info['languages']}
- Esperienza: {doctor_info['years_experience']} anni
- Biografia: {doctor_info['description']}

Regole IMPORTANTI:
- Rispondi sempre in italiano (o nella lingua in cui ti viene posta la domanda, se è una delle lingue supportate)
- Sii professionale ma amichevole e rassicurante
- NON dare mai consigli medici specifici o diagnosi
- Se chiedono informazioni non presenti nei dati forniti, reindirizza educatamente a telefono o email
- Per prenotare un appuntamento, suggerisci di usare il modulo di prenotazione del sito
- Usa un tono caldo, empatico e professionale
- Risposte concise ma complete"""

    async def answer(self, question: str, session_id: str, doctor_info: dict) -> str:
        if not self.client:
            return self._fallback_answer(question, doctor_info)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(doctor_info)},
                    {"role": "user", "content": question},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return self._fallback_answer(question, doctor_info)

    def _fallback_answer(self, question: str, doctor_info: dict) -> str:
        q = question.lower()
        if any(w in q for w in ["orari", "aperto", "aperta", "quando", "ore"]):
            return f"Gli orari dello studio sono: {doctor_info['work_hours']}. Per ulteriori informazioni chiamare il {doctor_info['phone']}."
        if any(w in q for w in ["dove", "indirizzo", "come arrivare", "sede"]):
            return f"Lo studio si trova in {doctor_info['address']}. Per indicazioni più precise non esitate a contattarci al {doctor_info['phone']}."
        if any(w in q for w in ["telefon", "contatt", "chiamare"]):
            return f"Puoi contattarci al numero {doctor_info['phone']} oppure via email a {doctor_info['email']}."
        if any(w in q for w in ["prenot", "appuntament", "visita"]):
            return "Per prenotare un appuntamento puoi usare il modulo di prenotazione online oppure chiamarci al " + doctor_info["phone"] + "."
        if any(w in q for w in ["specializ", "servizi", "cure", "tratta"]):
            specs = ", ".join(doctor_info.get("specializations", []))
            return f"Il {doctor_info['name']} si occupa di: {specs}. Per maggiori dettagli sui servizi visitate la pagina Servizi."
        return (
            f"Grazie per la sua domanda. Per informazioni dettagliate la invitiamo a contattare "
            f"lo studio al {doctor_info['phone']} oppure via email a {doctor_info['email']}. "
            f"Saremo felici di rispondere a tutte le sue domande."
        )
