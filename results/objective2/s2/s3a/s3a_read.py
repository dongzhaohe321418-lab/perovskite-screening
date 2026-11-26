#!/usr/bin/env python
"""Reader of the S3a statistics (results/objective2/s2/S3A_HINGE_PLAN.md, sections 3, 5, 5a and 8 step 6).

It parses the text that E's hinge run writes (E_hinge_output.txt, or E_hinge_output_attempt2.txt after a rerun) and
applies the readings and the outcome rule. It opens no archive file and computes no energy: S2, S1 and
E_b^A1(Pb136) are the two-decimal numbers that E printed.

    python -B results/objective2/s2/s3a/s3a_read.py FILE        the readings of FILE, as JSON and as text
    python -B results/objective2/s2/s3a/s3a_read.py --self-test invented texts only; reads no project file
"""
import json, re, sys
from decimal import Decimal

KBT, TWO_KBT, WIDE = Decimal("25.70"), Decimal("51.40"), Decimal("72.70")
HEAD = " 5.2 The quartet and gate values"
NUM = r"(-?\d+\.\d\d) meV"
ROWS = {"S2": re.compile(r"^  E_b\^A2\(Pb136\) = " + NUM),
        "S1": re.compile(r"^  δ_Sr,m30 = E_b\^A2 − E_b\^A1 = " + NUM),
        "Eb_A1": re.compile(r"^  E_b\^A1\(Pb136\) from k = 0 = " + NUM)}
XC_NEEDED = ("XC-STEP0-C2", "XC-K3HINGE", "XC-DSUM-HINGE", "XC-MACEPILOT-A1")
EXIT = re.compile(r"^E exit code: (\d+)$")


def read(text):
    lines = text.split("\n")
    out = {"exit_code": None, "lines": {}, "values": {}, "outcome": None, "why": None, "readings": {}, "xc": {}}
    last = [x for x in lines if x.strip()]
    m = EXIT.match(last[-1]) if last else None
    if m is None:
        return dict(out, outcome="OX", why="no 'E exit code' line at the end")
    out["exit_code"] = code = int(m.group(1))
    if code not in (0, 1):
        return dict(out, outcome="OX", why=f"exit code {code}: no hinge value is read from this file")
    heads = [i for i, x in enumerate(lines) if x.split("  -- ")[0].rstrip() == HEAD]
    if len(heads) != 1:
        return dict(out, outcome="OX", why=f"the heading of section 5.2 occurs {len(heads)} times")
    sec = []
    for x in lines[heads[0] + 1:]:
        if re.match(r"^ 5\.\d ", x) or x.startswith("BLOCK ") or x.startswith("COVERAGE"):
            break
        sec.append(x)
    for k, rx in ROWS.items():
        hit = [(x, rx.match(x)) for x in sec if rx.match(x)]
        if len(hit) != 1:
            return dict(out, outcome="OX", why=f"the row of {k} occurs {len(hit)} times in section 5.2")
        out["lines"][k] = hit[0][0].split("  -- ")[0]
        out["values"][k] = Decimal(hit[0][1].group(1)) + 0      # "-0.00" becomes 0.00
    end = lines.index("CROSS-CHECKS") if "CROSS-CHECKS" in lines else len(lines)   # the summary counts are not rows
    for name in XC_NEEDED:
        rows = [x for x in lines[:end] if x.startswith(f"  {name}: ")]
        out["xc"][name] = {"rows": len(rows), "ok": not any("cross-check failed" in r for r in rows)}
    if code == 1 and not all(v["ok"] for v in out["xc"].values()):     # section 5a item 3; exit 0: item 2
        bad = [k for k, v in out["xc"].items() if not v["ok"]]
        return dict(out, outcome="OX", why="not evaluable: " + ", ".join(bad) + " carries 'cross-check failed'")
    s1, s2 = out["values"]["S1"], out["values"]["S2"]
    a = abs(s1)
    out["readings"]["S1"] = ("raw A1 is within k_BT of raw A2 at the hinge" if a <= KBT else
                             "raw A1 differs from raw A2 by between k_BT and 2 k_BT at the hinge" if a <= TWO_KBT else
                             "raw A1 differs from raw A2 by more than 2 k_BT at the hinge")
    out["readings"]["S2"] = (
        "the raw E_b of Sr is repulsive after the constrained relaxation at the m30 hinge, with a margin of k_BT "
        "for the missing far reference" if s2 > TWO_KBT else
        "repulsive on the raw value; the margin for the far reference is not met" if s2 > KBT else
        "no repulsion beyond k_BT after the constrained relaxation at the m30 hinge" if s2 >= -KBT else
        "the raw E_b of Sr is attractive after the constrained relaxation at the m30 hinge")
    if s2 > TWO_KBT and a <= KBT:
        out["outcome"] = "O1"
    elif s2 > KBT:
        out["outcome"] = "O2"
    elif s2 >= -KBT:
        out["outcome"] = "O3"
    else:
        out["outcome"] = "O4"
    out["reported_only"] = {"S2 > 25.70 (no allowance)": bool(s2 > KBT), "S2 > 72.70 (two-SD allowance)": bool(s2 > WIDE),
                            "expectation: S2 in [80, 170] and outcome O1":
                                bool(Decimal("80") <= s2 <= Decimal("170") and out["outcome"] == "O1")}
    out["why"] = "readings of section 5" + ("" if code == 0 else "; exit 1 with the four named cross-checks ok")
    return out


