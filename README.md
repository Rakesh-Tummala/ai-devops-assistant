🤖 AI DevOps Assistant

Debugging logs and writing YAML files shouldn't take up half your day. AI DevOps Assistant is a smart, Gemini-powered tool designed to automate the "chore" parts of DevOps — from deciphering cryptic error logs to scaffolding production-ready CI/CD pipelines.


🧠 What Can It Do?

🔍 Smart Log Analysis
Stop squinting at stack traces. Upload your log files, and the assistant will:
Identify the issue
Suggest fixes
Provide actionable solutions

💬 DevOps Expert Chat
Ask questions like:
Kubernetes ingress setup
Docker issues
CI/CD problems
Cloud deployment
Get instant AI-powered answers.

⚙️ Pipeline Generator
Generate CI/CD pipelines for:
GitHub Actions
GitLab CI
Jenkins
No need to search documentation.

🐳 Dockerfile Generator
Tell the AI your project type:
Python
Node
Java
Go
Get a production-ready Dockerfile instantly.

✨ Extra Features
Copy to Clipboard
Download YAML
Loading Spinner
Clean UI
Fast Responses


🛠️ Tech Stack
Frontend
React
TypeScript
Tailwind CSS
Vite

Backend
FastAPI
Python
Google Gemini API

Development Tools
Node.js
Git
VS Code

⚙️ Installation
1. Clone Repository
git clone https://github.com/yourusername/AI-DevOps-Assistant.git
cd AI-DevOps-Assistant

Backend Setup
cd backend
pip install -r requirements.txt

Create .env
GEMINI_API_KEY=your_api_key_here

Run backend
uvicorn main:app --reload

Frontend Setup
npm install
npm run dev

Open in browser:
http://localhost:5173

📡 API Endpoints
| Endpoint            | Description          |
| ------------------- | -------------------- |
| `/analyze-log/`     | Log Analyzer         |
| `/chat/`            | DevOps Chat          |
| `/generate-cicd/`   | CI/CD Generator      |
| `/generate-docker/` | Dockerfile Generator |

📁 Project Structure
AI-DevOps-Assistant/
│
├── backend/
│   └── main.py
│
├── src/
│   ├── App.tsx
│   ├── index.css
│
├── index.html
├── package.json
└── README.md

🎯 Future Improvements
Kubernetes generator
Terraform generator
Deployment automation
Cloud cost optimizer


👨‍💻 Author

Rakesh Tummala
B.Tech CSE | Cloud + AI Enthusiast