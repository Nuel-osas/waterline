"""Check that a reading added after the pinned day cannot change any quoted number or break the checks.

  python3 -m pipeline.tomorrow      # works on a temporary copy; the repository is not touched

The dashboard job adds a day every morning and then runs the same checks. Every number in the text is pinned to
one day, so a new reading must leave the text true. This makes a copy of the repository, invents the next day by
repeating the last one, rebuilds, and runs the offline check there. It exists because a count that was not
pinned would have stopped the first scheduled run.
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    tmp = tempfile.mkdtemp(prefix="waterline-tomorrow-")
    try:
        for name in os.listdir(ROOT):
            if name.startswith(".") or name == "__pycache__":
                continue
            src, dst = os.path.join(ROOT, name), os.path.join(tmp, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(src, dst)
        data = os.path.join(tmp, "data")
        with open(os.path.join(data, "blocks.json")) as f:
            blocks = json.load(f)
        last = max(blocks)
        nxt = (dt.date.fromisoformat(last) + dt.timedelta(days=1)).isoformat()
        height = blocks[last]["height"] + 143_000
        blocks[nxt] = {"height": height, "timestamp": blocks[last]["timestamp"] + 86_400 * 10**9}
        with open(os.path.join(data, "blocks.json"), "w") as f:
            json.dump(blocks, f, indent=1, sort_keys=True)
        with open(os.path.join(data, "tracked.json")) as f:
            tracked = set(json.load(f))
        for kind in ("float", "held", "credited"):
            path = os.path.join(data, kind, last + ".json")
            if not os.path.exists(path):
                continue
            with open(path) as f:
                day = json.load(f)
            day["day"], day["height"] = nxt, height
            for key in ("held", "credited"):
                if key in day:   # a daily reading covers the tracked tokens only
                    day[key] = {k: v for k, v in day[key].items() if k in tracked}
            with open(os.path.join(data, kind, nxt + ".json"), "w") as f:
                json.dump(day, f, indent=1, sort_keys=True)
        run = lambda *cmd: subprocess.run([sys.executable, "-m", *cmd], cwd=tmp, capture_output=True, text=True)   # noqa: E731
        for module in ("pipeline.build", "pipeline.claims", "pipeline.score", "pipeline.score_audit"):
            got = run(module)
            if got.returncode:
                print(f"FAIL {module} does not run once {nxt} is added:\n{got.stdout[-600:]}{got.stderr[-600:]}")
                return 1
        got = run("pipeline.verify", "--offline")
        bad = [line for line in got.stdout.split("\n") if line.startswith("FAIL")]
        if got.returncode or bad:
            print(f"FAIL the checks do not pass once a reading for {nxt} is added:")
            print("\n".join(bad) or got.stdout[-800:])
            return 1
        print(f"ok   with a reading for {nxt} added to a copy, every module runs and the offline check still passes: "
              "no quoted number depends on days after the pinned one")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
