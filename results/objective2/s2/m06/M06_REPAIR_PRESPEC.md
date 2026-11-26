# m06 repair test: pre-specification (post hoc; changes nothing in E)

Written 2026-11-26, after the diagnosis `M06_DIAGNOSIS.md` and before any of the calculations below exists. This is
a post hoc diagnostic test with its readings fixed in advance. It is not a pre-registration in the sense of
`S2B_PLAN.md` section 7: by construction it uses values read at E (the archived energies of the m06 cells and the
tier of the other hosts). It supports no class and changes no class of E.

## 1. What is tested

The diagnosis says that host m06 is an outlier for Sr (Y_h = −0.40 meV in E, against 114.25 to 166.47 meV at the
other seven hosts) because the two Sr first-shell quartets pair a D+V cell in which the molecule FA28 has turned
with a vacancy cell in which it has not: the vacancy cells stopped on a gentle slope under the force criterion of
the relaxation. If that is right, a vacancy cell relaxed from the turned state gives an ordinary E_b.

## 2. Calculations (fixed now)

- **MACE, unchanged protocol** (the relaxation code of `scripts/46` at `e5883d5`, the same regions and settings),
  after a control that reproduces one archived relaxation:
  - V′: the vacancy cells of m06 at B124 and B136, relaxed from the turned start of the diagnosis;
  - D+V′: the Sr D+V cells at B124 and B136, built from V′ as the protocol builds a D+V start, and relaxed;
  - secondary: V′ for the seven other vacancy cells of m06 whose D+V child carries the unmatched turn (X102, X137,
    X138, X175, A92, A164, A200).
- **DFT**: one single point on each new cell (11), with the archived input of the corresponding cell changed in
  its atomic positions only; the campaign's binary, launcher and 64 MPI ranks.
- The host and the D cells are the archived ones.

## 3. Read-outs

- Primary: raw E_b′(B124) and E_b′(B136) = E[D+V′] − E[D] − E[V′] + E[host], and
  Y_h′ = mean of the two − mean of the two archived far-site values of Sr at m06 (2.98 and −5.69 meV).
- Variant, reported beside it: the same with the archived D+V cell in place of D+V′.
- Secondary, reported: the raw E_b of the eight quartets of the seven other sites with V′ in place of V and the
  archived D+V (Cl at X102, X137, X138, X175; Cs and GA at A92; Cs at A164; GA at A200).
- Geometry: the rotation of FA28 against the host in each new cell; whether the archived D+V cells pass check 5
  against V′.

## 4. Predictions of the diagnosis (stated so that they can fail)

FA28 stays turned in V′; E[V′] lies about 127 to 146 meV below E[V]; E_b′(B124) between 102 and 121 meV;
E_b′(B136) between 148 and 167 meV; Y_h′ between 127 and 146 meV.

## 5. Readings (fixed now)

Thresholds: the range of Y_h(Sr) over the other seven hosts widened by their standard deviation,
[114.25 − 20.51, 166.47 + 20.51] = [93.74, 186.98] meV; and k_BT = 25.7 meV.

- **"confirmed"**: FA28 is turned by at least 20° against the host in V′ and D+V′ at both sites, and Y_h′ lies in
  [93.74, 186.98] meV.
- **"refuted"**: Y_h′ < 25.7 meV with FA28 turned in all four new cells. The diagnosis is then wrong about the
  cause, and m06 stays unexplained.
- **"not tested"**: FA28 is not turned by 20° in one of the four new cells (the repaired state was not reached).
- **"partly"**: anything else (for example Y_h′ between 25.7 and 93.74 meV).
- The two Sr values against the narrower predicted ranges of section 4, the variant and the secondary values are
  reported and enter no reading.

## 6. What is reported with the result, and what it cannot show

- A sensitivity value: the Sr tier of E recomputed with Y_h′ in place of −0.40 meV for m06 (mean, s_Y and the
  interval by E's formula). It is labelled post hoc; E's class and interval stand.
- For the secondary sites: the repaired raw E_b beside the values of the same dopant and shell at the other hosts.
  Host m06 is not thereby made a valid host of E for Cl, Cs or GA.
- Limits: one host; the repair is chosen after seeing the data; the D cells and the host are not recomputed;
  fixed-geometry DFT as the tier itself. A "confirmed" reading shows a failure mode of the A1 protocol (an
  unfinished reorientation that check 5 does not gate within 6 Å of the site) and its size at one host. It does not
  show that no other quartet carries a smaller mismatch of the same kind.
