"""Collection plan for the language-conditioned task "Move the tape to sector N" (N = 1..9).

Layout: a FIXED 3x3 grid of sectors on the desk, numbered like a phone keypad as seen from behind the
robot (1 = far-left ... 9 = near-right). Each episode: the tape starts in a random sector S != N and is
moved into sector N. lerobot-record keeps one task text per run, so one block = one target sector.

Rounds grow the dataset after each evaluation (counts are a starting point, not a success guarantee):
  R1: 3 episodes per target (27)  -> first SmolVLA/ACT training, pipeline + language-following check
  R2: +3 per target (54 total)    R3: +3 per target (81 total)
Within a round, start sectors are balanced so every (start -> target) direction appears; block order is
shuffled so no target is always recorded first/last (operator fatigue would correlate with the label).

    python autograsp/tools/make_sector_plan.py --seed 0
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "config"
SECTORS = list(range(1, 10))


def task_text(n: int) -> str:
    return f"Move the tape to sector {n}."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--per-target", type=int, default=3, help="episodes per target sector per round")
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    # start-sector pools per target, consumed across rounds so directions don't repeat until exhausted
    pools = {t: [] for t in SECTORS}
    blocks = []
    for r in range(1, args.rounds + 1):
        order = SECTORS[:]
        rng.shuffle(order)
        for t in order:
            starts = []
            for _ in range(args.per_target):
                if not pools[t]:
                    pools[t] = [s for s in SECTORS if s != t]
                    rng.shuffle(pools[t])
                starts.append(pools[t].pop())
            blocks.append({"block": f"R{r}-T{t}", "round": r, "target": t, "task": task_text(t),
                           "episodes": [{"k": k, "start": s} for k, s in enumerate(starts)]})

    plan = {"seed": args.seed, "layout": "3x3 keypad as seen from behind the robot: 1 2 3 (far) / 4 5 6 / 7 8 9 (near)",
            "blocks": blocks}
    out = CFG / "sector_plan.json"
    out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    for b in blocks:
        print(f"{b['block']:7s} target={b['target']} starts={[e['start'] for e in b['episodes']]}")
    print(f"{len(blocks)} blocks, {sum(len(b['episodes']) for b in blocks)} episodes -> {out}")


if __name__ == "__main__":
    main()
