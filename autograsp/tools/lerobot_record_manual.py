"""lerobot-record where every episode starts on a key press instead of a timer.

Wraps the stock LeRobot 0.5.2 record loop (no source change). Per episode:
  WAIT   teleop is live, nothing is recorded; place the object, move to the start pose
  ->     start recording ("Recording" is spoken)
  ->     end the episode (or it ends at --dataset.episode_time_s); it is saved, then back to WAIT
  <-     while recording: discard this episode and go back to WAIT (ignored while waiting)
  Esc    stop the session (an episode being recorded is kept)
Run with --dataset.reset_time_s=0: the WAIT phase replaces LeRobot's timed reset.
"""

import sys

import lerobot.scripts.lerobot_record as lr

PLAY = "--play_sounds=true" in sys.argv
_orig_loop, _orig_say = lr.record_loop, lr.log_say


def _say(text, play_sounds, blocking=False):
    # timed prompts are replaced by the key-driven ones below
    if text.startswith(("Recording episode", "Reset the environment")):
        return
    _orig_say(text, play_sounds, blocking=blocking)


def _loop(**kw):
    if kw.get("dataset") is None:  # LeRobot's reset phase; zero-length with reset_time_s=0
        return _orig_loop(**kw)
    events = kw["events"]
    n = kw["dataset"].num_episodes
    _orig_say("Ready", PLAY)
    while True:
        print(f"\n>>> [대기] episode {n}: 테이프와 팔을 준비하고  →  키를 누르면 녹화 시작 (Esc 종료)", flush=True)
        _orig_loop(**{**kw, "dataset": None, "control_time_s": 24 * 3600})
        if events["stop_recording"]:
            events["rerecord_episode"] = True  # makes record() drop the empty buffer instead of saving it
            return None
        if events["rerecord_episode"]:  # <- while waiting means nothing; keep waiting
            events["rerecord_episode"] = events["exit_early"] = False
            continue
        events["exit_early"] = False
        break
    print(f">>> [녹화 중] episode {n}: 끝나면 →, 망쳤으면 ←", flush=True)
    _orig_say("Recording", PLAY)
    return _orig_loop(**kw)


lr.record_loop, lr.log_say = _loop, _say

if __name__ == "__main__":
    sys.argv[0] = "lerobot-record"
    lr.main()
