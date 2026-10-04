# Doctor Website

**Website for a medical practice with appointment booking, contact management and an AI chat assistant for patient questions.**

![Python](https://img.shields.io/badge/Python-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![FastAPI](https://img.shields.io/badge/FastAPI-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![SQLite](https://img.shields.io/badge/SQLite-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![OpenAI](https://img.shields.io/badge/OpenAI-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![HTML](https://img.shields.io/badge/HTML-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![CSS](https://img.shields.io/badge/CSS-161b22?style=for-the-badge&labelColor=161b22&color=161b22)

```mermaid
flowchart LR
    S0["Patient visits site"]
    S1["Booking + contact forms"]
    S2["FastAPI backend + SQLite"]
    S3["AI chat assistant"]
    S4["Appointments for the practice"]
    S0 --> S1 --> S2 --> S3 --> S4
```

## Problem it solves

Small practices lose time on the phone booking appointments and answering the same questions. This site lets patients book online and get answers from a chat assistant.

Professional website for a medical studio with appointment booking, contact management, and AI assistant chatbot.

## Features
- Doctor profile with bio, credentials, specializations
- Service catalog with detailed descriptions
- Online appointment booking with date/time selection
- Contact form with message management
- AI chat assistant — answers ONLY from doctor's information
- Mobile responsive design
- Configurable for any doctor, any city

## Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env   # customize doctor info
python main.py
# Open http://localhost:8000
```

## Configuration
All doctor information is configured via `.env` file:
- Name, title, specializations
- Address, phone, email, work hours
- Bio/description
- Map coordinates
- OpenAI API key for chat

## Tech Stack
FastAPI · SQLite · Jinja2 · OpenAI API · HTML/CSS/JS
