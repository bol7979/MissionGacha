#!/usr/bin/env python3
# gacha.py — Mission Gacha (roulette-only spinner)
# - Difficulty lock toggle (config.json)
# - rewards.json: user-managed, missing IDs auto-filled (UUID)
# - Single-line safe spinner (no blank lines), easing + overshoot + palette
# - validate mode to sanity-check rewards

import json, os, sys, time, random, uuid, shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH  = os.path.join(ROOT, "config.json")
REWARDS_PATH = os.path.join(ROOT, "rewards.json")
HISTORY_PATH = os.path.join(ROOT, "history.json")

DIFF_ORDER = ["EASY","MEDIUM","HARD"]

# -------------------- IO helpers --------------------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_files():
    if not os.path.exists(CONFIG_PATH):
        save_json(CONFIG_PATH, {
            "use_difficulty_lock": False,
            "grade_unlock_map": {
                "EASY":   ["BASIC"],
                "MEDIUM": ["BASIC","RARE"],
                "HARD":   ["BASIC","RARE","EPIC"]
            },
            "spinner": {
                "cycles": 3,
                "duration_ms": 0,     # 0이면 cycles 기반
                "fps": 30,
                "ease_out": True,
                "overshoot": True,
                "window": 5,
                "palette": "neon",   # classic | neon | sunset | mono
                "final_blink": 4,
                "confetti": True,
                "beep": False,
                "seed": None
            }
        })
        print("[init] config.json created with defaults.")
    if not os.path.exists(REWARDS_PATH):
        save_json(REWARDS_PATH, [
            { "name": "Short Video (5m)", "grade": "BASIC", "weight": 3, "enabled": True },
            { "name": "Game (30m)",       "grade": "BASIC", "weight": 2, "enabled": True },
            { "name": "Music Break",      "grade": "BASIC", "weight": 3, "enabled": True },
            { "name": "Cafe Drink",       "grade": "RARE",  "weight": 1, "enabled": True },
            { "name": "Movie Episode",    "grade": "RARE",  "weight": 1, "enabled": True },
            { "name": "Delivery Meal",    "grade": "EPIC",  "weight": 1, "enabled": True }
        ])
        print("[init] rewards.json created as empty []. Add your rewards and rerun.")
    if not os.path.exists(HISTORY_PATH):
        save_json(HISTORY_PATH, [])

# -------------------- ANSI / rendering --------------------
def ansi(text, fg=None, style=None):
    colors = {"black":"30","red":"31","green":"32","yellow":"33","blue":"34","magenta":"35","cyan":"36","white":"37"}
    styles = {"bold":"1","dim":"2","underline":"4"}
    parts = []
    if style in styles: parts.append(styles[style])
    if fg in colors: parts.append(colors[fg])
    return f"\033[{';'.join(parts)}m{text}\033[0m" if parts else text

def clear_line():
    sys.stdout.write("\r\033[2K")

def bell(beep=False):
    if beep: sys.stdout.write("\a")

def term_width(min_width=40):
    try:
        w = shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        w = 80
    return max(min_width, w)

def ellipsis(s, maxlen):
    if len(s) <= maxlen: return s
    return s[:maxlen-1] + "…"

