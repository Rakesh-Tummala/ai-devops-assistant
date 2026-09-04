import zipfile
import os
import shutil

MAX_MEMBERS = 20000
MAX_EXTRACTED_BYTES = 2000 * 1024 * 1024


def _safe_member_path(name, dest_root):
    if os.path.isabs(name) or (len(name) > 1 and name[1] == ":"):
        raise ValueError(f"Unsafe path in zip: {name}")

    dest = os.path.realpath(os.path.join(dest_root, name))
    root = os.path.realpath(dest_root)

    if os.path.commonpath([dest, root]) != root:
        raise ValueError(f"Path traversal in zip: {name}")

    return dest


def extract_zip(file_path, extract_to="projects"):
    os.makedirs(extract_to, exist_ok=True)

    try:
        zip_ref = zipfile.ZipFile(file_path, 'r')
    except zipfile.BadZipFile:
        raise ValueError("Uploaded file is not a valid zip archive")

    with zip_ref:
        infos = zip_ref.infolist()

        if len(infos) > MAX_MEMBERS:
            raise ValueError("Zip has too many entries")

        total_size = sum(info.file_size for info in infos)
        if total_size > MAX_EXTRACTED_BYTES:
            raise ValueError("Zip expands beyond the allowed size")

        for info in infos:
            target = _safe_member_path(info.filename, extract_to)

            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zip_ref.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)

    # Unwrap a single GitHub-style wrapper folder (e.g. "myproject-main/").
    # Only do this when the zip root contains exactly one real entry and
    # that entry is a directory — otherwise a normal project with several
    # top-level folders (src/, public/, ...) would get them all merged
    # into one directory, silently dropping same-named files.
    ignored = {".git", "__MACOSX", ".github"}
    items = [
        item for item in os.listdir(extract_to)
        if item not in ignored and not item.endswith(".zip")
    ]

    if len(items) == 1:
        item_path = os.path.join(extract_to, items[0])

        if os.path.isdir(item_path):
            for sub in os.listdir(item_path):
                src = os.path.join(item_path, sub)
                dst = os.path.join(extract_to, sub)

                if not os.path.exists(dst):
                    shutil.move(src, dst)

            try:
                shutil.rmtree(item_path)
            except Exception:
                pass

    return extract_to
