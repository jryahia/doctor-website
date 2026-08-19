from typing import Optional


class DoctorChat:
    def __init__(self, api_key: Optional[str], model: str = "deepseek-chat"):
        self.model = model
        self._api_key = api_key
        self._client = None
        # Track question count per session: {session_id: count}
        self._session_questions: dict[str, int] = {}
        self.MAX_QUESTIONS = 6

    async def _get_client(self):
        if self._client is not None:
            return self._client
        if self._api_key:
            try:
                from openai import AsyncOpenAI
                # Use DeepSeek's OpenAI-compatible endpoint
                self._client = AsyncOpenAI(
                    api_key=self._api_key,
                    base_url="https://api.deepseek.com"
                )
            except ImportError:
                pass
            except TypeError:
                try:
                    import httpx
                    from openai import AsyncOpenAI
                    self._client = AsyncOpenAI(
                        api_key=self._api_key,
                        base_url="https://api.deepseek.com",
                        http_client=httpx.AsyncClient()
                    )
                except Exception:
                    pass
        return self._client

    def _build_system_prompt(self, doctor_info: dict) -> str:
        specs = ", ".join(doctor_info.get("specializations", []))
        return f"""Sei l'assistente virtuale ufficiale di STUDIO MEDICO, un ambulatorio medico a Roma.
Il tuo nome è "Supporto Studio Medico" e il tuo unico scopo è rispondere a domande sullo studio medico.

INFORMAZIONI DISPONIBILI (usa SOLO queste per rispondere):
- Medico: {doctor_info['name']}, {doctor_info['title']}
- Specializzazioni: {specs}
- Indirizzo: {doctor_info['address']}
- Telefono: {doctor_info['phone']}
- Email: {doctor_info['email']}
- Orari: {doctor_info['work_hours']}
- Lingue: {doctor_info['languages']}
- Esperienza: {doctor_info['years_experience']} anni
- Biografia: {doctor_info['description']}

REGOLE STRICT (rispettale SEMPRE):
1. Rispondi SOLO in italiano, in modo educato e professionale.
2. Puoi parlare ESCLUSIVAMENTE di: orari, indirizzo, servizi offerti, specializzazioni del medico, contatti (telefono/email), prenotazioni, lingue parlate, biografia del medico.
3. Se l'utente chiede qualcosa FUORI da questi argomenti (diagnosi mediche, cure specifiche, consigli sanitari, opinioni personali, informazioni non presenti qui), rispondi gentilmente: "Mi dispiace, posso fornire solo informazioni sullo studio medico e sui suoi servizi. Per domande specifiche, La invito a contattare lo studio al {doctor_info['phone']} o via email a {doctor_info['email']}."
4. NON dare MAI diagnosi mediche, consigli terapeutici, o informazioni sanitarie specifiche.
5. Per prenotazioni, invita l'utente a usare il modulo di prenotazione online sul sito.
6. Risposte concise (max 3 frasi). Professionale, caldo, rassicurante.
7. PRESENTATI SOLO al primo messaggio della conversazione. Nelle risposte successive NON ripetere la presentazione, vai diretto al punto.
8. Non ti inventare MAI informazioni che non sono nei dati qui sopra."""

    async def answer(self, question: str, session_id: str, doctor_info: dict) -> str:
        # Track session questions
        count = self._session_questions.get(session_id, 0)
        self._session_questions[session_id] = count + 1

        # Block if over limit
        if count >= self.MAX_QUESTIONS:
            return (
                f"Ha raggiunto il limite massimo di {self.MAX_QUESTIONS} domande per questa conversazione. "
                f"Se ha bisogno di ulteriore assistenza, La invitiamo a contattare lo studio "
                f"al {doctor_info['phone']} o via email a {doctor_info['email']}. "
                "Grazie per averci contattato! "
            )

        client = await self._get_client()
        if not client:
            return self._fallback_answer(question, doctor_info)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(doctor_info)},
                    {"role": "user", "content": question},
                ],
                max_tokens=400,
                temperature=0.2,
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
        # Default fallback — polite redirect
        return (
            f"Grazie per la sua domanda. Per informazioni dettagliate, La invitiamo a contattare "
            f"lo studio al {doctor_info['phone']} oppure via email a {doctor_info['email']}. "
            f"Saremo felici di rispondere a tutte le sue domande."
        )
