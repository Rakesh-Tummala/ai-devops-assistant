🤖 AI DevOps Assistant

Debugging logs and writing YAML files shouldn't take up half your day. AI DevOps Assistant is a Groq-powered tool that automates the "chore" parts of DevOps — deciphering error logs, scaffolding CI/CD pipelines and Dockerfiles, answering DevOps questions, and deploying a project straight to Render with one upload.

🔗 Live App
- Frontend: https://ai-devops-assistant-theta.vercel.app
- Backend API: https://ai-devops-assistant-backend-mvrs.onrender.com

Access is gated by a shared access key (see [Access Key & Security](#-access-key--security) below) — you'll need it to use the live app or your own deployment.

📑 Contents
- [Features](#-features)
- [How to Use](#-how-to-use)
- [Architecture](#-architecture)
- [Workflow — how a request actually flows](#-workflow--how-a-request-actually-flows)
- [Access Key & Security](#-access-key--security)
- [Tech Stack](#-tech-stack)
- [Running It Yourself](#-running-it-yourself)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Known Limitations](#-known-limitations)
- [Roadmap](#-roadmap)

🧠 Features

🚀 One-Click Deploy
Upload a project ZIP. The assistant detects the project type, generates a Dockerfile, pushes it to a GitHub repo, and deploys it to Render — with live status, a progress bar, and logs in the UI.

🔍 Smart Log Analysis
Upload a log file and get an AI-generated breakdown of the errors, their likely root cause, and concrete remediation suggestions.

💬 DevOps Expert Chat
Ask questions about Docker, CI/CD, cloud deployment, Kubernetes, and general troubleshooting — get instant AI-powered answers.

⚙️ CI/CD Generator
Pick a project type and a target platform (GitHub Actions, GitLab CI, CircleCI) and get a ready-to-use pipeline config.

🐳 Dockerfile Generator
Tell the AI your project type (optionally upload a manifest like `package.json`/`requirements.txt`) and get a production-ready Dockerfile.

📖 How to Use

1. **Unlock the app** — on first load you'll be asked for an access key. Enter it once; the browser remembers it (stored in `localStorage`) until it's cleared or rejected.
2. **Deploy tab** — choose a `.zip` of a project, click **Deploy**. Watch the progress bar move through Generate Dockerfile → Push to GitHub → Deploy to Render → Complete. When it finishes, a live URL appears. Only one deploy can run at a time; starting a second while one is in progress is rejected until the first finishes.
3. **Log Analyzer tab** — choose a log file, click **Analyze**. The result panel shows the AI's breakdown; use **Copy** or **Download** to save it.
4. **DevOps Chat tab** — type a question, click **Send**. Each message is answered independently (no running conversation history).
5. **CI/CD Generator tab** — pick a project type and target platform, optionally attach a manifest file for extra context, click **Generate**.
6. **Dockerfile Generator tab** — pick a project type, optionally attach a manifest file, click **Generate**.

Uploads are capped (50MB for zips, 2MB for text/log files fed to the AI) and zip contents are validated before extraction — oversized or malformed uploads are rejected with a clear error instead of being processed.

🏗 Architecture

```
Browser (React, Vercel)
   │  every request carries an X-App-Key header
   ▼
FastAPI backend (Render)
   ├─ Groq API              → chat / log analysis / CI-CD gen / Dockerfile gen
   ├─ GitHub REST + git CLI → pushes generated project to a scratch repo
   └─ Render REST API       → creates a web service from that repo, polls until live
```

The frontend never talks to Groq, GitHub, or Render directly — every call goes through the backend, which is the only place real credentials live. The browser is treated as untrusted; the access key is the one thing it's allowed to hold.

The deploy target repo (`ai-devops-deploy` by default) is a separate, disposable scratch repo — **not** this project's own source repo. Every deploy force-pushes over it, so nothing of value should ever be kept there.

🔄 Workflow — how a request actually flows

**1. Every request passes through the access-key gate first.** The backend checks the `X-App-Key` header with `secrets.compare_digest` (constant-time comparison, so a wrong guess can't be timed to leak information) against `APP_ACCESS_KEY`. Everything except the health check (`GET /`) requires this. A missing/wrong key gets a `401`; the frontend clears its stored key and re-prompts instead of failing silently.

**2. From there, requests split into two very different paths:**

- **The four AI features** (Chat, Log Analyzer, CI/CD Generator, Dockerfile Generator) are simple and stateless — each one builds a system + user prompt and calls Groq's `chat.completions.create`, then returns the text. No shared state between requests.
- **Deploy** is a multi-stage pipeline that runs in a background thread so the upload request itself returns immediately:

  1. **Upload zip** — filename is checked against `^[A-Za-z0-9_.-]+\.zip$` (rejects path separators and anything but a plain `.zip`), and the file is streamed to disk with a running 50MB cap.
  2. **Extract safely** — every zip entry's target path is resolved and checked against the destination folder before writing; entries with `../`, absolute paths, or drive letters are rejected outright (blocks zip-slip). Entry count and total uncompressed size are capped too (blocks zip bombs).
  3. **Detect project type** — reads `package.json` (checks for `next`/`vite`/`react` keywords) or `requirements.txt`/`main.py`/`app.py` (checks for `fastapi`/`flask`) to classify the project as `nextjs` / `vite` / `react` / `node` / `fastapi` / `flask` / `python` / `unknown`.
  4. **Generate Dockerfile** — a fixed template per detected type (Node/Vite/React → `node:lts-alpine` + `serve`, Python → `python:3.11-slim` + `uvicorn`, unknown → `nginx:alpine` static). Deliberately deterministic, not AI-generated — this step has to be fast and reliable on every single deploy.
  5. **Push to GitHub** — `git init`/`add`/`commit`/`push --force` against the scratch repo. The GitHub token is never embedded in the remote URL; it's passed per-command via `git -c http.extraheader="Authorization: Basic <base64>"`, so it never persists into `.git/config` or gets echoed into an error message.
  6. **Create Render service** — calls Render's REST API to spin up a new web service from that repo, then polls `GET /v1/services/{id}` every 5 seconds (up to 10 minutes) until `serviceDetails.url` is populated.
  7. **Live URL returned** — surfaced through `/deployment-status/`, which the frontend polls every 2 seconds and reflects in the progress bar and logs.

  A `threading.Lock` means only one deploy can run at a time — a second upload while one's in progress gets a clean `409` instead of racing on the same working directory and global state. And every upload starts by wiping the `projects/` working directory clean first, so leftover state from a previous deploy (including a stray `.git`) can never bleed into the next one.

  If any step raises, the pipeline jumps straight to `status: "Error"` with a scrubbed (credential-redacted) message — it doesn't continue partway or silently swallow the failure.

🔑 Access Key & Security

Every backend route except the health check (`GET /`) requires a shared secret sent as the `X-App-Key` header. The frontend's unlock screen handles this for you — enter the key once and it's attached to every request automatically.

This was added deliberately after the backend was made public: **originally there was no authentication at all**, meaning anyone who found the URL could trigger a real deploy using this project's own GitHub token and Render account, or burn through its Groq quota. Beyond the access key, a few other security decisions worth knowing:

- **Zip-slip protection** — extraction validates every member's resolved path before writing, instead of a bare `zipfile.extractall()`.
- **No credentials in the git remote URL** — the GitHub token is passed per-command via an HTTP auth header, never embedded in the URL or written to `.git/config`.
- **CORS is an explicit allowlist** (`ALLOWED_ORIGINS`), not `allow_origins=["*"]`.
- **Upload limits** — filename pattern validation, a 50MB cap on zips, a 2MB cap on text fed to the AI.
- **Concurrency lock** — one deploy at a time; no racing on shared state or the working directory.

🛠️ Tech Stack

Frontend
- React (JavaScript)
- Tailwind CSS
- Vite
- Axios
- Deployed on Vercel

Backend
- FastAPI (Python)
- Groq API (`llama-3.3-70b-versatile` by default)
- Git CLI automation + GitHub REST API + Render REST API for the deploy flow
- Deployed on Render

⚙️ Running It Yourself

1. Clone the repository
```
git clone https://github.com/Rakesh-Tummala/ai-devops-assistant.git
cd ai-devops-assistant
```

2. Backend setup
```
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/` (see `.env.example` at the repo root for the full list with descriptions):
```
GROQ_API_KEY=your_groq_api_key
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_token
GITHUB_REPO_NAME=ai-devops-deploy
RENDER_API_KEY=your_render_api_key
ALLOWED_ORIGINS=http://localhost:5173
APP_ACCESS_KEY=pick_a_long_random_string
```

Run the backend:
```
uvicorn main:app --reload
```

3. Frontend setup
```
cd frontend
npm install
npm run dev
```

Open in browser: http://localhost:5173 — note that `frontend/src/App.jsx` has `API_URL` hardcoded to the deployed Render backend; point it at `http://127.0.0.1:8000` if you want the local frontend talking to a local backend instead.

📡 API Endpoints
All routes below require the `X-App-Key` header (see [Access Key & Security](#-access-key--security)) except `GET /`.

| Endpoint              | Method | Description                        |
| ---------------------- | ------ | ----------------------------------- |
| `/`                    | GET    | Health check (no key required)      |
| `/upload-zip/`         | POST   | Upload a project ZIP and deploy it  |
| `/deployment-status/`  | GET    | Poll current deployment status/logs |
| `/reset-deployment/`   | POST   | Reset deployment state              |
| `/detect-project/`     | GET    | Detect the current project's type   |
| `/analyze-log/`        | POST   | Log Analyzer                        |
| `/chat/`               | POST   | DevOps Chat                         |
| `/generate-cicd/`      | POST   | CI/CD Generator                     |
| `/generate-docker/`    | POST   | Dockerfile Generator                |

📁 Project Structure
```
ai-devops-assistant/
├── backend/
│   ├── main.py                     # routes, access-key gate, deploy orchestration
│   ├── deploy_render.py            # Render REST API calls
│   ├── deployment/
│   │   └── github_push.py          # git init/add/commit/push, credential handling
│   ├── utils/
│   │   ├── zip_handler.py          # safe zip extraction (zip-slip / zip-bomb protection)
│   │   └── project_detector.py     # project-type detection
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       └── App.jsx                 # all 5 tabs, unlock screen, API calls
│
├── .env.example
└── README.md
```

⚠️ Known Limitations

- **Global in-memory deployment state** (`deployment_status`/`deployment_logs` as module-level variables) only works because the backend runs as a single process/worker on Render. It wouldn't survive multiple workers or a process restart mid-deploy.
- **Shared access key, not per-user auth.** Keeps random visitors out; doesn't give distinct accounts or permissions to multiple real users.
- **Single, fixed scratch repo** for all deploys — not isolated per user or per deploy. Concurrent users would overwrite each other's in-flight deploys.
- **No automated test suite.** Correctness has been verified through live, manual, end-to-end runs against real GitHub/Render/Groq rather than CI tests.

🎯 Roadmap
- Support additional deploy targets beyond Render (Railway, Fly.io, AWS)
- Kubernetes manifest generator
- Terraform generator
- Multi-user accounts / per-user deploy targets

👨‍💻 Author

Rakesh Tummala
B.Tech CSE | Cloud + AI Enthusiast
