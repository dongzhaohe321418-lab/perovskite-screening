# S3a result: the hinge read

S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: pass. Valid far references: 1 of 2.

Written 2026-11-26. The rules are `S3A_HINGE_PLAN.md`; the evaluation record is `S3A_HINGE_EVAL.md`. Every number
below is copied from `s2b/E_hinge_output.txt` by `s3a/s3a_read.py` or by eye from the lines quoted.

## 1. The run

- E's hinge mode ran once, on 2026-11-26 at 17:03:33 UTC, at commit `00bb6616bc9d95f0ea0a45be844d65ebef026d10`, with
  the command of the record. Last line: "E exit code: 0". The rules had been pushed to the public branch before
  the run (commits `b6bacd4`, `325f606`, `00bb661`).
- The blob of `S3A_HINGE_PLAN.md` at that commit is `31e922cdc6304d319949f4e83536ab08b14c6e1e`, the blob that the
  record states. The read was made under that text.
- sha256 of the file E wrote: `5bd674acdd7596cf11f06bc9cee503fcc60b7c9a6481a5cd8f2060e5b08cac58`. The public copy
  (`4d8bb76892c978d13a8f7911f42691811707816cd8ffdfd5b1334ec69ee48650`) differs in line 84 only, where the local
  path of the private root is replaced by "<private root>"; this is the departure that the note names (section 8
  step 5). The two source-data files of the figure are unedited.

## 2. The statistics, as printed

The three lines of section 5.2 of the output:

```
  E_b^A1(Pb136) from k = 0 = 120.48 meV
  E_b^A2(Pb136) = 132.27 meV
  δ_Sr,m30 = E_b^A2 − E_b^A1 = 11.79 meV
```

- S2 = 132.27 meV. S1 = 11.79 meV. Both are raw values at one site of the pilot host m30.

## 3. Readings and outcome (rules of section 5 of the note; end state: exit 0)

- On S1: "raw A1 is within k_BT of raw A2 at the hinge" (|11.79| ≤ 25.70).
- On S2: "the raw E_b of Sr is repulsive after the constrained relaxation at the m30 hinge, with a margin of k_BT
  for the missing far reference" (132.27 > 51.40).
- **Outcome O1, "supported at the hinge".** By the rule: the hinge gives no ground to place a relaxed Sr quartet
  ahead of other uses of node time. That decision is taken with the D3(BJ) study and the diagnosis of host m06, not
  by this note alone.
- The expectation stated before the read (O1, with S2 between +80 and +170 meV) is met; there is no contradiction
  to report.
- Reported only, in no reading: S2 also exceeds 25.70 meV (no allowance) and 72.70 meV (the two-standard-deviation
  allowance).

## 4. Reported, in no reading

- E_b^A2(Pb136) − E_b^A2(Pb76) = 116.00 meV, with E's label "not a K3 decision; K3 failed on validity"; it rests on
  the invalid far quartet.
- The WP2c values at this site (a different fixed geometry, q = 0): 174.31 meV raw, 129.36 meV far-referenced,
  beside E_b^A1(Pb136) = 120.48 meV and E_b^A2(Pb136) = 132.27 meV.
- q = 0 at the S2 geometry: E_b(q = 0) = 181.62 meV; E_b(q = +1) − E_b(q = 0) = −61.14 meV.
- Zero-shot MACE E_b of Sr at Pb136: 138.11 meV, beside the DFT A1 value 120.48 meV.
- The four cross-checks named in the note (XC-STEP0-C2, XC-K3HINGE, XC-DSUM-HINGE, XC-MACEPILOT-A1) are "ok".
- The per-relaxation items of relaxations 1 to 4 and the residual forces of the Pb136 single points: sections 5.1
  and 5.4 of the output. Figure: `figures/fig_s2b_e_fk_hinge.png` (rendered without the panel-alignment audit,
  which was not available on the machine that built it).

## 5. What this shows and what it does not (section 7 of the note, fixed before the read)

- It shows that at the one first-shell Sr quartet that was relaxed with DFT, the raw repulsion is still there
  after a constrained, region-restricted relaxation, and that the raw fixed-geometry value differs from the relaxed
  one by 11.79 meV, less than k_BT.
- O1 was the expected outcome, with a prior probability of about 0.78 to 0.99 on public values; it is weak
  evidence.
- The quartet is the most favourable case the project could have chosen (pilot host m30, the WP2c hinge site). It
  is one host, which is not a production host, one of the two first-shell Pb sites, one pose, PBE without D3 or
  spin-orbit coupling, n = 1.
- The values are raw. No valid far reference of Sr exists after relaxation.
- It does not show that the A1 class of Sr holds after relaxation at the eight production hosts, does not explain
  host m06, and says nothing about Cl, Cs or GA.
- No class of E changes.

## 6. After the read

The hinge values are now values read at an evaluation. They may not enter a statistic, threshold or selection of
a later pre-registration. Block 5 of E is no longer blind: the items that E listed as deferred
have now been printed.
