"""Pluggable JSON storage for tracker.json and raw note files.

STORAGE_BACKEND=local (default) reads/writes the local data/ directory —
used for local development and testing with main.py. STORAGE_BACKEND=github
reads/writes the same relative paths inside the GitHub repo via the Contents
API instead — used by the deployed Vercel webhook, which has no persistent
local filesystem between invocations.

Known limitation: the github backend does a plain read-modify-write with no
locking. Two webhook invocations racing on the same file could lose one
update. Acceptable for a solo, low-volume channel; would need real
concurrency control (or a proper database) at higher note volume.
"""

import base64
import json
import os

import requests

GITHUB_API_BASE = "https://api.github.com"


def _backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "local")


def _local_path(relative_path: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def _github_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token or token.startswith("REPLACE_ME"):
        raise RuntimeError("GITHUB_TOKEN is not set. Required when STORAGE_BACKEND=github.")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def _github_repo() -> str:
    repo = os.environ.get("GITHUB_REPO", "")
    if not repo:
        raise RuntimeError(
            "GITHUB_REPO is not set (expected 'owner/repo'). Required when STORAGE_BACKEND=github."
        )
    return repo


def read_json(relative_path: str, default: dict | None) -> dict | None:
    if _backend() == "local":
        path = _local_path(relative_path)
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    url = f"{GITHUB_API_BASE}/repos/{_github_repo()}/contents/{relative_path}"
    response = requests.get(url, headers=_github_headers(), timeout=15)
    if response.status_code == 404:
        return default
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"]).decode("utf-8")
    return json.loads(content)


def write_json(relative_path: str, data: dict, message: str) -> None:
    if _backend() == "local":
        path = _local_path(relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return

    url = f"{GITHUB_API_BASE}/repos/{_github_repo()}/contents/{relative_path}"
    headers = _github_headers()
    existing = requests.get(url, headers=headers, timeout=15)
    sha = existing.json()["sha"] if existing.status_code == 200 else None

    content_b64 = base64.b64encode(
        (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    ).decode("utf-8")
    payload = {"message": message, "content": content_b64}
    if sha:
        payload["sha"] = sha
    response = requests.put(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
