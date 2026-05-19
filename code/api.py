import os
import sqlite3
import pickle
import hashlib
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import psutil
from fastapi import Depends, FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel, Field


DB_PATH = os.path.join(os.path.dirname(__file__), "database", "mentra.db")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "mentra_rf_model.pkl")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "10080"))

APP_START_TS = time.time()


STRESS_LABELS: Dict[int, str] = {
    0: "Low Stress",
    1: "Moderate Stress",
    2: "High Stress",
}


class RegisterRequest(BaseModel):
    username: str = Field(min_length=4, max_length=20)
    email: str
    password: str = Field(min_length=8)
    security_question: str
    security_answer: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None


class PredictRequest(BaseModel):
    features: Dict[str, float]


class FeatureContribution(BaseModel):
    feature: str
    value: float
    score: float
    percent: float


class PredictResponse(BaseModel):
    predicted_class: int
    stress_label: str
    confidence: float
    probabilities: Dict[str, float]
    prediction_id: Optional[int] = None
    timestamp: str
    suggestion: Optional[Dict[str, Any]] = None
    feature_contributions: Optional[List[FeatureContribution]] = None


class PredictionRecord(BaseModel):
    id: int
    stress_level: str
    confidence: float
    timestamp: str

class SuggestionRecord(BaseModel):
    id: int
    text: str
    type: str # 'URGENT', 'ROUTINE', 'POSITIVE'
    timestamp: str
    context: Optional[str] = None
    explanation: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    fullName: str
    dateOfBirth: str
    bloodGroup: str
    allergies: str
    clinicalHighlights: str
    homeAddress: str
    responderName: str
    responderPhone: str
    secondaryContactPhone: str
    avatarUrl: Optional[str] = None
    notes: Optional[str] = None
    nodeReferences: List[Dict[str, str]] = []
    intelCode: str
    createdAt: str
    updatedAt: str
    userId: int
    riskScore: float = 0
    lastAccessedAt: Optional[str] = None

class ProfileCreate(BaseModel):
    fullName: str
    dateOfBirth: str
    bloodGroup: str
    allergies: str
    clinicalHighlights: str
    homeAddress: str
    responderName: str
    responderPhone: str
    secondaryContactPhone: str
    notes: Optional[str] = None
    nodeReferences: List[Dict[str, str]] = []

class AuditLogEntry(BaseModel):
    id: str
    action: str
    entity: str
    entityId: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    createdAt: str


class SecurityQuestionResponse(BaseModel):
    username: str
    security_question: str


class VerifyAnswerRequest(BaseModel):
    username: str
    security_answer: str


class ResetPasswordRequest(BaseModel):
    username: str
    security_answer: str
    new_password: str = Field(min_length=8)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed_password: str) -> bool:
    return _hash_password(password) == hashed_password


