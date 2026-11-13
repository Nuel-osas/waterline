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
        out.append({"id": tid, "text": text, "due": due, "status": "PASS" if ok else "FAIL", "value": value})

    add("F1", f"The float on the {NEAR_TERM} reading is at least what it was on {WRITTEN} (${float(base['float_usd']) / 1e6:.1f}M).",
        NEAR_TERM, lambda r: (r["float_usd"] >= base["float_usd"], f"${float(r['float_usd']) / 1e6:.1f}M"))

    def breadth(r):
        later = [x for x in rows if WRITTEN <= x["day"] <= NEAR_TERM]
        biggest = max(later[k]["float_usd"] - later[k - 1]["float_usd"] for k in range(1, len(later)))
        return biggest < tenth, f"largest one-day rise ${float(biggest) / 1e6:.1f}M"
    add("F2", f"No single day between the two readings adds more than the tenth-largest rise so far (${float(tenth) / 1e6:.1f}M): "
              "growth, if any, is not one more lump.", NEAR_TERM, breadth)

    add("F3", f"The private share of the tracked tokens on the {NEAR_TERM} reading is at least 60.0% "
              f"(it was {float(base['share_usd']) * 100:.1f}% on {WRITTEN}).",
        NEAR_TERM, lambda r: (r["share_usd"] is not None and r["share_usd"] >= SHARE_FLOOR,
                              "unknown" if r["share_usd"] is None else f"{float(r['share_usd']) * 100:.1f}%"))

    add("R1", "The float is at least $200M.", LONG_DATED,
        lambda r: (r["float_usd"] >= 200_000_000, f"${float(r['float_usd']) / 1e6:.1f}M"))

    def concentration(r):
        upto = [x for x in rows if x["day"] <= LONG_DATED]
        top = sorted((upto[k]["float_usd"] - upto[k - 1]["float_usd"] for k in range(1, len(upto))), reverse=True)[:10]
        ratio = sum(top) / r["float_usd"]
        return ratio < Fraction(45, 100), f"{float(ratio) * 100:.0f}%"
    add("R2", "The ten best days are less than 45% of the float.", LONG_DATED, concentration)

    add("R3", "The private share of the tracked tokens is at least 50%.", LONG_DATED,
        lambda r: (r["share_usd"] is not None and r["share_usd"] >= Fraction(1, 2),
                   "unknown" if r["share_usd"] is None else f"{float(r['share_usd']) * 100:.1f}%"))
    return out


def score():
    rows, _, _, _ = build()
    out = {"written": WRITTEN, "tests": tests(rows)}
    save(os.path.join(DATA, "derived", "forward.json"), out)
    import json
    from .pull import ROOT
    with open(os.path.join(ROOT, "site", "forward.js"), "w") as f:
        f.write("window.WATERLINE_FORWARD = " + json.dumps(out, separators=(",", ":")) + ";\n")
    return out


if __name__ == "__main__":
    for t in score()["tests"]:
        print(f"{t['status']:8} {t['id']}  due {t['due']}  {t['text']}" + (f"  -> {t['value']}" if t["value"] else ""))
