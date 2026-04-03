import { useState, useEffect } from "react";
import axios from "axios";
import {
  FaRocket,
  FaCheckCircle,
  FaGithub,
  FaDocker,
  FaCloud
} from "react-icons/fa";

// Change this when deploying frontend later
const API_URL = "http://localhost:8000";

function App() {

  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const [deployStatus, setDeployStatus] = useState("Idle");
  const [logs, setLogs] = useState([]);
  const [liveUrl, setLiveUrl] = useState("");

  // Poll deployment status
  useEffect(() => {

    const interval = setInterval(() => {

      axios
        .get(`${API_URL}/deployment-status/`)
        .then((res) => {

          setDeployStatus(res.data.status || "Idle");
          setLogs(res.data.logs || []);

          if (res.data.url) {
            setLiveUrl(res.data.url);
          }

        })
        .catch((err) => {
          console.log("Polling error:", err.message);
        });

    }, 2000);

    return () => clearInterval(interval);

  }, []);

  // Deploy Handler
  const handleDeploy = async () => {

    if (!file) {
      setStatus("Please upload a ZIP file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {

      setLoading(true);
      setStatus("Starting deployment...");
      setLiveUrl("");

      console.log("Uploading file...");

      const response = await axios.post(
        `${API_URL}/upload-zip/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        }
      );

      console.log("Response:", response.data);

      setStatus(response.data.message || "Deployment started");

    } catch (error) {

      console.error("Deploy error:", error);

      setStatus("Deployment Failed");

    } finally {

      setLoading(false);

    }

  };

  // Progress calculation
  const getProgress = () => {

    if (deployStatus.includes("Starting")) return 20;
    if (deployStatus.includes("Dockerfile")) return 40;
    if (deployStatus.includes("GitHub")) return 60;
    if (deployStatus.includes("Render")) return 80;
    if (deployStatus.includes("Complete")) return 100;

    return 0;
  };

  return (

    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">

      <div className="bg-gray-800 shadow-2xl rounded-2xl p-8 w-[650px]">

        <h1 className="text-3xl font-bold mb-6 text-center flex items-center justify-center gap-2">
          <FaRocket />
          AI DevOps Dashboard
        </h1>

        {/* Upload */}
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

        <p className="text-sm text-gray-400 mb-4">
          {status}
        </p>

        {/* Progress Bar */}
        <div className="mb-6">

          <div className="w-full bg-gray-700 rounded-full h-3">

            <div
              className="bg-green-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${getProgress()}%` }}
            />

          </div>

          <p className="mt-2 text-sm text-gray-400">
            {deployStatus}
          </p>

        </div>

        {/* Deployment Timeline */}

        <div className="mb-6">

          <h2 className="font-semibold mb-3">
            Deployment Timeline
          </h2>

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

        {/* Logs */}

        <div className="mb-6">

          <h2 className="font-semibold mb-2">
            Deployment Logs
          </h2>

          <div className="bg-black text-green-400 font-mono p-4 rounded-lg h-40 overflow-y-auto">

            {logs.length === 0 ? (
              <p>No logs yet</p>
            ) : (
              logs.map((log, index) => (
                <p key={index}>{log}</p>
              ))
            )}

          </div>

        </div>

        {/* Live URL */}

        {liveUrl && liveUrl !== "Deployment started..." && (
          <div>

            <h2 className="font-semibold mb-2">
              Live URL
            </h2>

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

      </div>

    </div>

  );

}

export default App;