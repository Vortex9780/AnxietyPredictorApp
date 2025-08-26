# tip_proxy.py

import os
import re
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

app = FastAPI(title="Local Tip Proxy")

# --- health + ping endpoints (for curl checks) ---
@app.get("/")
def root():
    return {"ok": True, "service": "tips-proxy"}

@app.get("/health")
def health():
    return {"ok": True}

# Simple in-memory API key guard (change to something secret)
VALID_CLIENT_KEY = "local_secret_key_123"  # use a random string here

# Load model once globally (this can take a few seconds first time)
MODEL_NAME = "google/flan-t5-small"

print("Loading local model:", MODEL_NAME)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
generator = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    device=-1,  # CPU; change to 0 if you have a GPU and torch detects it
)

class TipRequest(BaseModel):
    predicted_anxiety: float
    sleep: float
    energy: float
    mood: float
    triggers: list[str]
    weeklyTrend: dict  # e.g., {"Mon":5,"Tue":4,...}


def build_prompt(req: TipRequest) -> str:
    weekly = ", ".join(f"{day}:{score}" for day, score in req.weeklyTrend.items())
    examples = """
Example 1:
Anxiety: 2/10; Sleep: 8h; Energy: 7/10; Mood: 6/10; Triggers: Social; Trend: Mon:3, Tue:4, Wed:3, Thu:2, Fri:3, Sat:2, Sun:3.
Tip: Keep up the routine and schedule a short mindfulness break on days anxiety tends to rise.

Example 2:
Anxiety: 8/10; Sleep: 4h; Energy: 3/10; Mood: 2/10; Triggers: Work, Deadline pressure; Trend: Mon:7, Tue:8, Wed:7, Thu:6, Fri:7, Sat:5, Sun:4.
Tip: Break your work into 25-minute focused sprints with 5-minute breaks to reduce overwhelm.

Example 3:
Anxiety: 5/10; Sleep: 6h; Energy: 5/10; Mood: 4/10; Triggers: Uncertainty; Trend: Mon:5, Tue:5, Wed:6, Thu:5, Fri:4, Sat:4, Sun:5.
Tip: Write down the top three uncertainties and identify one small action to address each.
"""
    instruction = (
        "You are a mental health coach. Based on the latest check-in and weekly anxiety trend, "
        "provide three distinct, concise, actionable tips (1 sentence each) tailored to their current state. "
        "Avoid generic or self-referential statements. Format as a numbered list."
    )
    latest = (
        f"Anxiety: {req.predicted_anxiety}/10; Sleep: {req.sleep}h; Energy: {req.energy}/10; "
        f"Mood: {req.mood}/10; Triggers: {', '.join(req.triggers)}; Trend: {weekly}."
    )
    # Force the list format to start so the model knows to output numbered tips
    return f"{instruction}\n{examples}\nLatest → {latest}\nTips:\n1."

def select_best_tips(raw_outputs: list[str]) -> list[str]:
    tips = []
    seen = set()
    verbs = [
        "try", "take", "do", "journal", "walk", "breathe", "reflect", "plan",
        "schedule", "pause", "break", "focus", "stretch", "meditate"
    ]
    for t in raw_outputs:
        clean = t.strip()
        for line in clean.splitlines():
            line = line.strip()
            if not line:
                continue
            # remove leading numbering or bullets like "1." or "2)"
            line = re.sub(r'^[0-9]+[\.)]\s*', '', line)
            low = line.lower()
            # degenerate filters
            trend_echo = re.fullmatch(r'(tips?:\s*)?((mon|tue|wed|thu|fri|sat|sun):\d[\s,]*)+', low)
            if trend_echo:
                continue
            # skip direct echo of the input summary (contains those key metrics)
            if (re.search(r'anxiety:', line, re.IGNORECASE)
                    and re.search(r'sleep:', line, re.IGNORECASE)
                    and re.search(r'mood:', line, re.IGNORECASE)):
                continue
            # if it starts with "tips:" without any action verb, skip
            if low.startswith("tips:") and not any(verb in low for verb in verbs):
                continue
            if len(line.split()) < 5:
                continue
            if low in seen:
                continue
            seen.add(low)
            tips.append(line)
            if len(tips) >= 3:
                return tips
    return tips

@app.post("/get-tip")
def get_tip(req: TipRequest, request: Request):
    api_key = request.headers.get("x-api-key", "")
    if api_key != VALID_CLIENT_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    prompt = build_prompt(req)
    try:
        out = generator(
            prompt,
            max_length=120,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.2,
            num_return_sequences=3,
            early_stopping=True,
        )
        raw_texts = [entry.get("generated_text", "") for entry in out]
        selected = select_best_tips(raw_texts)
        if not selected:
            raise ValueError("Degenerate or no valid tips from model")
        tip_text = "\n".join(selected[:3])
    except Exception as e:
        print("Model generation fallback due to:", e)
        if req.predicted_anxiety >= 7:
            fallback = [
                "Take 5 deep breaths and go for a short walk to reduce immediate stress.",
                "Try a grounding exercise: name 5 things you can see, 4 you can touch.",
                "Limit screen time for 30 minutes to lower cognitive overload."
            ]
        elif req.predicted_anxiety >= 4:
            fallback = [
                "Write down one worry and schedule a 10-minute worry window later.",
                "Journal for 5 minutes to externalize anxious thoughts.",
                "Set a small achievable goal for the next hour to regain control."
            ]
        else:
            fallback = [
                "Reflect on one recent success to reinforce positive momentum.",
                "Maintain consistent sleep by going to bed 15 minutes earlier tonight.",
                "Take time to plan tomorrow so you start with clarity."
            ]
        tip_text = "\n".join(fallback[:3])

    return {"tip": tip_text}


@app.post("/get-tip-batch")
def get_tip_batch(req: TipRequest, request: Request):
    api_key = request.headers.get("x-api-key", "")
    if api_key != VALID_CLIENT_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    prompt = build_prompt(req)
    try:
        out = generator(
            prompt,
            max_length=120,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.2,
            num_return_sequences=50,
            early_stopping=True,
        )
        raw_texts = [entry.get("generated_text", "") for entry in out]
        selected = select_best_tips(raw_texts)
        if not selected:
            raise ValueError("Degenerate or no valid tips from model")
        return {"tips": selected}
    except Exception as e:
        print("Batch generation fallback due to:", e)
        return {"tips": []}