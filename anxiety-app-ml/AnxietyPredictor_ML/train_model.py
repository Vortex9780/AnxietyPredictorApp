# train_model.py  (notes-aware)
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor

# --- sentiment: use simple lexicon only (no external deps) ---
_VADER = None  # explicitly disabled

DATA_PATH = Path("data/checkins.csv")   # optional; we synthesize if missing
MODEL_PATH = Path("anxiety_model.pkl")
RNG = np.random.default_rng(42)

BASE_NUMERIC = ["sleep", "energy", "mood", "anxiety_7d_avg"]
NOTE_NUMERIC = ["notes_len", "notes_words", "notes_sentiment"]
NOTE_KEYWORDS = ["kw_work", "kw_school", "kw_exam", "kw_sleep", "kw_social", "kw_finance", "kw_health"]
NUMERIC_FEATURES = BASE_NUMERIC + NOTE_NUMERIC + NOTE_KEYWORDS
TRIGGER_FEATURES = ["triggers"]  # one-hot

# -------- helpers for notes ----------
_POS = {"calm","better","rested","relaxed","improved","ok","good","great"}
_NEG = {"anxious","panic","stressed","overwhelmed","tired","exhausted","worried","nervous","insomnia"}

def _simple_sentiment(text: str) -> float:
    if not text:
        return 0.0
    words = {w.strip(".,!?").lower() for w in text.split()}
    score = 0
    score += sum(1 for w in words if w in _POS)
    score -= sum(1 for w in words if w in _NEG)
    # squash to roughly [-1,1]
    return max(-1.0, min(1.0, score / 5.0))

def notes_featurize(text: str) -> dict:
    t = (text or "").strip()
    toks = [w for w in t.split() if w]
    sent = _simple_sentiment(t)
    feats = {
        "notes_len": float(len(t)),
        "notes_words": float(len(toks)),
        "notes_sentiment": float(sent),
    }
    low = t.lower()
    feats["kw_work"]    = 1.0 if "work" in low else 0.0
    feats["kw_school"]  = 1.0 if "school" in low or "class" in low else 0.0
    feats["kw_exam"]    = 1.0 if "exam" in low or "test" in low or "deadline" in low else 0.0
    feats["kw_sleep"]   = 1.0 if "sleep" in low or "insomnia" in low else 0.0
    feats["kw_social"]  = 1.0 if "social" in low or "party" in low or "crowd" in low else 0.0
    feats["kw_finance"] = 1.0 if "money" in low or "rent" in low or "bills" in low else 0.0
    feats["kw_health"]  = 1.0 if "health" in low or "sick" in low or "doctor" in low else 0.0
    return feats

# ------------- load/synthesize -------------
def load_dataset() -> pd.DataFrame:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        print(f"[train] Loaded {DATA_PATH} shape={df.shape}")
        if "notes" not in df.columns:
            df["notes"] = ""
        return df

    print("[train] No CSV found. Generating synthetic data…")
    n = 1000
    ts = pd.date_range("2025-01-01", periods=n, freq="h")
    pool = ["Work","Social","Sleep deprivation","Caffeine","Noise","Crowds","None"]
    df = pd.DataFrame({
        "user_id": RNG.integers(1, 8, size=n),
        "timestamp": ts.astype(str),
        "sleep": np.clip(RNG.normal(6.5, 1.2, n), 3, 10),
        "energy": np.clip(RNG.normal(5.0, 2.0, n), 0, 10),
        "mood":   np.clip(RNG.normal(5.0, 2.0, n), 0, 10),
        "anxiety_7d_avg": np.clip(RNG.normal(4.5, 1.0, n), 0, 10),
    })
    trig = RNG.choice(pool, size=n)
    df["triggers"] = trig

    # simple synthetic notes correlated with triggers/mood
    notes_bank = [
        "Felt anxious at work today",
        "Did a short walk and felt better",
        "Social plans made me nervous",
        "Exam coming up next week",
        "Could not sleep well, insomnia",
        "Feeling calm and rested",
        "Money stress rising",
        "Health check tomorrow",
        "Crowded place was stressful",
        "Normal day, mood ok",
    ]
    df["notes"] = RNG.choice(notes_bank, size=n)

    noise = RNG.normal(0, 0.6, n)
    df["anxiety"] = np.clip(
        0.5 * (10 - df["sleep"]) +
        0.35 * (10 - df["mood"]) +
        0.25 * (10 - df["energy"]) +
        0.55 * df["anxiety_7d_avg"] +
        0.8 * (trig == "Sleep deprivation").astype(float) +
        0.5 * (trig == "Work").astype(float) +
        0.3 * (trig == "Crowds").astype(float) +
        0.3 * (df["notes"].str.contains("insomnia|nervous|anxious|stress", case=False)).astype(float) +
        noise,
        0, 10
    )
    print(f"[train] Synthetic shape={df.shape}")
    return df

