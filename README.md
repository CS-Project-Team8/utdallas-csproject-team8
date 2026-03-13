# Project Setup Guide (Backend + Frontend + DB)

This repo contains:
- `backend/` = **FastAPI** (Python)
- `frontend/` = **React + TypeScript + Tailwind + shadcn/ui**
- `docker-compose.yml` = **PostgreSQL**

Follow the steps in order.

---

## 0) Prerequisites (install these first)

You need:
- **Git**
- **Python 3.11+**
- **Node.js 20+** (includes npm)
- **Docker Desktop** (or Docker Engine + Docker Compose)

Verify installs:

```bash
git --version
python --version
node --version
npm --version
docker --version
docker compose version

```

---

## 1) Clone the repo + open the project
```bash

git clone <YOUR_REPO_URL>
cd utdallas-team8-CSProject
```
---

## 2) Create your local environment file
- Copy the example .env file:
```bash
# macOS/Linux
cp .env.example .env

# Windows PowerShell
copy .env.example .env
```
Fill in values in .env (at minimum):

- DATABASE_URL (depends on your DB port)

- YOUTUBE_API_KEY

- LLM Config

---
## 3) Start Postgres SQL
```bash
docker compose up -d
docker ps # verify that it is running
```
---
## 4) Backend Setup (FastAPI)

- Go into the backend folder
```bash

cd backend
```
- Create virtual environment
```bash

python -m venv .venv
```
- Activate virtual environment
```bash

.\.venv\Scripts\Activate.ps1 # Powershell
source .venv/bin/activate # MacOS
```
- Install python dependencies
```bash

python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```
- Run backend tests to check setup
```bash

python -m pytest -q
```
- Run backend server
```bash

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Test it in your browser
- - http://127.0.0.1:8000/health → should return {"status":"ok"}
- -http://127.0.0.1:8000/docs → Swagger UI
- **Keep this terminal running.**

---
## 5) Frontend Setup (React + Typescript + Tailwind + shadcn/ui)
**Open a new terminal at the repo root, then**
```bash

cd frontend
npm install
npm run dev
```
Frontend will print a URL like:
http://localhost:5173

Open it in your browser

---

## 6) Typical Dev Workflow
**Start Everything:**
- DB
```bash

docker compose up -d
```
- Backend (navigate to /backend, make sure venv is activated)
```bash

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Frontend (navigate to /frontend)
```bash
npm install 
npm run dev
```
- To Stop everything:
  - Backend: Ctrl + C
  - Frontend: Ctrl + C
  - DB: 'docker compose down'
