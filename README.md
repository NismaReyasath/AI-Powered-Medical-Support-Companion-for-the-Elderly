# AI-Powered-Medical-Support-Companion-for-the-Elderly

# MEDORA — Starter scaffold (Flutter + FastAPI)

This repo contains a starter Flutter mobile app (medora_app) and a lightweight FastAPI backend (backend).
The backend uses SQLite by default for quick local testing. Use Docker Compose to add Postgres if you prefer.

Quick start (backend + flutter)
- Backend (local, venv):
  cd backend
  python -m venv .venv
  .venv\Scripts\activate   # Windows PowerShell
  source .venv/bin/activate # macOS / Linux
  pip install -r requirements.txt
  uvicorn app.main:app --reload --port 8000

- Flutter:
  cd medora_app
  flutter pub get
  flutter run
