"""Run lerobot-train with one Windows fix: `checkpoints/last` becomes a directory junction.

LeRobot creates `last` with Path.symlink_to, which needs admin or Developer Mode on Windows
(WinError 1314). A junction needs neither and reads identically for --resume / --policy.path.
"""

import os
import shutil
import sys
from pathlib import Path


def update_last_checkpoint(checkpoint_dir: Path) -> Path:
    last = checkpoint_dir.parent / "last"
    if last.is_symlink() or last.is_junction():
        os.unlink(last)
    elif last.exists():
        shutil.rmtree(last)
    import _winapi

    _winapi.CreateJunction(str(checkpoint_dir.resolve()), str(last))
    return last


if __name__ == "__main__":
    import lerobot.common.train_utils as tu

    tu.update_last_checkpoint = update_last_checkpoint
    import lerobot.scripts.lerobot_train as lt

    lt.update_last_checkpoint = update_last_checkpoint
    sys.argv[0] = "lerobot-train"
    lt.main()
