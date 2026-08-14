🤖 AI DevOps Assistant

Debugging logs and writing YAML files shouldn't take up half your day. AI DevOps Assistant is a Groq-powered tool that automates the "chore" parts of DevOps — deciphering error logs, scaffolding CI/CD pipelines and Dockerfiles, answering DevOps questions, and deploying a project straight to Render with one upload.

🔗 Live App
- Frontend: https://ai-devops-assistant-theta.vercel.app
- Backend API: https://ai-devops-assistant-backend-mvrs.onrender.com

Access is gated by a shared access key (see [Access Key](#-access-key) below) — you'll need it to use the live app or your own deployment.

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

🔑 Access Key
Every backend route except the health check (`GET /`) requires a shared secret sent as the `X-App-Key` header. The frontend's unlock screen handles this for you — enter the key once and it's attached to every request automatically. If the key is ever wrong or revoked, the app clears it and re-prompts instead of failing silently.

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
All routes below require the `X-App-Key` header (see [Access Key](#-access-key)) except `GET /`.

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
│   ├── main.py
│   ├── deploy_render.py
│   ├── deployment/
│   │   └── github_push.py
│   ├── utils/
│   │   ├── zip_handler.py
│   │   └── project_detector.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       └── App.jsx
│
├── .env.example
└── README.md
```

🎯 Roadmap
- Support additional deploy targets beyond Render (Railway, Fly.io, AWS)
- Kubernetes manifest generator
- Terraform generator
- Multi-user accounts / per-user deploy targets

👨‍💻 Author

Rakesh Tummala
B.Tech CSE | Cloud + AI Enthusiast
