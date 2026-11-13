"""Score the audit's forward tests in PREREG-AUDIT.md against the readings taken after they were written.

  python3 -m pipeline.score_audit     # prints one line per test and writes data/derived/forward_audit.json

These tests are about the claim the thesis now leads with: that the public books of NEAR Intents are whole and
that a hole in them is seen and closed. The tests in PREREG.md, scored by pipeline/score.py, are about the money
behind the private chain. Both files are hashed; neither is edited after its hash was recorded.

A reading on which any tracked token's credited or held total could not be read is UNKNOWN, never a pass.
"""
import os

from . import audit
from .build import site_js, token_meta
from .pull import DATA, ROOT, load, save

WRITTEN = "2026-11-13"       # the last reading the authors had seen when the tests were written
FIRST_CHECK = "2026-11-14"
NEAR_TERM = "2026-11-17"
LONG_DATED = "2027-03-31"
CLOSE_WITHIN = 3             # readings: the October hole was open on three daily readings and closed on the fourth


def reading(day, held, credited, tracked):
    """One day's audit of the tracked tokens: (short ids, unknown ids)."""
    short, unknown = [], []
    for t in tracked:
        status, _ = audit.compare(credited.get(t), held.get(t))
        if status == "short":
            short.append(t)
        elif status == "unknown":
            unknown.append(t)
    return short, unknown


def tests(days, tracked):
    """`days` is [(day, held, credited)] oldest first, as audit.stored_days() returns it."""
    by_day = {d: reading(d, h, c, tracked) for d, h, c in days}
    later = sorted(d for d in by_day if d > WRITTEN)
    out = []

    def add(tid, text, due, status, value=None):
        out.append({"id": tid, "text": text, "due": due, "status": status, "value": value})

    for tid, due in (("G1", FIRST_CHECK), ("G2", NEAR_TERM)):
        text = f"On the {due} reading none of the {len(tracked)} tracked tokens is short: intents.near holds at least what it has credited."
        if due not in by_day:
            add(tid, text, due, "PENDING")
            continue
        short, unknown = by_day[due]
        if short:
            add(tid, text, due, "FAIL", f"{len(short)} short")
        elif unknown:
            add(tid, text, due, "UNKNOWN", f"{len(unknown)} could not be read")
        else:
            add(tid, text, due, "PASS", "none short")

    # G3: a token short on a reading is whole again within CLOSE_WITHIN readings. It fails as soon as one is not.
    text = (f"From {FIRST_CHECK} to {LONG_DATED}, any tracked token found short on a reading is whole again within "
            f"{CLOSE_WITHIN} readings.")
    open_run, broke, seen_short = {}, None, 0
    for d in later:
        if d > LONG_DATED:
            break
        short, _ = by_day[d]
        for t in tracked:
            if t in short:
                open_run[t] = open_run.get(t, 0) + 1
                seen_short += open_run[t] == 1
                if open_run[t] > CLOSE_WITHIN and broke is None:
                    broke = (t, d)
            elif t not in by_day[d][1]:
                open_run.pop(t, None)
    if broke:
        add("G3", text, LONG_DATED, "FAIL", f"{broke[0]} still short on {broke[1]}")
    elif LONG_DATED in by_day:
        add("G3", text, LONG_DATED, "PASS", f"{seen_short} holes, each closed in time")
    else:
        add("G3", text, LONG_DATED, "PENDING", f"{seen_short} holes so far" if later else None)

    # G4: the audit keeps being possible. If the two view methods stop answering, the claim has nothing under it.
    text = f"On the {LONG_DATED} reading both questions can still be asked for every tracked token: no total is unreadable."
    if LONG_DATED not in by_day:
        add("G4", text, LONG_DATED, "PENDING")
    else:
        short, unknown = by_day[LONG_DATED]
        add("G4", text, LONG_DATED, "FAIL" if unknown else "PASS", f"{len(unknown)} unreadable")
    return out


def score(write=True):
    tracked = load(os.path.join(DATA, "tracked.json"), [])
    meta, _ = token_meta()
    days = audit.stored_days()
    # a token is audited from the first day it has a total to read; before that it is not "unknown", it is absent
    first_seen = {}
    for d, h, _c in days:
        for t in h:
            first_seen.setdefault(t, d)
    days = [(d, h, c) for d, h, c in days]
    tracked = [t for t in tracked if t in meta and t in first_seen]
    out = {"written": WRITTEN, "tests": tests(days, tracked)}
    score.last = {"forward_audit": out, "forward_audit_js": site_js("WATERLINE_FORWARD_AUDIT", out)}
    if write:
        save(os.path.join(DATA, "derived", "forward_audit.json"), out)
        with open(os.path.join(ROOT, "site", "forward_audit.js"), "w") as f:
            f.write(score.last["forward_audit_js"])
    return out


if __name__ == "__main__":
    for t in score()["tests"]:
        print(f"{t['status']:8} {t['id']}  due {t['due']}  {t['text']}" + (f"  -> {t['value']}" if t["value"] else ""))