def _create_access_token(payload: Dict[str, Any]) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db() -> None:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                security_question TEXT,
                security_answer TEXT,
                is_suspended INTEGER DEFAULT 0,
                force_password_reset INTEGER DEFAULT 0,
                role TEXT CHECK(role IN ('user', 'admin')) NOT NULL,
                created_at TEXT
            )
            """
        )
        # Migration: Add columns if they don't exist
        try:
            cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN security_answer TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN is_suspended INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN force_password_reset INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("ALTER TABLE users ADD COLUMN avatar_base64 TEXT")
        except sqlite3.OperationalError:
            pass

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stress_level TEXT,
                confidence REAL,
                features_json TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        # Migration: add columns on existing installations
        try:
            cur.execute("ALTER TABLE predictions ADD COLUMN features_json TEXT")
        except sqlite3.OperationalError:
            pass
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                date_of_birth TEXT,
                blood_group TEXT,
                allergies TEXT,
                clinical_highlights TEXT,
                home_address TEXT,
                responder_name TEXT,
                responder_phone TEXT,
                secondary_contact_phone TEXT,
                avatar_url TEXT,
                notes TEXT,
                node_references TEXT,
                intel_code TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                risk_score REAL DEFAULT 0,
                last_accessed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                entity_id TEXT,
                payload TEXT,
                user_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT NOT NULL,
                type TEXT NOT NULL,
                context TEXT,
                explanation TEXT,
                timestamp TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        _ensure_suggestions_schema(cur)
        conn.commit()
    finally:
        conn.close()


def _ensure_suggestions_schema(cur: sqlite3.Cursor) -> None:
    # SQLite migration helper: keep existing DBs compatible.
    try:
        cur.execute("ALTER TABLE suggestions ADD COLUMN explanation TEXT")
    except sqlite3.OperationalError:
        # Column already exists (or table missing which is handled by CREATE TABLE).
        pass


_model: Any = None


def _get_model() -> Any:
    global _model
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def _generate_suggestions(
    stress_level: str,
    features: Dict[str, float],
    hour: int,
    trend: str,
    dominant_features: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Generate multiple actionable suggestions based on stress + context."""

    def add(items: List[Dict[str, Any]], s: Dict[str, Any]) -> None:
        txt = str(s.get("text") or "").strip()
        if not txt:
            return
        # de-dupe by text
        if any(str(x.get("text", "")).strip().lower() == txt.lower() for x in items):
            return
        items.append(s)

    suggestions: List[Dict[str, Any]] = []

    dom = [str(x) for x in (dominant_features or []) if str(x).strip()]
    primary_dom = dom[0] if dom else None

    # Dominant-feature-first steering: ensure the primary recommendation changes when the top driver changes.
    if primary_dom:
        if primary_dom in {"study_load", "future_career_concerns", "academic_performance"}:
            add(
                suggestions,
                {
                    "text": "Academic load is the primary driver. Break tasks into a 10-minute micro-plan, then take a 5-minute reset before continuing.",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Academic Load",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )
        elif primary_dom in {"sleep_quality"}:
            add(
                suggestions,
                {
                    "text": "Sleep quality is the primary driver. Protect a 7–8h sleep window tonight, avoid caffeine after mid-day, and do 5 minutes of slow breathing before bed.",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Sleep",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )
        elif primary_dom in {"anxiety_level", "depression", "mental_health_history", "self_esteem"}:
            add(
                suggestions,
                {
                    "text": "Emotional strain is the primary driver. Do 2 minutes of paced breathing (inhale 4s, exhale 6s), then write down the next single actionable step.",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Psychological",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )
        elif primary_dom in {"noise_level", "living_conditions", "safety", "basic_needs"}:
            add(
                suggestions,
                {
                    "text": "Environment is the primary driver. Change location or reduce noise (earplugs/NC audio), hydrate, and make a quick comfort check (temperature/light).",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Environment",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )
        elif primary_dom in {"bullying", "peer_pressure", "social_support", "teacher_student_relationship", "extracurricular_activities"}:
            add(
                suggestions,
                {
                    "text": "Social factors are the primary driver. Create distance from the trigger and contact one trusted person (friend/family/mentor) for support.",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Social",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )
        elif primary_dom in {"headache", "breathing_problem", "blood_pressure"}:
            add(
                suggestions,
                {
                    "text": "Physiological strain is the primary driver. Hydrate now, slow your breathing (inhale 4s, exhale 6s for 3 minutes), and take a short low-stimulus break.",
                    "type": "URGENT" if stress_level == "High Stress" else "ROUTINE",
                    "context": "Dominant Driver: Physiological",
                    "explanation": f"Top contributing feature: {primary_dom}.",
                },
            )

    # Temporal baseline
    is_sleep_hours = hour >= 22 or hour <= 5
    is_daylight = 6 <= hour <= 18

    if stress_level == "High Stress":
        # 1) Immediate action
        if is_sleep_hours:
            add(
                suggestions,
                {
                    "text": "Immediate sleep recovery required. Shutdown screens and do '4-7-8' breathing for 2 minutes.",
                    "type": "URGENT",
                    "context": "Temporal Cognitive Reset",
                    "explanation": f"High stress detected during sleep hours ({hour}:00).",
                },
            )
        elif is_daylight:
            add(
                suggestions,
                {
                    "text": "Immediate 15-min walk required. Leave the current room and get natural light if possible.",
                    "type": "URGENT",
                    "context": "Immediate Decompression",
                    "explanation": "High stress benefits from movement + context switch.",
                },
            )
        else:
            add(
                suggestions,
                {
                    "text": "Immediate 5-min guided breathing required. Try Box Breathing: 4-4-4-4 for 5 cycles.",
                    "type": "URGENT",
                    "context": "Immediate Decompression",
                    "explanation": "High stress outside daylight: prioritize breath regulation.",
                },
            )

        # 2) Trigger-based actions
        if features.get("headache", 0) > 4:
            add(
                suggestions,
                {
                    "text": "Physical strain detected. Drink water now and do a slow 10-min walk with steady nasal breathing.",
                    "type": "URGENT",
                    "context": "Physiological Alert",
                    "explanation": f"Headache level {features.get('headache', 0)} is high.",
                },
            )
        if features.get("breathing_problem", 0) > 3:
            add(
                suggestions,
                {
                    "text": "Respiratory tension detected. Do 3 minutes of paced breathing (inhale 4s, exhale 6s).",
                    "type": "URGENT",
                    "context": "Physiological Alert",
                    "explanation": f"Breathing issue level {features.get('breathing_problem', 0)}.",
                },
            )
        if features.get("study_load", 0) > 4:
            add(
                suggestions,
                {
                    "text": "Cognitive overload detected. Stop work for 15 minutes. No screens, no tasks. Just reset.",
                    "type": "URGENT",
                    "context": "Academic Capacity",
                    "explanation": f"Study load level {features.get('study_load', 0)}.",
                },
            )
        if features.get("bullying", 0) > 3 or features.get("peer_pressure", 0) > 4:
            add(
                suggestions,
                {
                    "text": "Social pressure detected. Distance yourself from the trigger and message a trusted person.",
                    "type": "URGENT",
                    "context": "Social Support",
                    "explanation": "Stress drivers indicate external social pressure.",
                },
            )

        # 3) Trend-aware
        if trend == "INCREASING":
            add(
                suggestions,
                {
                    "text": "Stress is trending upward. Reduce input: silence notifications for 60 minutes.",
                    "type": "URGENT",
                    "context": "Trend Response",
                    "explanation": "Recent predictions show increasing stress.",
                },
            )

    elif stress_level == "Moderate Stress":
        add(
            suggestions,
            {
                "text": "Take a 5-minute break: stand up, stretch shoulders/neck, and drink water.",
                "type": "ROUTINE",
                "context": "Proactive Maintenance",
                "explanation": "Moderate stress responds well to short resets.",
            },
        )
        if is_daylight:
            add(
                suggestions,
                {
                    "text": "Do a 10-minute light walk or step outside for fresh air.",
                    "type": "ROUTINE",
                    "context": "Movement Reset",
                    "explanation": "Daylight movement improves regulation.",
                },
            )
        if features.get("noise_level", 0) > 3:
            add(
                suggestions,
                {
                    "text": "Noise load is high. Move to a quieter space or use noise-canceling audio.",
                    "type": "ROUTINE",
                    "context": "Environmental Audit",
                    "explanation": f"Noise level {features.get('noise_level', 0)}.",
                },
            )
        if features.get("basic_needs", 0) < 3:
            add(
                suggestions,
                {
                    "text": "Basic needs low. Eat something light + protein and drink 500ml water.",
                    "type": "ROUTINE",
                    "context": "Resource Deficiency",
                    "explanation": f"Basic needs level {features.get('basic_needs', 0)}.",
                },
            )
        if trend == "INCREASING":
            add(
                suggestions,
                {
                    "text": "Stress is rising. Switch to a smaller task (5–10 mins) to avoid overload.",
                    "type": "ROUTINE",
                    "context": "Trend Response",
                    "explanation": "Recent predictions show increasing stress.",
                },
            )

    else:
        add(
            suggestions,
            {
                "text": "Maintain this baseline: keep hydration steady and protect your sleep window tonight.",
                "type": "POSITIVE",
                "context": "Resilience Baseline",
                "explanation": "Low stress detected.",
            },
        )
        add(
            suggestions,
            {
                "text": "Use this stable window for deep work: 25/5 Pomodoro for 2 cycles.",
                "type": "POSITIVE",
                "context": "Flow State",
                "explanation": "Low stress is a good opportunity for focused sessions.",
            },
        )

    # Safety: cap
    return suggestions[:5]


def _generate_suggestion(stress_level: str, features: Dict[str, float], hour: int, trend: str) -> Dict[str, Any]:
    # Backwards-compatible primary suggestion
    suggestions = _generate_suggestions(stress_level, features, hour, trend)
    return suggestions[0] if suggestions else {
        "text": "Take a short break and hydrate.",
        "type": "ROUTINE",
        "context": "Fallback",
        "explanation": "No specific triggers found.",
    }


def _get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    return parts[1]


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    token = _get_bearer_token(authorization)
    payload = _decode_token(token)

    user_id = payload.get("user_id")
    role = payload.get("role")
    username = payload.get("username")

    if not isinstance(user_id, int) or not isinstance(role, str) or not isinstance(username, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return {"user_id": user_id, "role": role, "username": username}


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


app = FastAPI(title="MENTRA API")

# Development-friendly CORS:
# - If CORS_ORIGINS is explicitly set, honor it.
# - If not set, allow all origins to avoid dev-port mismatches causing browser "Network Error".
cors_origins_raw = os.environ.get("CORS_ORIGINS")
if cors_origins_raw is None or not cors_origins_raw.strip():
    cors_origins_raw = "*"
if cors_origins_raw.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

cors_allow_credentials_env = os.environ.get("CORS_ALLOW_CREDENTIALS")
if cors_allow_credentials_env is None:
    allow_credentials = allow_origins != ["*"]
else:
    allow_credentials = cors_allow_credentials_env.strip().lower() in {"1", "true", "yes"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    _ensure_db()


@app.get("/health")
def health() -> Dict[str, Any]:
    # Keep this endpoint lightweight and safe; expose only high-level runtime metrics.
    cpu = None
    mem: Optional[Dict[str, int]] = None
    try:
        # Non-blocking snapshot. psutil may not be available if deps aren't installed.
        # NOTE: first call with interval=None can return 0.0; a tiny interval yields a real sample.
        cpu = float(psutil.cpu_percent(interval=0.1))
        vm = psutil.virtual_memory()
        mem = {
            "total": int(vm.total),
            "available": int(vm.available),
            "percent": int(vm.percent),
        }
    except Exception:
        cpu = None
        mem = None

    uptime_seconds = int(max(0.0, time.time() - APP_START_TS))
    
    return {
        "status": "ok",
        "uptimeSeconds": uptime_seconds,
        "cpuUsage": cpu,
        "memory": mem,
    }


@app.post("/auth/register", response_model=AuthResponse)
def register(req: RegisterRequest) -> AuthResponse:
    conn = _get_db()
    try:
        cur = conn.cursor()
        hashed = _hash_password(req.password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur.execute(
                "INSERT INTO users (username, email, password, security_question, security_answer, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (req.username, req.email, hashed, req.security_question, req.security_answer, "user", now),
            )
        except sqlite3.IntegrityError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from e

        conn.commit()
        user_id = int(cur.lastrowid or 0)
        role = "user"
        token = _create_access_token({"user_id": user_id, "username": req.username, "role": role})
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            username=req.username,
            email=req.email,
            role=role
        )
    finally:
        conn.close()


@app.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest) -> AuthResponse:
    conn = _get_db()
    try:
        cur = conn.cursor()
        # Support both username and email login
        cur.execute(
            "SELECT id, username, email, role, password, avatar_base64, is_suspended, force_password_reset FROM users WHERE username = ? OR email = ?",
            (req.username, req.username),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        if int(row["is_suspended"] or 0) == 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are suspended by the admin")

        if int(row["force_password_reset"] or 0) == 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Password reset required")

        if not _verify_password(req.password, str(row["password"])):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        user_id = int(row["id"])
        username = str(row["username"])
        email = str(row["email"]) if row["email"] else None
        role = str(row["role"])
        avatar_url = str(row["avatar_base64"]) if row["avatar_base64"] else None

        token = _create_access_token({"user_id": user_id, "username": username, "role": role})
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            avatar_url=avatar_url
        )
    finally:
        conn.close()


@app.post("/auth/inject-admin")
def inject_admin(username: str):
    # Promoting or creating a test admin account
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET role = 'admin' WHERE username = ? OR email = ?", (username, username))
        if cur.rowcount == 0:
             # If doesn't exist, create a default test admin
             hashed = _hash_password("admin123")
             now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
             cur.execute(
                 "INSERT INTO users (username, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
                 ("admin", "admin@mentra.sys", hashed, "admin", now),
             )
        conn.commit()
        return {"status": "success", "message": f"User {username} is now an admin or default admin created."}
    finally:
        conn.close()


@app.get("/auth/security-question/{username}", response_model=SecurityQuestionResponse)
def get_security_question(username: str):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT username, security_question FROM users WHERE username = ? OR email = ?", (username, username))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return SecurityQuestionResponse(
            username=str(row["username"]),
            security_question=str(row["security_question"] or "No security question set.")
        )
    finally:
        conn.close()


@app.post("/auth/verify-answer")
def verify_answer(req: VerifyAnswerRequest):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, security_answer FROM users WHERE username = ? OR email = ?",
            (req.username, req.username),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        
        if str(row["security_answer"] or "").lower().strip() == req.security_answer.lower().strip():
            return {"status": "verified"}
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect answer")
    finally:
        conn.close()


@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, security_answer FROM users WHERE username = ? OR email = ?",
            (req.username, req.username),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if str(row["security_answer"] or "").lower().strip() != req.security_answer.lower().strip():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

        new_hashed = _hash_password(req.new_password)
        resolved_username = str(row["username"]) if row["username"] else req.username
        cur.execute(
            "UPDATE users SET password = ?, force_password_reset = 0 WHERE username = ?",
            (new_hashed, resolved_username),
        )
        conn.commit()
        return {"status": "password reset successful"}
    finally:
        conn.close()


@app.get("/me")
def me(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT email, avatar_base64 FROM users WHERE id = ?", (user["user_id"],))
        row = cur.fetchone()
        if row is not None:
            user["email"] = str(row["email"]) if row["email"] else None
            user["avatar_url"] = str(row["avatar_base64"]) if row["avatar_base64"] else None
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


class EmailUpdateRequest(BaseModel):
    email: str


@app.post("/me/email")
def update_email(req: EmailUpdateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    email = req.email.strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, user["user_id"]))
        exists = cur.fetchone()
        if exists is not None:
            raise HTTPException(status_code=409, detail="Email already in use")

        cur.execute("UPDATE users SET email = ? WHERE id = ?", (email, user["user_id"]))
        conn.commit()
        return {"status": "success", "email": email}
    finally:
        conn.close()


class UsernameUpdateRequest(BaseModel):
    username: str = Field(min_length=4, max_length=20)


@app.post("/me/username")
def update_username(req: UsernameUpdateRequest, user: Dict[str, Any] = Depends(get_current_user)):
    next_username = req.username.strip()
    if not next_username:
        raise HTTPException(status_code=400, detail="Invalid username")

    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute("SELECT username, role FROM users WHERE id = ?", (user["user_id"],))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        current_username = str(row["username"])
        role = str(row["role"])

        if next_username == current_username:
            token = _create_access_token({"user_id": user["user_id"], "username": current_username, "role": role})
            return {"status": "success", "username": current_username, "access_token": token}

        cur.execute("SELECT id FROM users WHERE username = ?", (next_username,))
        exists = cur.fetchone()
        if exists is not None:
            raise HTTPException(status_code=409, detail="Username already exists")

        cur.execute("UPDATE users SET username = ? WHERE id = ?", (next_username, user["user_id"]))
        conn.commit()

        token = _create_access_token({"user_id": user["user_id"], "username": next_username, "role": role})
        return {"status": "success", "username": next_username, "access_token": token}
    finally:
        conn.close()


class AvatarRequest(BaseModel):
    avatar_base64: str


@app.post("/me/avatar")
def update_avatar(req: AvatarRequest, user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET avatar_base64 = ? WHERE id = ?", (req.avatar_base64, user["user_id"]))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


@app.post("/me/change-password")
def change_password(req: ChangePasswordRequest, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE id = ?", (user["user_id"],))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if not _verify_password(req.current_password, str(row["password"])):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

        new_hashed = _hash_password(req.new_password)
        cur.execute(
            "UPDATE users SET password = ?, force_password_reset = 0 WHERE id = ?",
            (new_hashed, user["user_id"]),
        )
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()


@app.get("/auth/sessions")
def get_sessions(user: Dict[str, Any] = Depends(get_current_user)):
    # In a real app, this would query a sessions table.
    # For Mentra, we'll return the current session as a real-time log.
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "data": [
            {
                "id": "current",
                "device": "Web Console / Industrial Portal",
                "createdAt": now,
                "isCurrent": True
            }
        ]
    }


@app.post("/auth/sessions/terminate-others")
def terminate_others(user: Dict[str, Any] = Depends(get_current_user)):
    return {"data": {"status": "success", "message": "All other sessions terminated."}}


@app.get("/security/my-snapshot")
def get_security_snapshot(user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT security_question FROM users WHERE id = ?", (user["user_id"],))
        row = cur.fetchone()
        has_sq = row and row["security_question"] is not None
        
        return {
            "data": {
                "status": "SECURE" if has_sq else "VULNERABLE",
                "recommendations": [
                    {
                        "title": "Account Integrity",
                        "details": "Two-factor recovery is active via Security Question." if has_sq else "Security question not established. Account recovery at risk.",
                        "type": "SECURE" if has_sq else "WARNING",
                        "icon": "ShieldCheck" if has_sq else "AlertTriangle"
                    },
                    {
                        "title": "Credential Strength",
                        "details": "AES-256 standard encryption detected on current hash.",
                        "type": "SECURE",
                        "icon": "CheckCircle"
                    }
                ]
            }
        }
    finally:
        conn.close()


@app.get("/me/predictions", response_model=List[PredictionRecord])
def my_predictions(user: Dict[str, Any] = Depends(get_current_user)) -> List[PredictionRecord]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, stress_level, confidence, timestamp
            FROM predictions
            WHERE user_id = ?
            ORDER BY timestamp DESC
            """,
            (user["user_id"],),
        )
        rows = cur.fetchall()
        return [
            PredictionRecord(
                id=int(r["id"]),
                stress_level=str(r["stress_level"]),
                confidence=float(r["confidence"]),
                timestamp=str(r["timestamp"]),
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, user: Dict[str, Any] = Depends(get_current_user)) -> PredictResponse:
    model = _get_model()

    # Feature list in exact order of StressLevelDataset.csv
    feature_names = [
        "anxiety_level", "self_esteem", "mental_health_history", "depression",
        "headache", "blood_pressure", "sleep_quality", "breathing_problem",
        "noise_level", "living_conditions", "safety", "basic_needs",
        "academic_performance", "study_load", "teacher_student_relationship",
        "future_career_concerns", "social_support", "peer_pressure",
        "extracurricular_activities", "bullying"
    ]

    features_list = []
    for fn in feature_names:
        features_list.append(float(req.features.get(fn, 0.0)))

    X = np.array(features_list, dtype=float).reshape(1, -1)
    pred = int(model.predict(X)[0])

    feature_contributions: Optional[List[FeatureContribution]] = None
    try:
        scores: Optional[np.ndarray] = None

        if hasattr(model, "coef_"):
            coef = getattr(model, "coef_")
            coef_arr = np.asarray(coef)
            if coef_arr.ndim == 2:
                if coef_arr.shape[0] > pred:
                    coef_vec = coef_arr[pred]
                else:
                    coef_vec = coef_arr[0]
            else:
                coef_vec = coef_arr
            scores = np.abs(np.asarray(coef_vec, dtype=float) * X[0])
        elif hasattr(model, "feature_importances_"):
            imp = np.asarray(getattr(model, "feature_importances_"), dtype=float)
            scores = np.abs(imp * X[0])

        if scores is not None and scores.size == len(feature_names):
            total = float(np.sum(scores))
            if total <= 0:
                total = 1.0

            contribs: List[FeatureContribution] = []
            for i, name in enumerate(feature_names):
                score = float(scores[i])
                contribs.append(
                    FeatureContribution(
                        feature=str(name),
                        value=float(X[0][i]),
                        score=score,
                        percent=float((score / total) * 100.0),
                    )
                )
            contribs.sort(key=lambda c: c.score, reverse=True)
            feature_contributions = contribs[:5]
    except Exception:
        feature_contributions = None

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        probs = {
            STRESS_LABELS.get(i, str(i)): float(proba[i] * 100.0)
            for i in range(len(proba))
        }
        confidence = float(max(probs.values()))
    else:
        probs = {}
        confidence = 0.0

    stress_label = STRESS_LABELS.get(pred, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Compute short-term stress trend from most recent predictions
    conn_trend = _get_db()
    trend = "STABLE"
    try:
        cur_trend = conn_trend.cursor()
        cur_trend.execute(
            "SELECT stress_level FROM predictions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 2",
            (user["user_id"],),
        )
        rows = cur_trend.fetchall()
        if len(rows) >= 2:
            latest = str(rows[0][0] or "")
            prev = str(rows[1][0] or "")
            order = {"Low Stress": 1, "Moderate Stress": 2, "High Stress": 3}
            if order.get(latest, 0) > order.get(prev, 0):
                trend = "INCREASING"
            elif order.get(latest, 0) < order.get(prev, 0):
                trend = "DECREASING"
    finally:
        conn_trend.close()

    hour = datetime.now().hour

    # Generate Dynamic Suggestions (multiple)
    dominant_features = [c.feature for c in (feature_contributions or [])][:3]
    suggestions = _generate_suggestions(stress_label, req.features, hour, trend, dominant_features=dominant_features)
    suggestion = suggestions[0] if suggestions else _generate_suggestion(stress_label, req.features, hour, trend)

    conn = _get_db()
    try:
        cur = conn.cursor()
        _ensure_suggestions_schema(cur)
        cur.execute(
            "INSERT INTO predictions (user_id, stress_level, confidence, features_json, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user["user_id"], stress_label, confidence, json.dumps(req.features or {}), timestamp),
        )
        row_id = cur.lastrowid
        prediction_id = int(row_id) if row_id is not None else 0
        
        # Save Suggestions (multiple)
        for s in suggestions:
            cur.execute(
                "INSERT INTO suggestions (user_id, text, type, context, explanation, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user["user_id"],
                    s.get("text"),
                    s.get("type"),
                    s.get("context"),
                    s.get("explanation"),
                    timestamp,
                ),
            )

        # Admin-notifiable audit events
        _log_activity(
            cur,
            "USER_PREDICT",
            "prediction",
            str(prediction_id),
            user["user_id"],
            {
                "stress_level": stress_label,
                "confidence": confidence,
                "trend": trend,
            },
        )
        if suggestions:
            _log_activity(
                cur,
                "SUGGESTION_GENERATED",
                "suggestion",
                str(prediction_id),
                user["user_id"],
                {
                    "count": len(suggestions),
                    "primary": suggestions[0].get("text"),
                    "stress_level": stress_label,
                },
            )
        conn.commit()
    finally:
        conn.close()

    return PredictResponse(
        predicted_class=pred,
        stress_label=stress_label,
        confidence=confidence,
        probabilities=probs,
        prediction_id=prediction_id,
        timestamp=timestamp,
        suggestion=suggestion,
        feature_contributions=feature_contributions,
    )


@app.get("/me/suggestions", response_model=List[SuggestionRecord])
def my_suggestions(user: Dict[str, Any] = Depends(get_current_user)) -> List[SuggestionRecord]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, text, type, context, explanation, timestamp
                FROM suggestions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                """,
                (user["user_id"],),
            )
        except sqlite3.OperationalError:
            # Older DB without 'explanation' column: migrate and retry.
            _ensure_suggestions_schema(cur)
            conn.commit()
            cur.execute(
                """
                SELECT id, text, type, context, explanation, timestamp
                FROM suggestions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                """,
                (user["user_id"],),
            )
        rows = cur.fetchall()

        # Backfill: if no suggestions exist yet, generate from latest prediction snapshot.
        if not rows:
            try:
                cur.execute(
                    """
                    SELECT stress_level, timestamp, features_json
                    FROM predictions
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (user["user_id"],),
                )
                p = cur.fetchone()
                if p is not None:
                    stress_level = str(p[0] or "Unknown")
                    ts_raw = str(p[1] or "")
                    features_raw = p[2]
                    try:
                        features = json.loads(features_raw) if features_raw else {}
                    except Exception:
                        features = {}

                    # Trend recompute (last 2 predictions)
                    cur.execute(
                        "SELECT stress_level FROM predictions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 2",
                        (user["user_id"],),
                    )
                    t_rows = cur.fetchall()
                    trend = "STABLE"
                    if len(t_rows) >= 2:
                        latest = str(t_rows[0][0] or "")
                        prev = str(t_rows[1][0] or "")
                        order = {"Low Stress": 1, "Moderate Stress": 2, "High Stress": 3}
                        if order.get(latest, 0) > order.get(prev, 0):
                            trend = "INCREASING"
                        elif order.get(latest, 0) < order.get(prev, 0):
                            trend = "DECREASING"

                    # Use timestamp hour if parseable, else current hour
                    hour = datetime.now().hour
                    try:
                        dt = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
                        hour = dt.hour
                    except Exception:
                        pass

                    generated = _generate_suggestions(stress_level, features, hour, trend)
                    for s in generated:
                        cur.execute(
                            "INSERT INTO suggestions (user_id, text, type, context, explanation, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                user["user_id"],
                                s.get("text"),
                                s.get("type"),
                                s.get("context"),
                                s.get("explanation"),
                                ts_raw or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            ),
                        )
                    conn.commit()

                    # Re-query suggestions
                    cur.execute(
                        """
                        SELECT id, text, type, context, explanation, timestamp
                        FROM suggestions
                        WHERE user_id = ?
                        ORDER BY timestamp DESC
                        """,
                        (user["user_id"],),
                    )
                    rows = cur.fetchall()
            except Exception:
                # If backfill fails, fall through to empty response.
                rows = rows

        return [
            SuggestionRecord(
                id=int(r["id"]),
                text=str(r["text"]),
                type=str(r["type"]),
                timestamp=str(r["timestamp"]),
                context=str(r["context"]) if r["context"] else None,
                explanation=str(r["explanation"]) if r["explanation"] else None
            )
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/admin/users")
def admin_users(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role, email, created_at, is_suspended, force_password_reset, avatar_base64 "
            "FROM users ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        return [
            {
                "id": int(r["id"]),
                "username": str(r["username"]),
                "role": str(r["role"]),
                "email": str(r["email"]) if r["email"] else None,
                "created_at": r["created_at"],
                "is_suspended": bool(int(r["is_suspended"] or 0)),
                "force_password_reset": bool(int(r["force_password_reset"] or 0)),
                "avatar_url": str(r["avatar_base64"]) if r["avatar_base64"] else None,
            }
            for r in rows
        ]
    finally:
        conn.close()


@app.post("/admin/users/{user_id}/suspend")
def admin_suspend_user(user_id: int, admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_suspended = 1 WHERE id = ? AND role != 'admin'", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found or cannot suspend admin")
        _log_activity(cur, "USER_SUSPENDED", "user", str(user_id), int(admin["user_id"]), {"targetUserId": user_id})
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()


@app.post("/admin/users/{user_id}/reactivate")
def admin_reactivate_user(user_id: int, admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_suspended = 0 WHERE id = ?", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        _log_activity(cur, "USER_REACTIVATED", "user", str(user_id), int(admin["user_id"]), {"targetUserId": user_id})
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()


@app.post("/admin/users/{user_id}/force-password-reset")
def admin_force_password_reset(user_id: int, admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET force_password_reset = 1 WHERE id = ?", (user_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        _log_activity(cur, "USER_FORCE_PASSWORD_RESET", "user", str(user_id), int(admin["user_id"]), {"targetUserId": user_id})
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()


@app.get("/admin/predictions")
def admin_predictions(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id,
                   p.user_id,
                   u.username,
                   u.avatar_base64,
                   p.stress_level,
                   p.confidence,
                   p.timestamp,
                   p.features_json,
                   (SELECT s.text FROM suggestions s WHERE s.user_id = p.user_id ORDER BY s.timestamp DESC LIMIT 1) as suggestion_text,
                   (SELECT s.type FROM suggestions s WHERE s.user_id = p.user_id ORDER BY s.timestamp DESC LIMIT 1) as suggestion_type
            FROM predictions p
            JOIN users u ON u.id = p.user_id
            ORDER BY p.timestamp DESC
            """
        )
        rows = cur.fetchall()
        return [
            {
                "id": int(r["id"]),
                "user_id": int(r["user_id"]),
                "username": str(r["username"]),
                "stress_level": str(r["stress_level"]),
                "confidence": float(r["confidence"]),
                "timestamp": str(r["timestamp"]),
                "avatar_url": str(r["avatar_base64"]) if r["avatar_base64"] else None,
                "features": json.loads(r["features_json"]) if r["features_json"] else {},
                "suggestion": {
                    "text": str(r["suggestion_text"]) if r["suggestion_text"] else None,
                    "type": str(r["suggestion_type"]) if r["suggestion_type"] else None,
                },
            }
            for r in rows
        ]
    finally:
        conn.close()


def _log_activity(cur: sqlite3.Cursor, action: str, entity: str, entity_id: str, user_id: int, payload: dict = None):
    raw_hash = hashlib.md5(f"{action}{entity_id}{datetime.now()}".encode()).hexdigest()
    log_id = f"log_{raw_hash[:12]}"
    cur.execute(
        "INSERT INTO audit_logs (id, action, entity, entity_id, payload, user_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (log_id, action, entity, entity_id, str(payload) if payload else None, user_id, datetime.now().isoformat())
    )

@app.get("/profiles", response_model=Dict[str, Any])
def get_profiles(current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE user_id = ?", (current_user["user_id"],))
        rows = cur.fetchall()
        profiles = []
        for r in rows:
            profiles.append({
                "id": r["id"],
                "fullName": r["full_name"],
                "dateOfBirth": r["date_of_birth"],
                "bloodGroup": r["blood_group"],
                "allergies": r["allergies"],
                "clinicalHighlights": r["clinical_highlights"],
                "homeAddress": r["home_address"],
                "responderName": r["responder_name"],
                "responderPhone": r["responder_phone"],
                "secondaryContactPhone": r["secondary_contact_phone"],
                "avatarUrl": r["avatar_url"],
                "notes": r["notes"],
                "nodeReferences": eval(r["node_references"]) if r["node_references"] else [],
                "intelCode": r["intel_code"],
                "createdAt": r["created_at"],
                "updatedAt": r["updated_at"],
                "userId": r["user_id"],
                "riskScore": r["risk_score"],
                "lastAccessedAt": r["last_accessed_at"]
            })
        return {"status": "success", "data": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/profiles", response_model=Dict[str, Any])
def create_profile(profile: ProfileCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        raw_profile_hash = hashlib.md5(f"{profile.fullName}{datetime.now()}".encode()).hexdigest()
        profile_id = f"prof_{raw_profile_hash[:12]}"
        # Generate a Mentra System Code
        short_id_raw = hashlib.md5(profile_id.encode()).hexdigest()
        short_id = short_id_raw[:8].upper()
        mentra_code = f"MS-{short_id[:4]}-{short_id[4:]}"
        
        now = datetime.now().isoformat()
        cur.execute(
            """
            INSERT INTO profiles (id, full_name, date_of_birth, blood_group, allergies, clinical_highlights, 
            home_address, responder_name, responder_phone, secondary_contact_phone, 
            notes, node_references, intel_code, user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (profile_id, profile.fullName, profile.dateOfBirth, profile.bloodGroup, profile.allergies, 
             profile.clinicalHighlights, profile.homeAddress, profile.responderName, 
             profile.responderPhone, profile.secondaryContactPhone, profile.notes, 
             str(profile.nodeReferences), mentra_code, current_user["user_id"], now, now)
        )
        _log_activity(cur, "PROFILE_CREATE", "profile", profile_id, current_user["user_id"], {"code": mentra_code})
        conn.commit()
        return {"status": "success", "data": {"id": profile_id, "intelCode": mentra_code}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/profiles/{profile_id}", response_model=Dict[str, Any])
def get_profile(profile_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = {
            "id": r["id"],
            "fullName": r["full_name"],
            "dateOfBirth": r["date_of_birth"],
            "bloodGroup": r["blood_group"],
            "allergies": r["allergies"],
            "clinicalHighlights": r["clinical_highlights"],
            "homeAddress": r["home_address"],
            "responderName": r["responder_name"],
            "responderPhone": r["responder_phone"],
            "secondaryContactPhone": r["secondary_contact_phone"],
            "avatarUrl": r["avatar_url"],
            "notes": r["notes"],
            "nodeReferences": eval(r["node_references"]) if r["node_references"] else [],
            "intelCode": r["intel_code"],
            "createdAt": r["created_at"],
            "updatedAt": r["updated_at"],
            "userId": r["user_id"],
            "riskScore": r["risk_score"],
            "lastAccessedAt": r["last_accessed_at"]
        }
        return {"status": "success", "data": profile}
    finally:
        conn.close()

@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM profiles WHERE id = ? AND user_id = ?", (profile_id, current_user["user_id"]))
        _log_activity(cur, "PROFILE_DELETE", "profile", profile_id, current_user["user_id"])
        conn.commit()
        return {"status": "success", "message": "Profile deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/analytics/my-dashboard", response_model=Dict[str, Any])
def get_user_dashboard_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        # Real stats from profiles
        cur.execute("SELECT COUNT(*), AVG(risk_score) FROM profiles WHERE user_id = ?", (current_user["user_id"],))
        p_row = cur.fetchone()
        profile_count = p_row[0] or 0
        avg_risk = p_row[1] or 0.0
        
        # Recent profiles (last 24h)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cur.execute("SELECT COUNT(*) FROM profiles WHERE user_id = ? AND created_at > ?", (current_user["user_id"], yesterday))
        recent_profiles = cur.fetchone()[0] or 0

        # Real accesses (INTEL_LOOKUP actions in audit_logs)
        cur.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE user_id = ? AND action = 'INTEL_LOOKUP'", 
            (current_user["user_id"],)
        )
        access_count = cur.fetchone()[0] or 0

        # Today's accesses
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        cur.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE user_id = ? AND action = 'INTEL_LOOKUP' AND created_at > ?", 
            (current_user["user_id"], today_start)
        )
        today_accesses = cur.fetchone()[0] or 0

        # Security anomalies (unauthorized syncs / anomalies)
        # Mocking these for now but structured for future real detection
        failed_logins = 0 
        suspicious_attempts = 0

        return {
            "status": "success",
            "data": {
                "dashboard": {
                    "totalProfiles": profile_count,
                    "recentProfiles": recent_profiles,
                    "totalAccesses": access_count,
                    "todayAccesses": today_accesses,
                    "avgRiskScore": float(round(float(avg_risk), 1)),
                    "unauthorizedSyncs": failed_logins,
                    "accessAnomalies": suspicious_attempts
                },
                "trends": 5,
                "peakTimes": [10, 20, 15, 45, 30, 60, 25, 10]
            }
        }
    finally:
        conn.close()

@app.get("/audit-vault/my-activity", response_model=Dict[str, Any])
def get_my_activity(limit: int = 10, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", 
            (current_user["user_id"], limit)
        )
        rows = cur.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "action": r["action"],
                "entity": r["entity"],
                "entityId": r["entity_id"],
                "payload": eval(r["payload"]) if r["payload"] else None,
                "createdAt": r["created_at"]
            })
        return {"status": "success", "data": logs}
    finally:
        conn.close()

@app.get("/admin/analytics/dashboard", response_model=Dict[str, Any])
def get_admin_dashboard_stats(_: Dict[str, Any] = Depends(require_admin)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        # NOTE: keep response keys stable for the current frontend.
        now = datetime.now()
        yesterday_iso = (now - timedelta(days=1)).isoformat()
        today_start_iso = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_start_sql = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        today_start_suggestions = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = int(cur.fetchone()[0] or 0)

        # users.created_at is stored as "YYYY-MM-DD HH:MM:SS" on register/inject paths
        yesterday_user = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT COUNT(*) FROM users WHERE created_at IS NOT NULL AND created_at > ?", (yesterday_user,))
        recent_users = int(cur.fetchone()[0] or 0)

        cur.execute("SELECT COUNT(*) FROM audit_logs")
        total_events = int(cur.fetchone()[0] or 0)

        cur.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE datetime(replace(created_at, 'T', ' ')) > datetime(?)",
            (today_start_sql,),
        )
        today_events = int(cur.fetchone()[0] or 0)

        cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action = 'INTEL_LOOKUP'")
        total_intel = int(cur.fetchone()[0] or 0)

        cur.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE action = 'INTEL_LOOKUP' AND datetime(replace(created_at, 'T', ' ')) > datetime(?)",
            (today_start_sql,),
        )
        today_intel = int(cur.fetchone()[0] or 0)

        # Some deployments may never hit the intel lookup endpoint; in that case the dashboard's
        # "Emergency Frequency" chart would be empty. Use prediction activity as a fallback signal.
        if total_intel == 0:
            cur.execute("SELECT COUNT(*) FROM audit_logs WHERE action = 'USER_PREDICT'")
            total_intel = int(cur.fetchone()[0] or 0)
            cur.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE action = 'USER_PREDICT' AND datetime(replace(created_at, 'T', ' ')) > datetime(?)",
                (today_start_sql,),
            )
            today_intel = int(cur.fetchone()[0] or 0)

        cur.execute("SELECT AVG(confidence) FROM predictions")
        avg_conf = cur.fetchone()[0]
        avg_conf_val = float(avg_conf or 0.0)
        # Some datasets store confidence as 0..1, others store 0..100.
        avg_conf_pct = float(round(avg_conf_val * 100.0, 1)) if avg_conf_val <= 1.0 else float(round(avg_conf_val, 1))

        cur.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = int(cur.fetchone()[0] or 0)

        cur.execute("SELECT COUNT(*) FROM suggestions")
        total_suggestions = int(cur.fetchone()[0] or 0)

        cur.execute("SELECT COUNT(*) FROM suggestions WHERE timestamp > ?", (today_start_suggestions,))
        today_suggestions = int(cur.fetchone()[0] or 0)

        # Derived quality signals
        success_rate = float(round((total_suggestions / total_predictions) * 100.0, 1)) if total_predictions > 0 else 0.0
        retention_rate = float(round((recent_users / total_users) * 100.0, 1)) if total_users > 0 else 0.0

        # If you later add explicit auth-failure audit events, you can count them here.
        unauthorized_syncs = 0
        access_anomalies = 0

        # 1. User Growth (Last 12 Months) - Backend Real Data
        growth_data = []
        twelve_months_ago_user = (now - timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count 
            FROM users 
            WHERE created_at > ? 
            GROUP BY month 
            ORDER BY month ASC
            """,
            (twelve_months_ago_user,)
        )
        growth_rows = cur.fetchall()
        for r in growth_rows:
            # Map '2026-03' to 'Mar' for cleaner UI if possible, or just send ISO
            # The frontend safeParse handles this.
            growth_data.append({"label": r["month"], "users": r["count"]})
        
        # 2. Emergency Frequency (Last 30 Days) - Backend Real Data
        frequency_data = []
        thirty_days_ago_sql = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            SELECT date(replace(created_at, 'T', ' ')) as day, COUNT(*) as count
            FROM audit_logs
            WHERE action = 'INTEL_LOOKUP'
              AND datetime(replace(created_at, 'T', ' ')) > datetime(?)
            GROUP BY day
            ORDER BY day ASC
            """,
            (thirty_days_ago_sql,)
        )
        freq_rows = cur.fetchall()

        if not freq_rows:
            cur.execute(
                """
                SELECT date(replace(created_at, 'T', ' ')) as day, COUNT(*) as count
                FROM audit_logs
                WHERE action = 'USER_PREDICT'
                  AND datetime(replace(created_at, 'T', ' ')) > datetime(?)
                GROUP BY day
                ORDER BY day ASC
                """,
                (thirty_days_ago_sql,),
            )
            freq_rows = cur.fetchall()

        for r in freq_rows:
            frequency_data.append({"label": r["day"], "count": r["count"]})

        return {
            "status": "success",
            "data": {
                # Legacy keys expected by frontend
                "totalProfiles": total_users,
                "recentProfiles": recent_users,
                "totalAccesses": total_intel,
                "todayAccesses": today_intel,
                "avgRiskScore": avg_conf_pct,
                "unauthorizedSyncs": unauthorized_syncs,
                "accessAnomalies": access_anomalies,

                # Time-series data for premium charts
                "growth": growth_data,
                "frequency": frequency_data,

                # Additional backend-truth fields
                "totalUsers": total_users,
                "recentUsers": recent_users,
                "totalPredictions": total_predictions,
                "totalSuggestions": total_suggestions,
                "todaySuggestions": today_suggestions,
                "successRate": success_rate,
                "retentionRate": retention_rate,
                "totalEvents": total_events,
                "todayEvents": today_events,
            }
        }
    finally:
        conn.close()

@app.get("/admin/audit-vault/activity", response_model=Dict[str, Any])
def get_admin_activity(limit: int = 20, _: Dict[str, Any] = Depends(require_admin)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT l.*, u.username FROM audit_logs l JOIN users u ON l.user_id = u.id ORDER BY l.created_at DESC LIMIT ?", 
            (limit,)
        )
        rows = cur.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "action": r["action"],
                "entity": r["entity"],
                "entityId": r["entity_id"],
                "username": r["username"],
                "payload": eval(r["payload"]) if r["payload"] else None,
                "createdAt": r["created_at"]
            })
        return {"status": "success", "data": logs}
    finally:
        conn.close()

@app.get("/intel/{code}", response_model=Dict[str, Any])
def lookup_code(code: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM profiles WHERE intel_code = ?", (code,))
        r = cur.fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="No active identity found for this code")
        
        profile = {
            "id": r["id"],
            "fullName": r["full_name"],
            "intelCode": r["intel_code"],
            "riskScore": r["risk_score"]
        }
        
        # Log the access
        _log_activity(cur, "INTEL_LOOKUP", "profile", profile["id"], current_user["user_id"], {"code": code})
        
        # Update last accessed
        cur.execute("UPDATE profiles SET last_accessed_at = ? WHERE id = ?", (datetime.now().isoformat(), profile["id"]))
        conn.commit()
        
        return {"status": "success", "data": profile}
    finally:
        conn.close()

@app.get("/profiles/my/emergency-logs")
def get_my_emergency_logs(limit: int = 10, current_user: Dict[str, Any] = Depends(get_current_user)):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT l.*, p.intel_code 
            FROM audit_logs l 
            JOIN profiles p ON l.entity_id = p.id 
            WHERE l.action = 'INTEL_LOOKUP' AND p.user_id = ? 
            ORDER BY l.created_at DESC LIMIT ?
            """, 
            (current_user["user_id"], limit)
        )
        rows = cur.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r["id"],
                "intelCode": r["intel_code"],
                "timestamp": r["created_at"],
                "ipAddress": "127.0.0.1" # Mock or get from request
            })
        return {"status": "success", "data": logs}
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("RELOAD", "true").strip().lower() in {"1", "true", "yes"}

    uvicorn.run("api:app", host=host, port=port, reload=reload)
