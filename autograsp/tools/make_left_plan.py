"""Collection plan for the fixed task "Move the dice to the left cell." (start sector 1..9 -> one fixed left cell).

The left cell is a separate marked cell to the left of the 3x3 grid. The task text never changes, so one
block can hold many episodes; a block here is 9 episodes, one per start sector in shuffled order, to keep
operator fatigue from correlating with the start sector. Rounds grow the dataset after each evaluation:
  R1: 3 blocks (27 episodes)   R2: +3 blocks (54)   R3: +3 blocks (81)

    python autograsp/tools/make_left_plan.py --seed 0
    python autograsp/tools/record_sector.py --plan left_plan.json --round 1
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "config"
SECTORS = list(range(1, 10))
TASK = "Move the dice to the left cell."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--blocks-per-round", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    blocks = []
    for r in range(1, args.rounds + 1):
        for b in range(1, args.blocks_per_round + 1):
            order = SECTORS[:]
            rng.shuffle(order)
            blocks.append({"block": f"R{r}-B{b}", "round": r, "target": "left", "target_label": "the LEFT cell",
                           "task": TASK, "episodes": [{"k": k, "start": s} for k, s in enumerate(order)]})
    plan = {"seed": args.seed, "layout": "3x3 keypad as seen from behind the robot: 1 2 3 (far) / 4 5 6 / 7 8 9 (near); "
            "target = separate fixed cell to the left of the grid", "blocks": blocks}
    out = CFG / "left_plan.json"
    out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    for b in blocks:
        print(f"{b['block']:7s} starts={[e['start'] for e in b['episodes']]}")
    print(f"{len(blocks)} blocks, {sum(len(b['episodes']) for b in blocks)} episodes -> {out}")


if __name__ == "__main__":
    main()
