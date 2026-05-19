import json
import os
import sqlite3
import subprocess
import sys
import time
import hashlib

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
DB_PATH = os.path.join(os.path.dirname(__file__), "database", "mentra.db")


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\nSTDOUT: {p.stdout}\nSTDERR: {p.stderr}")
    return p.stdout.strip()


def curl_json(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    cmd = ["curl", "-s", "-X", method, url, "-H", "Content-Type: application/json"]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    out = sh(cmd)
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Non-JSON response from {method} {path}: {out}") from e


def ensure_admin(username: str, password: str) -> None:
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password, role, created_at) VALUES (?, ?, 'admin', datetime('now'))",
            (username, h),
        )
        conn.commit()
    finally:
        conn.close()


def main() -> int:
    print(f"BASE_URL={BASE_URL}")

    health = curl_json("GET", "/health")
    print("/health:", health)

    username = f"u{int(time.time())}"[:20]
    password = "Test@1234A"

    reg = curl_json("POST", "/auth/register", {"username": username, "password": password})
    print("/auth/register:", {"user": reg.get("username"), "role": reg.get("role")})
    token = reg["access_token"]

    me = curl_json("GET", "/me", token=token)
    print("/me:", me)

    features = [0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    pred = curl_json("POST", "/predict", {"features": features}, token=token)
    print("/predict:", {"stress_label": pred.get("stress_label"), "confidence": pred.get("confidence")})

    hist = curl_json("GET", "/me/predictions", token=token)
    print("/me/predictions count:", len(hist) if isinstance(hist, list) else "?")

    admin_user = "Admin"
    admin_pass = "Admin@123"
    ensure_admin(admin_user, admin_pass)

    admin_login = curl_json("POST", "/auth/login", {"username": admin_user, "password": admin_pass})
    admin_token = admin_login["access_token"]
    print("/auth/login (admin):", {"user": admin_login.get("username"), "role": admin_login.get("role")})

    users = curl_json("GET", "/admin/users", token=admin_token)
    preds = curl_json("GET", "/admin/predictions", token=admin_token)
    print("/admin/users count:", len(users) if isinstance(users, list) else "?")
    print("/admin/predictions count:", len(preds) if isinstance(preds, list) else "?")

    print("SMOKE TEST: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
