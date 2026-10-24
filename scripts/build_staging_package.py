"""Build a credential-free staging ZIP containing Django source and collected static."""
import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRS = ("accounts", "articles", "config", "courses", "exams", "pages",
        "templates", "static", "staticfiles")
FILES = ("manage.py", "requirements.txt", ".env.example", "scripts/staging_smoke.py")
SKIP_DIRS = {"__pycache__", "fixtures", ".pytest_cache", ".venv", "venv"}
SKIP_FILES = {"tests.py", ".env", "db.sqlite3"}


def release_files():
    files = [ROOT / name for name in FILES]
    for name in DIRS:
        folder = ROOT / name
        if not folder.is_dir():
            raise FileNotFoundError(f"Required release directory missing: {name}")
        files.extend(folder.rglob("*"))
    selected = []
    for path in files:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            raise ValueError(f"Symlinks are not permitted in the release: {relative}")
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.name in SKIP_FILES or path.name.startswith("test_"):
            continue
        if path.suffix in (".pyc", ".pyo", ".sqlite3"):
            continue
        selected.append(path)
    return sorted(selected)


def main():
    paths = release_files()
    if not any(path.relative_to(ROOT).parts[0] == "staticfiles" for path in paths):
        raise RuntimeError("Run collectstatic before staging packaging.")
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    commit = os.getenv("GITHUB_SHA", "local")
    archive = output / f"scs-gyan-staging-{commit[:7]}.zip"
    manifest = {"source_commit": commit, "type": "staging-source-and-static", "files": {}}
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            zipped.writestr(relative, data)
            manifest["files"][relative] = hashlib.sha256(data).hexdigest()
        zipped.writestr("RELEASE-MANIFEST.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(archive) as zipped:
        names = set(zipped.namelist())
        required = {"manage.py", "requirements.txt", ".env.example",
                    "config/wsgi.py", "scripts/staging_smoke.py", "RELEASE-MANIFEST.json"}
        if not required.issubset(names):
            raise AssertionError(f"Missing release files: {required - names}")
        if any(name.endswith("/.env") or "private_media/" in name
               or ".git/" in name or name.endswith(".sqlite3") for name in names):
            raise AssertionError("Private data detected inside release.")
        for path, digest in manifest["files"].items():
            if hashlib.sha256(zipped.read(path)).hexdigest() != digest:
                raise AssertionError(f"Checksum mismatch: {path}")
    print(f"Built {archive.name} with {len(paths)} verified files.")


if __name__ == "__main__":
    main()
