import zipfile
import os

def extract_zip(file_path, extract_to="projects"):
    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    return extract_to