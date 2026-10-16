"""Run a LeRobot CLI with the so101_safe_follower plugin registered (nothing is pip-installed).

    python autograsp/tools/lr.py rollout --robot.type=so101_safe_follower ...
    python autograsp/tools/lr.py record  ...
"""

import sys

from common import enable_plugin

COMMANDS = {
    "record": "lerobot.scripts.lerobot_record",
    "rollout": "lerobot.scripts.lerobot_rollout",
    "teleoperate": "lerobot.scripts.lerobot_teleoperate",
    "replay": "lerobot.scripts.lerobot_replay",
    "train": "lerobot.scripts.lerobot_train",
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"usage: lr.py {{{'|'.join(COMMANDS)}}} [lerobot args...]")
    cmd = sys.argv.pop(1)
    enable_plugin()
    import importlib

    sys.argv[0] = f"lerobot-{cmd}"
    importlib.import_module(COMMANDS[cmd]).main()
