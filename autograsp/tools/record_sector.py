"""Record target-sector blocks with the leader arm (key-driven lerobot-record, plain so101_follower).

    python autograsp/tools/record_sector.py --round 1           # every remaining block of round 1, in order
    python autograsp/tools/record_sector.py --next              # only the first block not recorded yet
    python autograsp/tools/record_sector.py --block R1-T5
    python autograsp/tools/record_sector.py --status            # what has been recorded

Per episode: tape in the printed START sector, arm (leader) in the start pose, then move the tape into
the TARGET sector and return to the start pose. Keys (see lerobot_record_manual.py):
  ->  start / end an episode     <-  (while recording) redo it     Esc  stop
The follower keeps torque after each block, so a raised arm does not drop between blocks.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

from common import CONFIG_DIR, PYTHON, cameras_cli, dataset_root, load_rig

LOG = CONFIG_DIR / "sector_conditions.csv"
FIELDS = ["dataset", "episode_index", "block", "round", "start", "target", "task"]


def total_episodes(root: Path) -> int:
    info = root / "meta" / "info.json"
    return json.loads(info.read_text(encoding="utf-8"))["total_episodes"] if info.exists() else 0


def sync_follower_to_leader(rig, max_speed_deg_s: float = 30.0, timeout_s: float = 15.0) -> bool:
    """Drive the follower slowly onto the leader's current pose, then leave it holding (torque on).

    lerobot-record would otherwise snap the follower to the leader at full servo speed on connect.
    """
    import time

    from align_check import BASE, NAMES, bus_for

    fol = bus_for(rig["follower"]["port"], BASE / f"robots/so_follower/{rig['follower']['id']}.json")
    lead = bus_for(rig["leader"]["port"], BASE / f"teleoperators/so_leader/{rig['leader']['id']}.json")
    try:
        f, l = fol.sync_read("Present_Position"), lead.sync_read("Present_Position")
        roll = ((l["wrist_roll"] - f["wrist_roll"] + 180) % 360) - 180
        if abs(roll) > 45:
            print(f"wrist_roll differs by {roll:.0f} deg (>45): align the leader wrist first (align_check.py)")
            return False
        goal = dict(f)  # integrate the goal toward the leader; comparing to the *measured* pose would stall
        fol.sync_write("Goal_Position", goal)  # under gravity sag (servo tracking error)
        fol.enable_torque()
        dt, step = 1 / 30, max_speed_deg_s / 30
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            l = lead.sync_read("Present_Position")
            err = {n: l[n] - goal[n] for n in NAMES}
            err["wrist_roll"] = ((err["wrist_roll"] + 180) % 360) - 180
            if max(abs(err[n]) for n in NAMES) < 0.5:
                time.sleep(0.5)  # let the servos settle on the final goal
                f = fol.sync_read("Present_Position")
                lag = {n: round(l[n] - f[n], 1) for n in NAMES}
                print(f"follower synced to leader (remaining servo lag: {lag})")
                return True
            goal = {n: goal[n] + max(-step, min(step, err[n])) for n in NAMES}
            fol.sync_write("Goal_Position", goal)
            time.sleep(dt)
        print("sync timed out (keep the leader still while syncing)")
        return False
    finally:
        fol.disconnect(disable_torque=False)  # keep holding until lerobot-record takes over
        lead.disconnect(disable_torque=False)


def recorded_blocks() -> dict[str, int]:
    done: dict[str, int] = {}
    if LOG.exists():
        with open(LOG, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                done[row["block"]] = done.get(row["block"], 0) + 1
    return done


def speak(text: str) -> None:
    subprocess.Popen(["PowerShell", "-Command", "Add-Type -AssemblyName System.Speech; "
                      f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"])


def run_block(block, args, rig, root) -> tuple[int, int]:
    already = recorded_blocks().get(block["block"], 0)
    todo = block["episodes"][already:]
    before = total_episodes(root)
    label = block.get("target_label", f"sector {block['target']}")
    print(f"\n=== {block['block']}  TARGET = {label}   task: \"{block['task']}\"")
    print(f"dataset: {root}  (existing episodes: {before})")
    for i, e in enumerate(todo):
        print(f"  episode {before + i:4d}: put the object in sector {e['start']}  ->  move it to {label}")
    print("Keys: -> start / end an episode   <- (while recording) redo it   Esc stop.\n")

    cmd = [
        str(PYTHON), str(Path(__file__).with_name("lerobot_record_manual.py")),
        "--robot.type=so101_follower", f"--robot.port={rig['follower']['port']}", f"--robot.id={rig['follower']['id']}",
        f"--robot.cameras={cameras_cli(rig)}",
        "--robot.disable_torque_on_disconnect=false",  # keep holding the pose between blocks instead of dropping
        "--teleop.type=so101_leader", f"--teleop.port={rig['leader']['port']}", f"--teleop.id={rig['leader']['id']}",
        f"--dataset.repo_id={args.repo}", f"--dataset.root={root.as_posix()}",
        f"--dataset.single_task={block['task']}", f"--dataset.fps={rig['control_fps']}",
        f"--dataset.num_episodes={len(todo)}", f"--dataset.episode_time_s={args.episode_time}",
        f"--dataset.reset_time_s={args.reset_time}", "--dataset.push_to_hub=false", "--dataset.video=true",
        "--dataset.vcodec=h264", "--display_data=false", f"--play_sounds={'false' if args.quiet else 'true'}",
        f"--resume={'true' if before > 0 else 'false'}",
    ]
    if args.print_only:
        print(" ".join(cmd))
        return len(todo), len(todo)
    if args.go_start and subprocess.call([str(PYTHON), str(Path(__file__).with_name("go_start.py"))]) != 0:
        sys.exit("start pose not reached: not started")
    if args.sync and not sync_follower_to_leader(rig):
        sys.exit("not started")
    rc = subprocess.call(cmd)
    recorded = total_episodes(root) - before
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for i, e in enumerate(todo[:recorded]):
            w.writerow({"dataset": args.repo, "episode_index": before + i, "block": block["block"],
                        "round": block["round"], "start": e["start"], "target": block["target"], "task": block["task"]})
    print(f"\nlerobot-record exit={rc}; recorded {recorded}/{len(todo)} episodes of {block['block']}")
    return recorded, len(todo)


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--block")
    g.add_argument("--next", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--round", type=int, help="record every remaining block of this round, one after another")
    ap.add_argument("--repo", default="local/so101_sector_train")
    ap.add_argument("--plan", default="sector_plan.json", help="plan file name in config/ (e.g. left_plan.json)")
    ap.add_argument("--episode-time", type=float, default=120, help="max length; end earlier with ->")
    ap.add_argument("--reset-time", type=float, default=0, help="0: the key-driven wait replaces the timed reset")
    ap.add_argument("--quiet", action="store_true", help="no spoken cues")
    ap.add_argument("--sync", action="store_true", help="slowly move the follower onto the leader before recording")
    ap.add_argument("--go-start", action="store_true",
                    help="first move the follower to the fixed rig.json start_pose and wait until the leader matches it")
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args()

    rig = load_rig()
    plan = json.loads((CONFIG_DIR / args.plan).read_text(encoding="utf-8"))
    root = dataset_root(rig, args.repo)

    def pending(blocks):
        done = recorded_blocks()
        return [b for b in blocks if done.get(b["block"], 0) < len(b["episodes"])]

    if args.status:
        done = recorded_blocks()
        for b in plan["blocks"]:
            print(f"{b['block']:7s} target={b['target']} {done.get(b['block'], 0)}/{len(b['episodes'])}")
        print(f"dataset {root}: {total_episodes(root)} episodes")
        return
    if args.block:
        queue = [b for b in plan["blocks"] if b["block"] == args.block]
        if not queue:
            sys.exit(f"unknown block {args.block}")
    elif args.round:
        queue = pending([b for b in plan["blocks"] if b["round"] == args.round])
    else:
        queue = pending(plan["blocks"])[:1]
    if not queue:
        sys.exit("nothing left to record")

    print("\n[준비] 리더를 시작 자세로 가만히 들고, 다른 손으로 follower 팔뚝을 살짝 받쳐 주세요.")
    print("       연결 순간(1초 미만) follower 토크가 잠깐 꺼지고, 리더 자세로 바로 이동합니다.")
    print("       'Ready' 음성이 나오면 받친 손을 떼고, 준비되면 → 키로 녹화를 시작하세요.")
    print("       블록이 끝나도 follower 토크는 유지됩니다(팔이 떨어지지 않음).")
    for i, block in enumerate(queue):
        if i > 0:
            print(f"\n########  다음 블록: {block['block']} (목표 {block.get('target_label', str(block['target']) + '번 칸')})  ########")
            if not args.quiet:
                speak(f"Next block {block['block']}")
        recorded, wanted = run_block(block, args, rig, root)
        if recorded < wanted:  # Esc pressed: stop the chain
            print("Stopped early; run the same command again to continue where you left off.")
            break
    else:
        print("\n모든 블록 완료")


if __name__ == "__main__":
    main()
