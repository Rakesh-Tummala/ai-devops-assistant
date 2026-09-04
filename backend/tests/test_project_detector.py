import json
import os

from utils.project_detector import detect_project


def write_package_json(path, data):
    with open(os.path.join(path, "package.json"), "w") as f:
        json.dump(data, f)


def test_detects_react(tmp_path):
    write_package_json(tmp_path, {"dependencies": {"react": "^18"}})
    assert detect_project(str(tmp_path)) == "react"


def test_detects_vite(tmp_path):
    write_package_json(tmp_path, {"devDependencies": {"vite": "^5"}})
    assert detect_project(str(tmp_path)) == "vite"


def test_detects_nextjs(tmp_path):
    write_package_json(tmp_path, {"dependencies": {"next": "^14"}})
    assert detect_project(str(tmp_path)) == "nextjs"


def test_plain_dependency_named_next_auth_is_not_misdetected_as_nextjs(tmp_path):
    write_package_json(tmp_path, {"dependencies": {"next-auth": "^4"}})
    assert detect_project(str(tmp_path)) == "node"


def test_defaults_to_node_for_unrecognized_package_json(tmp_path):
    write_package_json(tmp_path, {"dependencies": {"express": "^4"}})
    assert detect_project(str(tmp_path)) == "node"


def test_detects_fastapi(tmp_path):
    with open(tmp_path / "requirements.txt", "w") as f:
        f.write("fastapi\nuvicorn\n")
    assert detect_project(str(tmp_path)) == "fastapi"


def test_detects_flask(tmp_path):
    with open(tmp_path / "requirements.txt", "w") as f:
        f.write("flask\n")
    assert detect_project(str(tmp_path)) == "flask"


def test_unknown_when_nothing_matches(tmp_path):
    assert detect_project(str(tmp_path)) == "unknown"
