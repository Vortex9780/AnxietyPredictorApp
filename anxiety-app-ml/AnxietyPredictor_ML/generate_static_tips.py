# generate_static_tips.py
def generate_tips():
    anxiety_phrases = {
        "high": "Your anxiety is high—try {action} for {duration}.",
        "moderate": "You seem moderately anxious; consider {action} to reset for {duration}.",
        "low": "You're doing well; maintain momentum with {action} for {duration}."
    }

    actions = [
        "a 5-minute breathing exercise",
        "journaling for 5 minutes",
        "a short walk outside",
        "a quick body scan",
        "connecting with a friend",
        "limiting screen time for a bit",
        "drinking a full glass of water and pausing",
        "setting a small achievable goal",
        "doing the box breath (4-4-4-4)",
        "reflecting on one positive thing from today"
    ]

    durations = [
        "5 minutes",
        "10 minutes",
        "a short moment",
        "a mindful pause",
        "a brief break"
    ]

    tips = []
    for level in ["high", "moderate", "low"]:
        for action in actions:
            for duration in durations:
                tip = anxiety_phrases[level].format(action=action, duration=duration)
                tips.append(tip)

    # dedupe while preserving order
    seen = set()
    unique_tips = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            unique_tips.append(t)
        if len(unique_tips) >= 200:
            break

    return unique_tips

if __name__ == "__main__":
    tips = generate_tips()
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")