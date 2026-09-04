import { useState, useEffect } from "react";
import axios from "axios";
import {
  FaRocket,
  FaCheckCircle,
  FaGithub,
  FaDocker,
  FaCloud,
  FaFileAlt,
  FaComments,
  FaCogs,
  FaCopy,
  FaDownload
} from "react-icons/fa";

// Your deployed backend
const API_URL = "https://ai-devops-assistant-backend-mvrs.onrender.com";

const TABS = [
  { key: "deploy", label: "Deploy", icon: <FaRocket /> },
  { key: "log", label: "Log Analyzer", icon: <FaFileAlt /> },
  { key: "chat", label: "DevOps Chat", icon: <FaComments /> },
  { key: "cicd", label: "CI/CD Generator", icon: <FaCogs /> },
  { key: "docker", label: "Dockerfile Generator", icon: <FaDocker /> }
];

const PROJECT_TYPES = [
  "nextjs", "vite", "react", "node", "fastapi", "flask", "python", "unknown"
];

const CICD_TYPES = ["github", "gitlab", "circleci"];

function ResultPanel({ output, loading }) {
  const copyToClipboard = () => {
    if (output) navigator.clipboard.writeText(output);
  };

  const downloadFile = () => {
    if (!output) return;
    const blob = new Blob([output], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "output.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!loading && !output) return null;

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-semibold">Result</h2>
        {output && (
          <div className="flex gap-2">
            <button
              onClick={copyToClipboard}
              className="text-gray-300 hover:text-white flex items-center gap-1 text-sm"
            >
              <FaCopy /> Copy
            </button>
            <button
              onClick={downloadFile}
              className="text-gray-300 hover:text-white flex items-center gap-1 text-sm"
            >
              <FaDownload /> Download
            </button>
          </div>
        )}
      </div>
      <pre className="bg-black text-green-400 font-mono p-4 rounded-lg max-h-80 overflow-auto whitespace-pre-wrap text-sm">
        {loading ? "Working..." : output}
      </pre>
    </div>
  );
}

function App() {
  const [accessKey, setAccessKey] = useState(
    () => localStorage.getItem("appAccessKey") || ""
  );
  const [keyInput, setKeyInput] = useState("");
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    axios.defaults.headers.common["X-App-Key"] = accessKey;
  }, [accessKey]);

  useEffect(() => {
    const id = axios.interceptors.response.use(
      (res) => res,
      (error) => {
        if (error?.response?.status === 401) {
          localStorage.removeItem("appAccessKey");
          setAccessKey("");
          setAuthError("Access key rejected — try again.");
        }
        return Promise.reject(error);
      }
    );
    return () => axios.interceptors.response.eject(id);
  }, []);

  const unlock = (e) => {
    e.preventDefault();
    if (!keyInput.trim()) return;
    localStorage.setItem("appAccessKey", keyInput.trim());
    setAccessKey(keyInput.trim());
    setAuthError("");
  };

  const [activeTab, setActiveTab] = useState("deploy");

  // ---- Deploy tab state ----
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [deployStatus, setDeployStatus] = useState("Idle");
  const [logs, setLogs] = useState([]);
  const [liveUrl, setLiveUrl] = useState("");

  // ---- Shared tool state (log analyzer / chat / cicd / docker) ----
  const [toolOutput, setToolOutput] = useState("");
  const [toolLoading, setToolLoading] = useState(false);

  // Log Analyzer
  const [logFile, setLogFile] = useState(null);

  // DevOps Chat
  const [chatMessage, setChatMessage] = useState("");

  // CI/CD Generator
  const [cicdProjectType, setCicdProjectType] = useState("node");
  const [cicdType, setCicdType] = useState("github");
  const [cicdFile, setCicdFile] = useState(null);

  // Dockerfile Generator
  const [dockerProjectType, setDockerProjectType] = useState("node");
  const [dockerFile, setDockerFile] = useState(null);

  // Poll deployment status
  useEffect(() => {
    if (!accessKey) return;

    const interval = setInterval(() => {
      axios
        .get(`${API_URL}/deployment-status/`)
        .then((res) => {
          if (res.data.status) setDeployStatus(res.data.status);
          if (res.data.logs) setLogs(res.data.logs);
          if (res.data.url) setLiveUrl(res.data.url);
        })
        .catch(() => {});
    }, 2000);

    return () => clearInterval(interval);
  }, [accessKey]);

  const handleDeploy = async () => {
    if (!file) {
      setStatus("Please upload a ZIP file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setLogs([]);
      setLiveUrl("");
      setDeployStatus("Starting Deployment...");
      setStatus("Starting deployment...");

      const response = await axios.post(`${API_URL}/upload-zip/`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setStatus(response.data.message || "Deployment started");
    } catch (error) {
      setStatus(error?.response?.data?.detail || "Deployment Failed");
    } finally {
      setLoading(false);
    }
  };

  const getProgress = () => {
    if (deployStatus.includes("Starting")) return 20;
    if (deployStatus.includes("Dockerfile")) return 40;
    if (deployStatus.includes("GitHub")) return 60;
    if (deployStatus.includes("Render")) return 80;
    if (deployStatus.includes("Complete")) return 100;
    return 0;
  };

  const runTool = async (fn) => {
    setToolOutput("");
    setToolLoading(true);
    try {
      await fn();
    } catch (error) {
      setToolOutput(error?.response?.data?.detail || "Something went wrong");
    } finally {
      setToolLoading(false);
    }
  };

  const submitLog = () =>
    runTool(async () => {
      if (!logFile) {
        setToolOutput("Please choose a log file first");
        return;
      }
      const formData = new FormData();
      formData.append("file", logFile);
      const res = await axios.post(`${API_URL}/analyze-log/`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setToolOutput(res.data.analysis || "No analysis returned");
    });

  const handleChat = () =>
    runTool(async () => {
      if (!chatMessage.trim()) {
        setToolOutput("Please enter a message first");
        return;
      }
      const res = await axios.post(`${API_URL}/chat/`, {
        message: chatMessage
      });
      setToolOutput(res.data.response || "No response received");
    });

  const handleCICD = () =>
    runTool(async () => {
      const formData = new FormData();
      formData.append("project_type", cicdProjectType);
      formData.append("cicd_type", cicdType);
      if (cicdFile) formData.append("file", cicdFile);
      const res = await axios.post(`${API_URL}/generate-cicd/`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setToolOutput(res.data.response || "No response received");
    });

  const handleDocker = () =>
    runTool(async () => {
      const formData = new FormData();
      formData.append("project_type", dockerProjectType);
      if (dockerFile) formData.append("file", dockerFile);
      const res = await axios.post(`${API_URL}/generate-docker/`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setToolOutput(res.data.response || "No response received");
    });

  const switchTab = (key) => {
    setActiveTab(key);
    setToolOutput("");
  };

  if (!accessKey) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <form
          onSubmit={unlock}
          className="bg-gray-800 shadow-2xl rounded-2xl p-8 w-[380px]"
        >
          <h1 className="text-2xl font-bold mb-4 text-center flex items-center justify-center gap-2">
            <FaRocket />
            AI DevOps Assistant
          </h1>
          <p className="text-sm text-gray-400 mb-4 text-center">
            Enter the access key to continue.
          </p>
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder="Access key"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm mb-3"
            autoFocus
          />
          {authError && (
            <p className="text-sm text-red-400 mb-3">{authError}</p>
          )}
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
          >
            Unlock
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center py-10">
      <div className="bg-gray-800 shadow-2xl rounded-2xl p-8 w-[700px]">
        <h1 className="text-3xl font-bold mb-6 text-center flex items-center justify-center gap-2">
          <FaRocket />
          AI DevOps Assistant
        </h1>

        {/* Tab bar */}
        <div className="flex flex-wrap gap-2 mb-6 justify-center">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => switchTab(tab.key)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                activeTab === tab.key
                  ? "bg-blue-600"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "deploy" && (
          <>
            <div className="mb-6 flex items-center justify-between">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setFile(e.target.files[0])}
              />
              <button
                onClick={handleDeploy}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
              >
                {loading ? "Deploying..." : "Deploy"}
              </button>
            </div>

            <p className="text-sm text-gray-400 mb-4">{status}</p>

            <div className="mb-6">
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${getProgress()}%` }}
                />
              </div>
              <p className="mt-2 text-sm text-gray-400">{deployStatus}</p>
            </div>

            <div className="mb-6">
              <h2 className="font-semibold mb-3">Deployment Timeline</h2>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <FaDocker /> Generate Dockerfile
                </div>
                <div className="flex items-center gap-2">
                  <FaGithub /> Push to GitHub
                </div>
                <div className="flex items-center gap-2">
                  <FaCloud /> Deploy to Render
                </div>
                <div className="flex items-center gap-2">
                  <FaCheckCircle /> Deployment Complete
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h2 className="font-semibold mb-2">Deployment Logs</h2>
              <div className="bg-black text-green-400 font-mono p-4 rounded-lg h-40 overflow-y-auto">
                {logs.length === 0 ? (
                  <p>No logs yet</p>
                ) : (
                  logs.map((log, index) => <p key={index}>{log}</p>)
                )}
              </div>
            </div>

            {liveUrl && (
              <div>
                <h2 className="font-semibold mb-2">Live URL</h2>
                <a
                  href={liveUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 underline"
                >
                  {liveUrl}
                </a>
              </div>
            )}
          </>
        )}

        {activeTab === "log" && (
          <div>
            <p className="text-sm text-gray-400 mb-3">
              Upload a log file to get an AI-generated root-cause analysis and
              remediation suggestions.
            </p>
            <div className="flex items-center justify-between mb-2">
              <input
                type="file"
                onChange={(e) => setLogFile(e.target.files[0])}
              />
              <button
                onClick={submitLog}
                disabled={toolLoading}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
              >
                {toolLoading ? "Analyzing..." : "Analyze"}
              </button>
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div>
            <p className="text-sm text-gray-400 mb-3">
              Ask a DevOps question — deployments, CI/CD, containers, cloud
              infra, troubleshooting.
            </p>
            <textarea
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="e.g. Why would a Docker build fail with 'no space left on device'?"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm mb-2 h-28"
            />
            <button
              onClick={handleChat}
              disabled={toolLoading}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
            >
              {toolLoading ? "Thinking..." : "Send"}
            </button>
          </div>
        )}

        {activeTab === "cicd" && (
          <div>
            <p className="text-sm text-gray-400 mb-3">
              Generate a CI/CD pipeline for your project type and target
              platform.
            </p>
            <div className="flex gap-3 mb-3">
              <select
                value={cicdProjectType}
                onChange={(e) => setCicdProjectType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm flex-1"
              >
                {PROJECT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <select
                value={cicdType}
                onChange={(e) => setCicdType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm flex-1"
              >
                {CICD_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center justify-between">
              <input
                type="file"
                onChange={(e) => setCicdFile(e.target.files[0])}
              />
              <button
                onClick={handleCICD}
                disabled={toolLoading}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
              >
                {toolLoading ? "Generating..." : "Generate"}
              </button>
            </div>
          </div>
        )}

        {activeTab === "docker" && (
          <div>
            <p className="text-sm text-gray-400 mb-3">
              Generate a production-ready Dockerfile for your project type.
            </p>
            <div className="flex items-center justify-between mb-3">
              <select
                value={dockerProjectType}
                onChange={(e) => setDockerProjectType(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded-lg p-2 text-sm flex-1 mr-3"
              >
                {PROJECT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <input
                type="file"
                onChange={(e) => setDockerFile(e.target.files[0])}
              />
            </div>
            <button
              onClick={handleDocker}
              disabled={toolLoading}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
            >
              {toolLoading ? "Generating..." : "Generate"}
            </button>
          </div>
        )}

        {activeTab !== "deploy" && (
          <ResultPanel output={toolOutput} loading={toolLoading} />
        )}
      </div>
    </div>
  );
}

export default App;