def show(o):
    o = dict(o); o["values"] = {k: str(v) for k, v in o["values"].items()}
    return json.dumps(o, ensure_ascii=False, indent=1, sort_keys=True)


def _text(a1, a2, d, code=0, xc="ok", drop=None, twice=None):
    rows = {"Eb_A1": f"  E_b^A1(Pb136) from k = 0 = {a1} meV  -- label; label",
            "S2": f"  E_b^A2(Pb136) = {a2} meV  -- label",
            "S1": f"  δ_Sr,m30 = E_b^A2 − E_b^A1 = {d} meV  -- label"}
    body = [v for k, v in rows.items() if k != drop] + ([rows[twice]] if twice else [])
    return "\n".join(["S2b E, hinge", "BLOCK 5. Hinge block", " 5.1 Per relaxation", "  x", HEAD] + body + [
        "  B5.step0 note", f"  XC-STEP0-C2: a: {xc}", "  XC-STEP0-C2: b: ok",
        "  E_b^A2(Pb136) − E_b^A2(Pb76) = 1.00 meV  -- not a K3 decision", " 5.3 Pb136 comparisons and MACE",
        "  XC-MACEPILOT-A1: x: ok", " 5.4 The cross-check", "  XC-K3HINGE: E_b^A2(Pb136) 1.00 meV against y: ok",
        "  XC-DSUM-HINGE: δ_Sr,m30 1.00 meV against the signed sum: ok", "", "CROSS-CHECKS",
        "  XC-STEP0-C2: 2 ok, 0 failed, 0 not evaluated", "  XC-K3HINGE: 1 ok, 0 failed, 0 not evaluated", "",
        "END", f"E exit code: {code}", ""])


def self_test():
    cases = [(("120.00", "118.00", "-2.00"), {}, "O1"), (("120.00", "51.41", "25.70"), {}, "O1"),
             (("120.00", "51.40", "0.00"), {}, "O2"), (("120.00", "90.00", "-25.71"), {}, "O2"),
             (("120.00", "25.71", "-94.29"), {}, "O2"), (("120.00", "25.70", "-94.30"), {}, "O3"),
             (("1.00", "-25.70", "-26.70"), {}, "O3"), (("1.00", "-25.71", "-26.71"), {}, "O4"),
             (("0.00", "-0.00", "-0.00"), {}, "O3"), (("120.00", "118.00", "-2.00"), {"code": 1}, "O1"),
             (("120.00", "118.00", "-2.00"), {"code": 1, "xc": "x  -- cross-check failed"}, "OX"),
             (("120.00", "118.00", "-2.00"), {"code": 0, "xc": "not evaluated here"}, "O1"),
             (("120.00", "118.00", "-2.00"), {"code": 3}, "OX"), (("120.00", "118.00", "-2.00"), {"drop": "S1"}, "OX"),
             (("120.00", "118.00", "-2.00"), {"twice": "S2"}, "OX"), (("120.00", "118.0", "-2.00"), {}, "OX"),
             (("120.00", "118.00", "−2.00"), {}, "OX")]
    bad = 0
    for args, kw, want in cases:
        got = read(_text(*args, **kw))["outcome"]
        print(f"{'ok ' if got == want else 'BAD'} {args} {kw} -> {got} (expected {want})")
        bad += got != want
    o = read(_text("120.00", "118.00", "-2.00"))
    ok = o["values"] == {"S2": Decimal("118.00"), "S1": Decimal("-2.00"), "Eb_A1": Decimal("120.00")}
    print("ok  values parsed" if ok else "BAD values parsed"); bad += not ok
    print(f"self-test: {len(cases) + 1} cases, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    o = read(open(sys.argv[1], encoding="utf-8").read())
    print(show(o))
