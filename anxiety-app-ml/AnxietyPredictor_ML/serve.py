# serve.py
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union, Optional
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
# VADER disabled to avoid dependency issues; use simple lexicon instead
_VADER = None


_POS = {"calm","better","rested","relaxed","improved","ok","good","great"}
_NEG = {"anxious","panic","stressed","overwhelmed","tired","exhausted","worried","nervous","insomnia"}

# --- Notes sentiment and featurization helpers ---
def _simple_sentiment(text: str) -> float:
    if not text:
        return 0.0
    words = {w.strip(".,!?").lower() for w in text.split()}
    score = 0
    score += sum(1 for w in words if w in _POS)
    score -= sum(1 for w in words if w in _NEG)
    return max(-1.0, min(1.0, score / 5.0))

def notes_featurize(text: str) -> dict:
    t = (text or "").strip()
    toks = [w for w in t.split() if w]
    sent = _simple_sentiment(t)
    low = t.lower()
    feats = {
        "notes_len": float(len(t)),
        "notes_words": float(len(toks)),
        "notes_sentiment": float(sent),
        "kw_work":    1.0 if "work" in low else 0.0,
        "kw_school":  1.0 if ("school" in low or "class" in low) else 0.0,
        "kw_exam":    1.0 if ("exam" in low or "test" in low or "deadline" in low) else 0.0,
        "kw_sleep":   1.0 if ("sleep" in low or "insomnia" in low) else 0.0,
        "kw_social":  1.0 if ("social" in low or "party" in low or "crowd" in low) else 0.0,
        "kw_finance": 1.0 if ("money" in low or "rent" in low or "bills" in low) else 0.0,
        "kw_health":  1.0 if ("health" in low or "sick" in low or "doctor" in low) else 0.0,
    }
    return feats

app = FastAPI(title="Anxiety Predictor API")
print(">>> Loading serve.py from", __file__)

# (Optional) CORS for debugging from other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}


# --- Debug helpers ----------------------------------------------------------
@app.on_event("startup")
async def _show_routes():
    print(">>> Routes loaded:", [route.path for route in app.routes])

@app.get("/")
def root():
    return {"ok": True, "routes": [r.path for r in app.routes]}

# --- Load model bundle -------------------------------------------------------
MODEL_PATH = Path("anxiety_model.pkl")
if not MODEL_PATH.exists():
    raise RuntimeError(f"Model file not found at {MODEL_PATH}. Run train_model.py first.")

bundle = joblib.load(MODEL_PATH.as_posix())
pipeline = bundle.get("pipeline")
if pipeline is None:
    raise RuntimeError("Model bundle is missing 'pipeline'. Did training succeed?")

# Accept both old and new key names
numeric_features = (
    bundle.get("numeric_features")
    or bundle.get("numeric")
    or ["sleep", "energy", "mood", "anxiety_7d_avg"]
)
trigger_features = (
    bundle.get("trigger_features")
    or bundle.get("trigger_cols")
    or ["triggers"]  # default to a single string column if unknown
)

# --- Debug: show loaded bundle details ---
print(">>> Loaded model bundle:", MODEL_PATH.resolve())
print(">>> Numeric features:", numeric_features)
print(">>> Trigger features:", trigger_features)
print(">>> Metrics:", bundle.get("metrics"))

# Convenience: which cyclical extras are requested by the model (if any)
USE_DOW_SIN = "dow_sin" in numeric_features
USE_DOW_COS = "dow_cos" in numeric_features
USE_HOUR_SIN = "hour_sin" in numeric_features
USE_HOUR_COS = "hour_cos" in numeric_features

# --- Request model -----------------------------------------------------------
class CheckInEntry(BaseModel):
    sleep: float
    energy: float
    mood: float
    anxiety_7d_avg: float
    triggers: Union[str, List[str]]
    timestamp: str  # ISO format like "2025-08-01T10:12:00Z"
    notes: Optional[str] = ""