# ------------- clean & featurize -------------
def clean(df: pd.DataFrame) -> pd.DataFrame:
    for c in BASE_NUMERIC:
        if c not in df.columns:
            df[c] = 0.0
    if "triggers" not in df.columns:
        df["triggers"] = ""
    if "notes" not in df.columns:
        df["notes"] = ""

    for c in BASE_NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    def to_str(x):
        if isinstance(x, list):
            return ",".join(map(str, x))
        return "" if pd.isna(x) else str(x)
    df["triggers"] = df["triggers"].apply(to_str)
    df["notes"] = df["notes"].apply(lambda x: "" if pd.isna(x) else str(x))

    # derive note features
    nf = df["notes"].apply(notes_featurize).apply(pd.Series)
    for col in NOTE_NUMERIC + NOTE_KEYWORDS:
        if col not in nf.columns:
            nf[col] = 0.0
    df = pd.concat([df, nf], axis=1)

    if "anxiety" not in df.columns:
        raise ValueError("Missing target column 'anxiety'.")
    df["anxiety"] = pd.to_numeric(df["anxiety"], errors="coerce").fillna(0.0)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce").fillna(pd.Timestamp.utcnow())
    return df

# ------------- splitting with fallbacks -------------
def split_data(df: pd.DataFrame):
    X = df[NUMERIC_FEATURES + TRIGGER_FEATURES].copy()
    y = df["anxiety"].values

    if "user_id" in df.columns:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        for tr, te in gss.split(X, y, groups=df["user_id"]):
            if len(te) > 0:
                print("[train] Split: GroupShuffleSplit(user_id)")
                return X.iloc[tr], X.iloc[te], y[tr], y[te]

    if "timestamp" in df.columns:
        df2 = df.sort_values("timestamp")
        X2, y2 = df2[NUMERIC_FEATURES + TRIGGER_FEATURES], df2["anxiety"].values
        n = len(df2); te = max(1, int(0.2 * n))
        if n - te > 0:
            print("[train] Split: time-based (last 20%)")
            return X2.iloc[: n - te], X2.iloc[n - te :], y2[: n - te], y2[n - te :]

    try:
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        if len(y_te) > 0:
            print("[train] Split: random")
            return X_tr, X_te, y_tr, y_te
    except Exception:
        pass

    n = len(X); te = max(1, int(0.2 * n))
    if n - te <= 0:
        raise RuntimeError("Not enough rows to split dataset.")
    print("[train] Split: manual slice fallback")
    return X.iloc[: n - te], X.iloc[n - te :], y[: n - te], y[n - te :]

# ------------- pipeline & train -------------
def build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            ("trg", OneHotEncoder(handle_unknown="ignore"), TRIGGER_FEATURES),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )
    model = GradientBoostingRegressor(random_state=42)
    return Pipeline([("pre", pre), ("model", model)])

def main():
    df = load_dataset()
    df = clean(df)
    X_tr, X_te, y_tr, y_te = split_data(df)

    pipe = build_pipeline()
    print(f"[train] Fitting on {len(y_tr)} rows; testing on {len(y_te)} rows…")
    pipe.fit(X_tr, y_tr)

    preds = pipe.predict(X_te)
    mae  = mean_absolute_error(y_te, preds)
    rmse = np.sqrt(mean_squared_error(y_te, preds))
    r2   = r2_score(y_te, preds)
    print(f"[train] MAE={mae:.3f}  RMSE={rmse:.3f}  R2={r2:.3f}")

    bundle = {
        "pipeline": pipe,
        "numeric_features": NUMERIC_FEATURES,
        "trigger_features": TRIGGER_FEATURES,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "n_train": int(len(y_tr)),
        "n_test": int(len(y_te)),
        "metrics": {"mae": float(mae), "rmse": float(rmse), "r2": float(r2)},
        "version": "1.3.0-notes",
    }
    joblib.dump(bundle, MODEL_PATH.as_posix())
    print(f"[train] Saved → {MODEL_PATH.resolve()}")
    chk = joblib.load(MODEL_PATH.as_posix())
    print("[train] Reload OK. Keys:", sorted(chk.keys()))

if __name__ == "__main__":
    main()