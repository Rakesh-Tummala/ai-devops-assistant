🤖 AI DevOps Assistant

Debugging logs and writing YAML files shouldn't take up half your day. AI DevOps Assistant is a Groq-powered tool that automates the "chore" parts of DevOps — deciphering error logs, scaffolding CI/CD pipelines and Dockerfiles, answering DevOps questions, and deploying a project straight to Render with one upload.

🧠 What Can It Do?

🚀 One-Click Deploy
Upload a project ZIP. The assistant detects the project type, generates a Dockerfile, pushes it to GitHub, and deploys it to Render — with live status and logs in the UI.

🔍 Smart Log Analysis
Upload a log file and get an AI-generated breakdown of the errors, their likely root cause, and concrete remediation suggestions.

💬 DevOps Expert Chat
Ask questions about Docker, CI/CD, cloud deployment, Kubernetes, and general troubleshooting — get instant AI-powered answers.

⚙️ CI/CD Generator
Pick a project type and a target platform (GitHub Actions, GitLab CI, CircleCI) and get a ready-to-use pipeline config.

🐳 Dockerfile Generator
Tell the AI your project type (optionally upload a manifest like `package.json`/`requirements.txt`) and get a production-ready Dockerfile.

🛠️ Tech Stack

Frontend
- React (JavaScript)
- Tailwind CSS
- Vite
- Axios

Backend
- FastAPI (Python)
- Groq API (`llama-3.3-70b-versatile` by default)
- GitPython-free git CLI automation + GitHub + Render APIs for the deploy flow

⚙️ Installation

1. Clone the repository
```
git clone https://github.com/yourusername/AI-DevOps-Assistant.git
cd AI-DevOps-Assistant
```

2. Backend setup
```
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/` (see `.env.example` at the repo root for the full list):
```
GROQ_API_KEY=your_groq_api_key
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=your_github_token
RENDER_API_KEY=your_render_api_key
ALLOWED_ORIGINS=http://localhost:5173
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

Open in browser: http://localhost:5173

📡 API Endpoints

| Endpoint              | Method | Description                        |
| ---------------------- | ------ | ----------------------------------- |
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