def build_feature_row(entry: CheckInEntry) -> dict:
    # Parse timestamp and compute cyclical features ONLY if the model expects them
    try:
        dt = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
    except Exception as e:
        raise ValueError(f"Invalid timestamp format: {entry.timestamp}") from e

    row: dict = {}

    # Base numeric features expected by the model
    # Invert mood: UI sends valence (0 good..10 good), model expects distress (0 good..10 bad)
    base_map = {
        "sleep": float(entry.sleep),
        "energy": float(entry.energy),
        "mood": float(10.0 - float(entry.mood)),  # inverted here
        "anxiety_7d_avg": float(entry.anxiety_7d_avg),
    }
    for nf in ["sleep", "energy", "mood", "anxiety_7d_avg"]:
        if nf in numeric_features:
            row[nf] = base_map[nf]

    # Also expose raw hour / is_weekend if the trained pipeline expects them
    hour = dt.hour
    is_weekend = 1 if dt.weekday() >= 5 else 0
    if "hour" in numeric_features:
        row["hour"] = float(hour)
    if "is_weekend" in numeric_features:
        row["is_weekend"] = float(is_weekend)

    # Cyclical, only if requested
    if USE_DOW_SIN or USE_DOW_COS:
        dow = dt.weekday()  # 0=Mon
        if USE_DOW_SIN:
            row["dow_sin"] = float(np.sin(2 * np.pi * dow / 7))
        if USE_DOW_COS:
            row["dow_cos"] = float(np.cos(2 * np.pi * dow / 7))
    if USE_HOUR_SIN or USE_HOUR_COS:
        hour = dt.hour
        if USE_HOUR_SIN:
            row["hour_sin"] = float(np.sin(2 * np.pi * hour / 24))
        if USE_HOUR_COS:
            row["hour_cos"] = float(np.cos(2 * np.pi * hour / 24))

    # Triggers handling:
    # - If the model expects a single 'triggers' column, send a comma-joined string.
    # - If it expects pre-expanded 'trigger_*' columns, set 1/0 accordingly.
    if "triggers" in trigger_features:
        trig_str = (
            ",".join(entry.triggers) if isinstance(entry.triggers, list)
            else str(entry.triggers or "")
        )
        row["triggers"] = trig_str
    else:
        # Pre-expanded binary columns
        trig_list = (
            [t.strip().lower() for t in entry.triggers] if isinstance(entry.triggers, list)
            else [x.strip().lower() for x in str(entry.triggers or "").split(",") if x.strip()]
        )
        for tf in trigger_features:
            if tf.startswith("trigger_"):
                base = tf.replace("trigger_", "").lower()
                row[tf] = 1 if base in trig_list else 0

    # Notes-derived features, add only if the trained model expects them
    note_feats = notes_featurize(getattr(entry, "notes", "") or "")
    for k, v in note_feats.items():
        if k in numeric_features:  # include only features present in the model bundle
            row[k] = float(v)

    # Compatibility: if model expects `notes_sent`, map from our `notes_sentiment`
    if "notes_sent" in numeric_features and "notes_sentiment" in note_feats:
        row["notes_sent"] = float(note_feats["notes_sentiment"])

    # Ensure every expected feature column exists (fill with sane defaults)
    expected_cols = set(numeric_features) | set(trigger_features)
    for col in expected_cols:
        if col not in row:
            row[col] = "" if col == "triggers" else 0.0

    return row

# --- Endpoint ----------------------------------------------------------------
@app.post("/predict")
def predict(entry: CheckInEntry):
    try:
        feature_row = build_feature_row(entry)
        df = pd.DataFrame([feature_row])

        raw = float(pipeline.predict(df)[0])          # raw model output
        clamped = float(np.clip(raw, 0.0, 10.0))      # clamp to [0, 10]
        rounded = float(np.round(clamped, 1))         # round to 1 decimal

        # Debug (optional): comment these out later
        print("PREDICT_IN:", feature_row, flush=True)
        print("PREDICT_RAW:", raw, "CLAMPED:", clamped, "ROUNDED:", rounded, flush=True)

        return {"predicted_anxiety": rounded}
    except Exception as e:
        print("Prediction error:", e, flush=True)
        raise HTTPException(status_code=400, detail=str(e))