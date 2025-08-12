#!/usr/bin/env python3
# gacha.py
import json, os, sys, time, random, uuid
from datetime import datetime

# ---------- Utils ----------
ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(ROOT, "config.json")
REWARDS_PATH = os.path.join(ROOT, "rewards.json")
HISTORY_PATH = os.path.join(ROOT, "history.json")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_history():
    if not os.path.exists(HISTORY_PATH):
        save_json(HISTORY_PATH, [])

def color(text, fg=None, style=None):
    # minimal ANSI
    colors = {"red":"31","green":"32","yellow":"33","blue":"34","magenta":"35","cyan":"36","white":"37"}
    styles = {"bold":"1","dim":"2"}
    parts = []
    if style and style in styles: parts.append(styles[style])
    if fg and fg in colors: parts.append(colors[fg])
    if not parts: return text
    return f"\033[{';'.join(parts)}m{text}\033[0m"

# ---------- Spinner (visual only) ----------
def spinner(names, final_index, cycles=2, fps=30, ease_out=True):
    """Simple text spinner that cycles through names and lands on final_index."""
    if not names:
        return
    # Build sequence ring
    ring = list(names)
    n = len(ring)
    total_steps = cycles * n + final_index % n

    # easing: start fast, end slow
    base_delay = 1.0 / max(10, fps)  # fast
    max_delay  = 1.0 / 4             # slow cap
    delays = []
    for i in range(total_steps+1):
        t = i / max(1, total_steps)
        if ease_out:
            # quadratic ease-out: delay increases over time
            d = base_delay + (max_delay - base_delay) * (t**2)
        else:
            d = base_delay
        delays.append(d)

    # Render
    for i in range(total_steps+1):
        idx = i % n
        line = []
        for j, name in enumerate(ring):
            if j == idx:
                line.append(color(f"[{name}]", fg="yellow", style="bold"))
            else:
                line.append(name)
        out = "  ".join(line)
        sys.stdout.write("\r" + " " * 120)  # clear line
        sys.stdout.write("\r" + out[:120])  # truncate to keep tidy
        sys.stdout.flush()
        time.sleep(delays[i])
    sys.stdout.write("\n")

# ---------- Core ----------
DIFF_ORDER = ["EASY","MEDIUM","HARD"]

def build_pool(rewards, cfg, mission_diff):
    enabled = [r for r in rewards if r.get("enabled", True)]
    if not cfg.get("use_difficulty_lock", False):
        return enabled
    # lock mode
    unlock_map = cfg.get("grade_unlock_map", {})
    allowed = set(unlock_map.get(mission_diff, []))
    return [r for r in enabled if r.get("grade") in allowed]

def pick_reward(pool):
    weights = [max(0.000001, float(r.get("weight", 1.0))) for r in pool]
    choice = random.choices(pool, weights=weights, k=1)[0]
    return choice

def record_history(difficulty, reward_id):
    ensure_history()
    hist = load_json(HISTORY_PATH, [])
    hist.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "difficulty": difficulty,
        "reward_id": reward_id
    })
    save_json(HISTORY_PATH, hist)

def require_files():
    # Create sample config/rewards if missing
    if not os.path.exists(CONFIG_PATH):
        sample = {
            "use_difficulty_lock": False,
            "grade_unlock_map": {
                "EASY":   ["BASIC"],
                "MEDIUM": ["BASIC","RARE"],
                "HARD":   ["BASIC","RARE","EPIC"]
            },
            "spinner": {"cycles": 2, "fps": 30, "ease_out": True}
        }
        save_json(CONFIG_PATH, sample)

    if not os.path.exists(REWARDS_PATH):
        sample_rewards = [
            {"id": str(uuid.uuid4()), "name":"Short Video (5m)", "grade":"BASIC", "weight":3, "enabled": True},
            {"id": str(uuid.uuid4()), "name":"Game (30m)",       "grade":"BASIC", "weight":2, "enabled": True},
            {"id": str(uuid.uuid4()), "name":"Music Break",      "grade":"BASIC", "weight":3, "enabled": True},
            {"id": str(uuid.uuid4()), "name":"Cafe Drink",       "grade":"RARE",  "weight":1, "enabled": True},
            {"id": str(uuid.uuid4()), "name":"Movie Episode",    "grade":"RARE",  "weight":1, "enabled": True},
            {"id": str(uuid.uuid4()), "name":"Delivery Meal",    "grade":"EPIC",  "weight":1, "enabled": True}
        ]
        save_json(REWARDS_PATH, sample_rewards)

    ensure_history()

def main():
    require_files()
    cfg = load_json(CONFIG_PATH, {})
    rewards = load_json(REWARDS_PATH, [])

    # Get mission difficulty
    if len(sys.argv) >= 2:
        mission_diff = sys.argv[1].upper()
    else:
        mission_diff = input("Mission difficulty (EASY/MEDIUM/HARD): ").strip().upper()

    if mission_diff not in DIFF_ORDER:
        print("Invalid difficulty. Use EASY / MEDIUM / HARD.")
        sys.exit(1)

    pool = build_pool(rewards, cfg, mission_diff)
    if not pool:
        print(color("No rewards available for current settings.", fg="red", style="bold"))
        sys.exit(0)

    # Draw
    chosen = pick_reward(pool)

    # Visual spinner
    sp_cfg = cfg.get("spinner", {})
    cycles  = int(sp_cfg.get("cycles", 2))
    fps     = int(sp_cfg.get("fps", 30))
    ease    = bool(sp_cfg.get("ease_out", True))

    # Names for spinner; ensure chosen ends at final index
    names = [r["name"] for r in pool]
    final_index = names.index(chosen["name"])
    print(color("Spinning...", fg="cyan", style="bold"))
    spinner(names, final_index, cycles=cycles, fps=fps, ease_out=ease)

    # Result
    print(color(f"★ Reward: {chosen['name']}  (grade={chosen.get('grade')})", fg="green", style="bold"))
    record_history(mission_diff, chosen["id"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
