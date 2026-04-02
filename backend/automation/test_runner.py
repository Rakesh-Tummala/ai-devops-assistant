import subprocess

def run_tests(project_type):

    if project_type == "python":
        subprocess.run(["pytest"])

    elif project_type == "node":
        subprocess.run(["npm", "test"])

    elif project_type == "java":
        subprocess.run(["mvn", "test"])

    return "Tests completed"