# -------------------- Roulette Spinner --------------------
class Spinner:
    PALETTES = {
        "classic": {"focus":"yellow", "trail1":"white", "trail2":"white"},
        "neon":    {"focus":"magenta","trail1":"cyan",  "trail2":"blue"},
        "sunset":  {"focus":"yellow", "trail1":"magenta","trail2":"red"},
        "mono":    {"focus":"white",  "trail1":"white", "trail2":"white"},
    }

    def __init__(self, cfg):
        sp = cfg.get("spinner", {})
        self.cycles      = int(sp.get("cycles", 3))
        self.duration_ms = int(sp.get("duration_ms", 0))
        self.fps         = int(sp.get("fps", 30))
        self.ease_out    = bool(sp.get("ease_out", True))
        self.overshoot   = bool(sp.get("overshoot", True))
        self.window      = int(sp.get("window", 5))
        self.palette     = self.PALETTES.get(sp.get("palette","neon"), self.PALETTES["neon"])
        self.final_blink = int(sp.get("final_blink", 4))
        self.confetti    = bool(sp.get("confetti", True))
        self.beep_on     = bool(sp.get("beep", False))
        self.seed        = sp.get("seed", None)
        if isinstance(self.seed, int):
            random.seed(self.seed)

    def run(self, names, final_index):
        if not names: return
        self._run_roulette(names, final_index)
        self._finish(names[final_index])

    def _delays(self, steps):
        base = 1.0 / max(10, self.fps)
        slow = 1.0 / 4
        delays = []
        for i in range(steps):
            if self.ease_out:
                t = i / max(1, steps-1)
                d = base + (slow - base) * (t**2)
            else:
                d = base
            delays.append(d)
        return delays

    def _render_band(self, items, focus_idx):
        painted = []
        for i, name in enumerate(items):
            if i == focus_idx:
                painted.append(ansi(f"[{name}]", fg=self.palette["focus"], style="bold"))
            elif abs(i - focus_idx) == 1:
                painted.append(ansi(name, fg=self.palette["trail1"]))
            elif abs(i - focus_idx) == 2:
                painted.append(ansi(name, fg=self.palette["trail2"], style="dim"))
            else:
                painted.append(name)
        return "  ".join(painted)

    def _run_roulette(self, names, final_index):
        ring = list(names)
        n = len(ring)
        # steps: cycles 기반 또는 duration 기반
        if self.duration_ms > 0:
            steps = max(10, int(self.fps * (self.duration_ms/1000.0)))
            base_rot = (steps // n) * n
            steps = base_rot + (final_index % n)
        else:
            steps = self.cycles * n + (final_index % n)

        overshoot_steps = 0
        backtrack = []
        if self.overshoot:
            overshoot_steps = min(n//3 + 1, 5)
            backtrack = list(range(overshoot_steps, 0, -1))

        delays = self._delays(steps + overshoot_steps + len(backtrack))
        w = term_width()
        half = max(1, self.window // 2)

        pos = 0
        for i in range(steps + overshoot_steps):
            pos = i % n
            seq = [ring[(pos - half + k) % n] for k in range(self.window)]
            out = self._render_band(seq, half)
            clear_line(); sys.stdout.write(ellipsis(out, w-1)); sys.stdout.flush()
            time.sleep(delays[i])

        for j, step_back in enumerate(backtrack):
            pos = (steps + overshoot_steps - step_back) % n
            seq = [ring[(pos - half + k) % n] for k in range(self.window)]
            out = self._render_band(seq, half)
            clear_line(); sys.stdout.write(ellipsis(out, w-1)); sys.stdout.flush()
            time.sleep(delays[steps + overshoot_steps + j])

        clear_line()
        pos = final_index % n
        seq = [ring[(pos - half + k) % n] for k in range(self.window)]
        out = self._render_band(seq, half)
        sys.stdout.write(ellipsis(out, w-1) + "\n"); sys.stdout.flush()

    def _finish(self, name):
        for _ in range(max(0, self.final_blink)):
            clear_line(); sys.stdout.write(ansi(f"★ {name}", fg=self.palette["focus"], style="bold")); sys.stdout.flush(); time.sleep(0.08)
            clear_line(); sys.stdout.write(ansi(f"★ {name}", fg="white")); sys.stdout.flush(); time.sleep(0.08)
        clear_line(); sys.stdout.write(ansi(f"★ {name}", fg=self.palette["focus"], style="bold") + "\n"); sys.stdout.flush()
        if self.confetti:
            conf = " ".join(random.choice(["🎉","✨","💥","🎊","⭐"]) for _ in range(12))
            print(conf)
        bell(self.beep_on)

# -------------------- Rewards / Engine --------------------
def load_config():
    return load_json(CONFIG_PATH, {})

def load_rewards_with_uuid_backfill():
    rewards = load_json(REWARDS_PATH, [])
    changed = False
    seen = set()
    for r in rewards:
        if not r.get("id"):
            r["id"] = str(uuid.uuid4()); changed = True
        if r["id"] in seen:
            r["id"] = str(uuid.uuid4()); changed = True
        seen.add(r["id"])
        if "enabled" not in r:
            r["enabled"] = True; changed = True
        if "weight" not in r:
            r["weight"] = 1.0; changed = True
    if changed:
        save_json(REWARDS_PATH, rewards)
        print(ansi("[auto-fix] rewards.json updated (UUID/backfill).", fg="cyan"))
    return rewards

def validate_rewards(rewards):
    ok = True
    ids = set()
    for i, r in enumerate(rewards):
        rid = r.get("id")
        if rid in ids:
            print(ansi(f"[validate] duplicate id at index {i}: {rid}", fg="red", style="bold")); ok = False
        ids.add(rid)
        if r.get("grade") not in ("BASIC","RARE","EPIC"):
            print(ansi(f"[validate] invalid grade at index {i}: {r.get('grade')}", fg="yellow"))
        try:
            w = float(r.get("weight", 1))
            if w <= 0: raise ValueError
        except Exception:
            print(ansi(f"[validate] non-positive weight at index {i}: {r.get('weight')}", fg="yellow")); ok = False
    if ok: print(ansi("[validate] rewards.json looks fine.", fg="green", style="bold"))
    return ok

def build_pool(rewards, cfg, mission_diff):
    enabled = [r for r in rewards if r.get("enabled", True)]
    if not cfg.get("use_difficulty_lock", False):
        return enabled
    unlock_map = cfg.get("grade_unlock_map", {})
    allowed = set(unlock_map.get(mission_diff, []))
    return [r for r in enabled if r.get("grade") in allowed]

def pick_reward(pool):
    weights = [max(1e-6, float(r.get("weight", 1.0))) for r in pool]
    return random.choices(pool, weights=weights, k=1)[0]

def record_history(difficulty, reward_id, reward_name):
    hist = load_json(HISTORY_PATH, [])
    hist.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "difficulty": difficulty,
        "reward_id": reward_id,
        "reward_name": reward_name
    })
    save_json(HISTORY_PATH, hist)

# -------------------- Main --------------------
def main():
    if "--validate" in sys.argv:
        ensure_files()
        rewards = load_rewards_with_uuid_backfill()
        validate_rewards(rewards)
        return

    ensure_files()
    cfg = load_config()
    rewards = load_rewards_with_uuid_backfill()

    if len(sys.argv) >= 2 and sys.argv[1] not in ("--validate",):
        mission_diff = sys.argv[1].upper()
    else:
        mission_diff = input("Mission difficulty (EASY/MEDIUM/HARD): ").strip().upper()

    if mission_diff not in DIFF_ORDER:
        print("Invalid difficulty. Use EASY / MEDIUM / HARD.")
        sys.exit(1)

    pool = build_pool(rewards, cfg, mission_diff)
    if not pool:
        print(ansi("No rewards available for current settings.", fg="red", style="bold"))
        return

    chosen = pick_reward(pool)
    names = [r["name"] for r in pool]
    final_index = names.index(chosen["name"])

    print(ansi("Spinning...", fg="cyan", style="bold"))
    sp = Spinner(cfg)
    sp.run(names, final_index)

    print(ansi(f"★ Reward: {chosen['name']}  (grade={chosen.get('grade')})", fg="green", style="bold"))
    record_history(mission_diff, chosen["id"], chosen["name"])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
