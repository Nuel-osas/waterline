"""Score the forward tests in PREREG.md against the readings taken after they were written.

  python3 -m pipeline.score        # prints one line per test and writes data/derived/forward.json

A test whose reading does not exist yet is PENDING. Nothing here can be tuned after the fact: the
thresholds are constants below, the same ones written in PREREG.md, and the readings are block-pinned.
"""
import os
from fractions import Fraction

from .build import build
from .pull import DATA, load, save

WRITTEN = "2026-11-13"      # the pinned day: the last reading the authors had seen
FIRST_CHECK = "2026-11-14"  # scored on the next day's reading, before the submission deadline
NEAR_TERM = "2026-11-17"    # scored on this day's reading, during judging
LONG_DATED = "2027-03-31"
SHARE_FLOOR = Fraction(60, 100)


def tests(rows):
    by_day = {r["day"]: r for r in rows}
    seen = [r for r in rows if r["day"] <= WRITTEN]
    base = by_day[WRITTEN]
    rises = sorted((seen[k]["float_usd"] - seen[k - 1]["float_usd"] for k in range(1, len(seen))), reverse=True)
    tenth = rises[9]
    out = []

    def add(tid, text, due, check):
        r = by_day.get(due)
        if r is None:
            out.append({"id": tid, "text": text, "due": due, "status": "PENDING", "value": None})
            return
        ok, value = check(r)
        status = "UNKNOWN" if ok is None else "PASS" if ok else "FAIL"
        out.append({"id": tid, "text": text, "due": due, "status": status, "value": value})

    def breadth(due):
        def check(r):
            later = [x for x in rows if WRITTEN <= x["day"] <= due]
            biggest = max(later[k]["float_usd"] - later[k - 1]["float_usd"] for k in range(1, len(later)))
            return biggest < tenth, f"largest one-day rise ${float(biggest) / 1e6:.1f}M"
        return check

    def share_at(floor):
        def check(r):
            # a share over only some of the tracked tokens is not the share that was written down: unknown, not a fail
            if not r.get("tracked_complete") or r["share_usd"] is None:
                return None, "not every tracked total could be read"
            return r["share_usd"] >= floor, f"{float(r['share_usd']) * 100:.1f}%"
        return check

    for prefix, due in (("E", FIRST_CHECK), ("F", NEAR_TERM)):
        add(prefix + "1", f"The float on the {due} reading is at least what it was on {WRITTEN} (${float(base['float_usd']) / 1e6:.1f}M).",
            due, lambda r: (r["float_usd"] >= base["float_usd"], f"${float(r['float_usd']) / 1e6:.1f}M"))
        add(prefix + "2", f"No single day between {WRITTEN} and {due} adds more than the tenth-largest rise so far "
                          f"(${float(tenth) / 1e6:.1f}M): growth, if any, is not one more lump.", due, breadth(due))
        add(prefix + "3", f"The private share of the tracked tokens on the {due} reading is at least 60.0% "
                          f"(it was {float(base['share_usd']) * 100:.1f}% on {WRITTEN}).", due, share_at(SHARE_FLOOR))

    add("R1", "The float is at least $200M.", LONG_DATED,
        lambda r: (r["float_usd"] >= 200_000_000, f"${float(r['float_usd']) / 1e6:.1f}M"))

    def concentration(r):
        upto = [x for x in rows if x["day"] <= LONG_DATED]
        top = sorted((upto[k]["float_usd"] - upto[k - 1]["float_usd"] for k in range(1, len(upto))), reverse=True)[:10]
        ratio = sum(top) / r["float_usd"]
        return ratio < Fraction(45, 100), f"{float(ratio) * 100:.0f}%"
    add("R2", "The ten best days are less than 45% of the float.", LONG_DATED, concentration)

    add("R3", "The private share of the tracked tokens is at least 50%.", LONG_DATED, share_at(Fraction(1, 2)))
    add("R5", "The float without NEAR's own token is at least $130M.", LONG_DATED,
        lambda r: (r["float_usd"] - r["groups"]["NEAR"] >= 130_000_000,
                   f"${float(r['float_usd'] - r['groups']['NEAR']) / 1e6:.1f}M"))
    return out


def score(write=True):
    from .build import site_js
    from .pull import ROOT
    rows, _, _, _ = build(write)
    out = {"written": WRITTEN, "tests": tests(rows)}
    score.last = {"forward": out, "forward_js": site_js("WATERLINE_FORWARD", out)}
    if write:
        save(os.path.join(DATA, "derived", "forward.json"), out)
        with open(os.path.join(ROOT, "site", "forward.js"), "w") as f:
            f.write(score.last["forward_js"])
    return out


if __name__ == "__main__":
    for t in score()["tests"]:
        print(f"{t['status']:8} {t['id']}  due {t['due']}  {t['text']}" + (f"  -> {t['value']}" if t["value"] else ""))
