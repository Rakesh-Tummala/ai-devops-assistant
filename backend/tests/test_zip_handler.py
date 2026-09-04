import os
import zipfile

import pytest

from utils.zip_handler import extract_zip


def make_zip(path, members: dict):
    with zipfile.ZipFile(path, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)


def test_extract_preserves_multiple_top_level_folders(tmp_path):
    zpath = tmp_path / "proj.zip"
    make_zip(zpath, {
        "src/index.js": "console.log(1)",
        "public/index.html": "<html></html>",
        "package.json": "{}",
    })

    out = tmp_path / "out"
    extract_zip(str(zpath), extract_to=str(out))

    assert set(os.listdir(out)) == {"src", "public", "package.json"}
    assert os.path.isfile(out / "src" / "index.js")
    assert os.path.isfile(out / "public" / "index.html")


def test_extract_unwraps_single_github_style_wrapper(tmp_path):
    zpath = tmp_path / "proj.zip"
    make_zip(zpath, {
        "myrepo-main/src/index.js": "console.log(1)",
        "myrepo-main/package.json": "{}",
    })

    out = tmp_path / "out"
    extract_zip(str(zpath), extract_to=str(out))

    assert set(os.listdir(out)) == {"src", "package.json"}
    assert not os.path.isdir(out / "myrepo-main")


def test_extract_rejects_path_traversal(tmp_path):
    zpath = tmp_path / "evil.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr("../../evil.txt", "pwned")

    out = tmp_path / "out"
    with pytest.raises(ValueError):
        extract_zip(str(zpath), extract_to=str(out))


def test_extract_rejects_absolute_path_member(tmp_path):
    zpath = tmp_path / "evil.zip"
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr("/etc/passwd", "pwned")

    out = tmp_path / "out"
    with pytest.raises(ValueError):
        extract_zip(str(zpath), extract_to=str(out))


def test_extract_rejects_too_many_members(tmp_path, monkeypatch):
    import utils.zip_handler as zip_handler
    monkeypatch.setattr(zip_handler, "MAX_MEMBERS", 2)

    zpath = tmp_path / "many.zip"
    make_zip(zpath, {"a.txt": "1", "b.txt": "2", "c.txt": "3"})

    out = tmp_path / "out"
    with pytest.raises(ValueError):
        extract_zip(str(zpath), extract_to=str(out))


def test_extract_rejects_oversized_total(tmp_path, monkeypatch):
    import utils.zip_handler as zip_handler
    monkeypatch.setattr(zip_handler, "MAX_EXTRACTED_BYTES", 10)

    zpath = tmp_path / "big.zip"
    make_zip(zpath, {"a.txt": "x" * 1000})

    out = tmp_path / "out"
    with pytest.raises(ValueError):
        extract_zip(str(zpath), extract_to=str(out))
