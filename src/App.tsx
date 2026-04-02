import { useState } from "react";

function App() {
  const [activeTab, setActiveTab] = useState("log");
  const [response, setResponse] = useState("");
  const [message, setMessage] = useState("");
  const [projectType, setProjectType] = useState("");
  const [file, setFile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [cicdType, setCicdType] = useState("github");

  // ---------------------------
  // Copy Function
  // ---------------------------
  const copyToClipboard = () => {
    navigator.clipboard.writeText(response);
  };

  // ---------------------------
  // Download YAML
  // ---------------------------
  const downloadFile = () => {
    const blob = new Blob([response], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "output.txt";
    a.click();
  };

  // ---------------------------
  // Log Upload
  // ---------------------------
  const handleLogUpload = (e: any) => {
    setFile(e.target.files[0]);
  };

  const submitLog = async () => {
    setLoading(true);
    setResponse("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://127.0.0.1:8000/analyze-log/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data.analysis || "No analysis returned");
    } catch (error) {
      setResponse("Error analyzing logs");
    }

    setLoading(false);
  };

  // ---------------------------
  // Chat
  // ---------------------------
  const handleChat = async () => {
    setLoading(true);
    setResponse("");

    try {
      const res = await fetch("http://127.0.0.1:8000/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
        }),
      });

      const data = await res.json();
      setResponse(data.response || "No response received");
    } catch (error) {
      setResponse("Error generating response");
    }

    setLoading(false);
  };

  // ---------------------------
  // Project Upload
  // ---------------------------
  const handleProjectUpload = (e: any) => {
    setFile(e.target.files[0]);
  };

  // ---------------------------
  // CICD Generator
  // ---------------------------
  const handleCICD = async () => {
    setLoading(true);
    setResponse("");

    try {
      const formData = new FormData();

      if (file) {
        formData.append("file", file);
      }

      formData.append("project_type", projectType);
      formData.append("cicd_type", cicdType);

      const res = await fetch("http://127.0.0.1:8000/generate-cicd/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data.response || "No response received");
    } catch (error) {
      setResponse("Error generating pipeline");
    }

    setLoading(false);
  };

  // ---------------------------
  // Docker Generator
  // ---------------------------
  const handleDocker = async () => {
    setLoading(true);
    setResponse("");

    try {
      const formData = new FormData();

      if (file) {
        formData.append("file", file);
      }

      formData.append("project_type", projectType);

      const res = await fetch("http://127.0.0.1:8000/generate-docker/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data.response || "No response received");
    } catch (error) {
      setResponse("Error generating dockerfile");
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6 text-center">
        AI DevOps Assistant
      </h1>

      {/* Tabs */}
      <div className="flex gap-4 justify-center mb-6">
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 rounded"
          onClick={() => setActiveTab("log")}
        >
          Log Analyzer
        </button>

        <button
          type="button"
          className="px-4 py-2 bg-green-600 rounded"
          onClick={() => setActiveTab("chat")}
        >
          DevOps Chat
        </button>

        <button
          type="button"
          className="px-4 py-2 bg-purple-600 rounded"
          onClick={() => setActiveTab("cicd")}
        >
          CI/CD Generator
        </button>
      </div>

      {/* Log Analyzer */}
      {activeTab === "log" && (
        <div className="text-center">
          <input
            type="file"
            className="bg-white text-black p-2 rounded"
            onChange={handleLogUpload}
          />

          <button
            type="button"
            className="ml-3 px-4 py-2 bg-blue-600 rounded"
            onClick={submitLog}
          >
            Submit
          </button>
        </div>
      )}

      {/* DevOps Chat */}
      {activeTab === "chat" && (
        <div className="text-center">
          <input
            type="text"
            placeholder="Ask DevOps question..."
            className="bg-white text-black p-2 rounded w-96"
            onChange={(e) => setMessage(e.target.value)}
          />

          <button
            type="button"
            className="ml-2 px-4 py-2 bg-green-600 rounded"
            onClick={handleChat}
          >
            Ask
          </button>
        </div>
      )}

      {/* CICD Generator */}
      {activeTab === "cicd" && (
        <div className="text-center space-y-3">
          <input
            type="file"
            className="bg-white text-black p-2 rounded"
            onChange={handleProjectUpload}
          />

          <br />

          <input
            type="text"
            placeholder="Enter project type (optional)..."
            className="bg-white text-black p-2 rounded w-96"
            onChange={(e) => setProjectType(e.target.value)}
          />

          <br />

          <select
            className="bg-white text-black p-2 rounded"
            onChange={(e) => setCicdType(e.target.value)}
          >
            <option value="github">GitHub Actions</option>
            <option value="gitlab">GitLab CI</option>
            <option value="jenkins">Jenkins</option>
          </select>

          <br />

          <button
            type="button"
            className="px-4 py-2 bg-purple-600 rounded"
            onClick={handleCICD}
          >
            Generate CI/CD
          </button>

          <button
            type="button"
            className="ml-2 px-4 py-2 bg-orange-600 rounded"
            onClick={handleDocker}
          >
            Generate Dockerfile
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center mt-6">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white mx-auto"></div>
          <p className="mt-2">Generating...</p>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="mt-8 p-4 bg-gray-900 rounded-lg">
          <div className="flex justify-between mb-2">
            <h2 className="text-xl">Result</h2>

            <div>
              <button
                type="button"
                className="px-3 py-1 bg-blue-600 rounded mr-2"
                onClick={copyToClipboard}
              >
                Copy
              </button>

              <button
                type="button"
                className="px-3 py-1 bg-green-600 rounded"
                onClick={downloadFile}
              >
                Download
              </button>
            </div>
          </div>

          <pre className="whitespace-pre-wrap text-green-300">
            {response}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;