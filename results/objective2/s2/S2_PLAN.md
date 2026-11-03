# S2 pre-registration: first-shell binding of V_I⁺ to Ca, Cl, Cs and GA (route D, "A1 decides, A2 calibrates")

**Status: PLAN, written 2026-11-03 before any S2 energy value (MACE or DFT) existed, and revised the
same day, before its commit and still before any S2 value, after three reviews, the decisions of
the analyst (an AI assistant, to whom the PI delegated the S2 research direction on 2026-11-03;
`S2_DECISION.md`, "Who decided") on their open issues, and a review of those decisions (§20).** It
is binding from the commit that adds it together with PLAN amendment n (`dopant_shell/PLAN.md`,
"Amendment 2026-11-03n"). Later changes are appended to this file as dated amendments, never
edited in place, and each is written before any value it affects is read. Until that commit no S2
cell, pilot or production, is evaluated with MACE or DFT. Smoke tests run only on synthetic cells or on the 233-atom
reference cell `results/fa_host/fa19cs1_pb20i60_233.extxyz` and its 232-atom vacancy partner
`results/fa_host/fa19cspb20i59_232_vI.extxyz`, and their energies are discarded unread.

**Decision and rules.** `S2_DECISION.md` records the route and the reasons for it. This file holds
every rule. Where the two differ, this file governs.

**Tags.** **[R]** read from a repository file (path and section) or measured on repository structures
without any calculator; **[M]** modelling choice fixed by this plan; **[I]** interpretation or
estimate; **[MC]** Monte Carlo under stated assumptions (not a measurement); **[S]** secondary
source. [M] means a modelling choice here, as in `S2_BUILDERS_DESIGN.md`; the panel's drafts used
[M] for measured values, which carry [R] below. Paths are relative to `results/objective2/` unless
they begin with `scripts/`, `ehpc/` or `results/`. "Answer k" means answer k of
`S2_BUILDERS_DESIGN.md` §16 (the 13 builder questions of its §12).

**Symbols.**

| symbol | meaning |
|---|---|
| h, p | a host; a pilot host (m30, m05) |
| d | a dopant token: Sr, Ca, Cl, Cs, GA |
| L | sublattice: B (Pb sites), A (FA sites), X (I sites) |
| v | the vacancy site of a host: the position of its vacancy iodide (I127 in every member, §4); taken in the unrelaxed member for site distances (§4) and in the S2-relaxed host for regions and the refill check (§§4–5) [M] |
| j, f | a site (index of the host site atom); a far site |
| R_j | the free region of site j (§4) |
| F[·] | the QE free energy ("!" total energy, including −TS) of a cell, in eV |
| host, V⁺_Rj, D_j, D_j+V⁺ | the four cells of site j (§5); "⁺" marks tot_charge = +1 at DFT |
| E_b(j) | binding energy at site j (§1); positive = repulsion |
| Y_h | the per-host first-shell statistic (§1) |
| δ | the relaxation bias A2 − A1 (§11) |
| k_BT | 25.7 meV exactly, the value of PLAN criterion 2 at 298 K [M] |

## 0. Information state

- **Read before these rules were written** (by the panel, by the synthesis and by the writer of
  this file):
  - every S1 result: WP1 (pilot and production), WP2a–2e, WP3 with its adoption checks, and the post
    hoc diagnostics D1–D3 (`dopant_shell/*_RESULT.md`, `WP3_DIAGNOSTICS.md`);
  - in particular the DFT E_b of m05, m21 and m30 at the WP2c sites (`WP2C_RESULT.md`), including
    the pilot-host first-shell sites used for calibration here: Pb136 and FA128 on m30, and Pb124 on
    m05 (Sr), the site of the +36.1 meV zero-shot overestimate (§11; Pb136 and FA128 of m05 and Pb124
    of m30 have no S2 cell); and the q = +1 values of m30 at Pb136 and FA128 (`WP2D_RESULT.md`);
  - the WP1 zero-shot MACE E_b at every Pb and FA site of m30, m21 and m05
    (`dopant_shell/wp1_production/`), which include the noise-pilot sites of §8. The site rules of §4
    and §8 are fixed by distance alone; the panel notes record no use of the per-site WP1 values;
  - for production hosts drawn in §3: WP2b band single points exist for m06, m12 and m32
    (`WP2B_RESULT.md` §1), WP3 training frames for m06 and m12 (`WP3_RESULT.md` §2), and m32
    carries the WP3 test-host results (criterion 6, WP3b, MD; `WP3_RESULT.md`). No E_b of any host
    in draw ranks 1–12 (production or reserve, n = 8 or 10) exists at any level; WP1 and WP2c ran
    on m30, m21 and m05 only;
  - the builders design and implementation (`S2_BUILDERS_DESIGN.md`; `scripts/42`, `s2b-2`);
  - the panel's three proposals, two judges' notes, the refuter's notes and Monte Carlo, and the
    synthesis drafts and checks (kept off-repository in the private record folder).
- **In the repository, not cited by the panel.** The one eligible host with any E_b is m15 (draw
  rank 14): exploratory zero-shot MACE E_b at 38 of its 39 Pb and FA sites from the superseded
  protocol v1 (`dopant_shell/v1_exploratory/`, cold start, fmax 0.02 eV/Å; its README: "do not
  report as binding energies"), besides its WP2b band single points and WP3 training frames. The
  panel notes do not mention these values; the first draft of this file overlooked them, and the
  facts review found them (§20).
- **Choices made knowing those values** (disclosed):
  1. the pilot hosts m30 and m05 (m30 for WP2c/2d continuity; m05 because it carries the systematic
     zero-shot first-shell Sr overestimate, +21.7 and +36.1 meV, that m30 lacks; amendment m item 5,
     Coverage);
  2. the calibration sites (§11). On m30: Pb136 and FA128, whose S1 DFT values are known at a
     different geometry, at q = 0 (WP2c) and q = +1 (WP2d), and the migrating iodide I138. On m05:
     Pb124, the only other first-shell Pb, chosen so that the two pilot hosts together calibrate the
     whole B shell. WP2c measured Sr at Pb124 on m05 (q = 0, WP1 MACE minima, one far site), and the
     +36.1 meV zero-shot overestimate is at this site (`WP2C_RESULT.md`, Results table) [R]. The m05
     A and X sites, FA28 and I49, were drawn by the seeded rule of §11, executed once with one seed
     string before any S2 value existed; the WP1 zero-shot MACE E_b of GA at FA28 on m05 exists, as at
     every FA site, and no E_b of any kind exists at I49 (S1 placed no dopant on an X site). δ (§11)
     is a within-S2 difference on the same S2 cells and uses none of these values;
  3. the charge state q = +1 (WP2d; roadmap update 2026-10-28, consequence 2);
  4. the dopant set and the deferrals (§2), chosen knowing that GA is unresolved at both levels and
     that Sr repels at DFT on MACE geometries;
  5. the far rule "two farthest sites" (§4), chosen knowing that WP2c used one median-distance far
     site per host and that two of its GA far references are atypical at MACE level
     (`WP2C_RESULT.md`, Limitations);
  6. the planning values of §18: s_Y = 13 meV (the DFT Sr host-mean SD, WP2c) and s_δ = 10–20 meV
     (from the WP3b DFT dopant − undoped relaxation-energy differences at fine-tuned frozen minima);
     these measure only the vacancy-cell half of δ, r(D+V) − r(V), so s_δ up to about 21 meV
     (√2 × 15.0) is equally consistent with them [I];
  7. the exclusion of m21 (WP2c E_b known; WP3 checkpoint selection);
  8. the host-draw rule (§3). The panel records show one seed string and one draw. No E_b exists for
     any host in ranks 1–12; the one eligible host with (exploratory, MACE-level) E_b values, m15,
     ranks 14th and cannot enter production or the reserves (§3), so the lists could not have been
     selected on an E_b;
  9. the n-rule threshold of 20 meV (§8), set knowing the WP1 MACE far SDs (Sr 11.1, GA 28.3 meV).
- **Done for this plan on 2026-11-03, without any calculator** (geometry with ase, numpy and
  `scripts/42`; draws with the Python standard library; Monte Carlo with numpy and scipy;
  `"mace" not in sys.modules` asserted):
  - the host draw of §3, re-executed with the Python standard library;
  - a site census of all 36 members with `scripts/42` (`vacancy_context`, `list_sites`), which gives
    the site sets, far sites and distances of §4 [R];
  - the sha256 and header fields of the five downloaded UPF files (`PSEUDOPOTENTIALS_S2.md`) [R];
  - the node-hour arithmetic of §16 [I] and the power and coverage figures of §18 [MC];
  - three reviews of this file and its companions (facts; rules and statistics; feasibility and
    conformance), with their own geometry census and Monte Carlo, and the corrections they led to
    (§20);
  - the analyst's decisions on the reviews' open issues (§20): the draw of the m05 A and X
    calibration sites (§11, Python standard library, one seed string), a geometry-only census and
    admissibility build of the m05 calibration cells, the coverage Monte Carlo of §18 and the
    node-hour arithmetic of §16 for the new A2 cap;
  - a review of those decisions (consistency; numbers and statistics), with its own geometry
    census, step-ratio and Monte Carlo checks, and the corrections it led to (§20).

  The scripts and outputs of these checks are kept off-repository in the private record folder.
- **Facts recorded today (records, not S2 values).**
  - MACE-MP-0 medium (foundation file sha256 `01bfe221…`, amendment m item 2) covers Z = 16, 17,
    20 and 37, as well as 1, 6, 7, 38, 53, 55 and 82: read on the laptop from
    `calc.models[0].atomic_numbers` (89 elements). No structure was evaluated.
  - The Cl, S (`-n-` and `-nl-`), Ca and Rb pslibrary 1.0.0 files were downloaded with the PI's
    approval and are kept off-repository; they are not on the node (`PSEUDOPOTENTIALS_S2.md`).
- **Does not exist.** Any S2 cell evaluated by any calculator (MACE, DFT or other); any Cl, Ca, S or
  Rb pseudopotential on the node; any frozen-far-field DFT relaxation (WP2e′ never ran).
- **Exists, geometry only.** `scripts/42` at `s2b-2` (commit b9a6a8d; `GEOM_SHA` `58ebbd29…` pinned
  in its self-test). The T4 admissibility report of `s2b-2` is not archived in the repository;
  Stage 0 regenerates and archives it before the freeze (§17).

## 1. Question, target and decisive quantity

- **Question.** For each decisive dopant d, is V_I⁺ attracted to, repelled by, or indifferent to the
  dopant's first shell, relative to two far sites, by more than k_BT = 25.7 meV at 298 K?
  - Evidence: the thermal-relevance threshold of PLAN criterion 2 [R]. Binding is the first-order
    transport effect of a dopant (PLAN "Why"; `WP1_RESULT.md`, "What follows") [I].
- **Target θ_d.** The frozen-far-field DFT-relaxed first-shell E_b of V_I⁺ (definition below with A2
  energies), far-referenced, averaged over FA orientational disorder at one vacancy site that has the
  native Cs in its cage. It is estimated as θ̂_d = Ȳ_d + δ̄_d (A1 mean plus the A2 calibration, §14).
- **Binding energy at site j** (one host, one dopant, one level):

  E_b(j) = F[D_j+V⁺] − F[D_j] − F[V⁺_Rj] + F[host]   (positive = repulsion).

  At A2 the host term is F[host_Rj], the host relaxed in R_j (§11).
- **Per-site far-referenced value.** e_h(j) = E_b,h(j) − ½[E_b,h(f₁) + E_b,h(f₂)], with f₁, f₂ the
  far pair of §4.
- **Per-host statistic.** Y_h,d = mean over the valid first-shell sites j of e_h(j)
  = mean_j E_b,h(j) − mean_f E_b,h(f). F[host] cancels in Y_h; it is computed for the raw values.
  - Evidence: shell mean as in criterion 2 and amendment d item 3 [R]; the first-shell sites of a
    sublattice form one orbit of the cubic aristotype (8 X, 4 A and 2 B neighbours of an X site),
    so their mean estimates the disorder-averaged interaction [I]; far-referencing removes the
    site-independent offsets (amendment g item 1; `WP2C_RESULT.md`) [R].
- **Charge.** Every vacancy cell (V⁺_Rj, D_j+V⁺) is computed at tot_charge = +1; every vacancy-free
  cell is neutral.
  - Evidence: far-referenced E_b(q = +1) − E_b(q = 0) is −4.9 meV (Sr hinge) and −2.9 meV (GA near)
    at m30 (`WP2D_RESULT.md`) [R]. That q = +1 removes the 13–66 meV neutral-cell band term
    (amendment g item 1; roadmap update 2026-10-28, consequence 2) is supported by the post hoc
    WP2d diagnostic at m30 only [I]; q = +1 cells are gapped, so the failed degauss row
    (`WP2B_RESULT.md` §6) does not apply.

## 2. Dopants

| role | tokens (sublattice) | builder (`scripts/42`) | evidence |
|---|---|---|---|
| positive control | Sr (B) | `build_b`, symbol swap | fixed-geometry DFT (WP1 MACE minima, q = 0, one far site per host) first-shell E_b +95.6 to +136.7 meV at 6 sites on 3 hosts (`WP2C_RESULT.md`) [R] |
| decisive family, m = 4 | Ca (B), Cl (X), Cs (A), GA (A) | `build_b`; `build_x_atomic` with `mig="allow"`; `build_a_atomic`; `build_a_molecular` (S1 recipe) | registry (`S2_BUILDERS_DESIGN.md` §2); GA for S1 continuity (`WP1_RESULT.md`, "What follows") |
| deferred | Rb; DMA; AA; SCN | — | Rb hypothetical (t 0.818 / 0.858 < 0.875); DMA starts invert the donors (25 of 141 m30 starts with N–H···I < 3.0 Å); AA `inherit` clashes at 15 of 19 m30 sites; SCN has no admissible start at I49 or I138 (`S2_BUILDERS_DESIGN.md` §10) [R] |

- **Poses** (answers 1, 2 and 6 of `S2_BUILDERS_DESIGN.md` §16):
  - Sr, Ca: one start (the replaced Pb's position).
  - Cs: default `pb8_centroid`, centred; the six ±0.30 Å starts along ±Q enter only through the pose
    pilot (§9).
  - Cl: default centred on the replaced I; the two shifted starts (Pb–Cl 2.837 Å) enter only through
    the pose pilot. Before any shifted start is built, the 2.837 Å value is checked against Poglitsch
    & Weber 1987 on the laptop. If the source gives another Pb–Cl distance, the shifted starts use
    it, recorded in a dated note before any shifted start is built; if no value can be verified, the
    shifted starts are built at 2.837 Å with `--allow-provisional` and labelled [M] starting points
    (answer 4).
  - GA: the S1 recipe, frozen, one start (`inherit`); clash thresholds report only, absolute limits
    enforced (`S2_BUILDERS_DESIGN.md` §6).
- **Rule.** No token is added to the decisive family after any S2 value exists. An element that
  fails G1 (§7) leaves it.

## 3. Hosts

- **Pilot hosts: m30 and m05.** They carry the noise, pose and calibration pilots. Their A1 E_b
  values never enter Ȳ_d or any production value Y_h,d. The quantities measured on them enter the
  decisive rules only as stated: δ_{d,p} and δ_far (§§11, 14), a_pose,d (§9), and σ_far,d through
  gate N and the n rule (§8).
  - Evidence: m30 carries the WP2c/2d comparators; m05 carries the zero-shot first-shell Sr
    overestimate (+21.7 and +36.1 meV) that m30 lacks (amendment m item 5, Coverage;
    `WP2C_RESULT.md`) [R]; refuter objection 4 (`S2_DECISION.md` §4).
- **Eligible set (28).** m00–m35 minus {m30, m05} (pilots), minus {m04, m10, m14, m18, m27}
  (amendment m item 1′, "Isolation": "These hosts are test only, and no other frame of them is used
  anywhere"), minus m21 (WP2c E_b known; WP3 checkpoint selection).
- **Draw.** The eligible members are ordered by `zlib.crc32(("S2n-host-" + member).encode())`,
  ascending (no ties occur). **Executed 2026-11-03** (Python 3.9.6, standard library) [R]:

  | rank | member | crc32 | | rank | member | crc32 |
  |---|---|---|---|---|---|---|
  | 1 | m06 | 18472929 | | 15 | m11 | 2254863107 |
  | 2 | m02 | 108272632 | | 16 | m19 | 2294149937 |
  | 3 | m16 | 402845344 | | 17 | m09 | 2443625072 |
  | 4 | m12 | 527379129 | | 18 | m01 | 2675788354 |
  | 5 | m32 | 760825915 | | 19 | m29 | 2744164594 |
  | 6 | m26 | 858766691 | | 20 | m25 | 2854677721 |
  | 7 | m22 | 876771706 | | 21 | m35 | 3007176088 |
  | 8 | m23 | 1128614380 | | 22 | m31 | 3025148289 |
  | 9 | m33 | 1516140717 | | 23 | m34 | 3292196110 |
  | 10 | m13 | 1751652911 | | 24 | m28 | 3566702692 |
  | 11 | m17 | 1862655542 | | 25 | m20 | 3662420054 |
  | 12 | m03 | 1903373166 | | 26 | m24 | 3709983823 |
  | 13 | m07 | 1981738871 | | 27 | m08 | 3869373158 |
  | 14 | m15 | 2165030682 | | 28 | m00 | 3900340948 |

  - **n = 8:** production m06, m02, m16, m12, m32, m26, m22, m23; reserves m33, m13.
  - **n = 10:** production adds m33 and m13; reserves m17, m03.
  - These equal the synthesis draft's list.
- **Admissibility and the production list [M].** In Stage 0, before any calculator runs on any of
  them, every required cell (all 19 sites of §4 × the tokens of their sublattice, both legs, default
  poses) is built with `scripts/42 build_paired(..., partners="unrelaxed")` on the unrelaxed pool
  member of ranks 1–12. A host is admissible if no required cell raises `Inadmissible` or
  `Refused`. The production list is the first n admissible hosts in draw order; the reserves are the
  next two. If ranks 1–12 are all admissible, the lists are those above. A build failure on relaxed
  partners later (§5) makes that cell missing; it never triggers a replacement. No host is added or
  replaced once any calculator has run on a production host.
- **n.** n = 8, raised to 10 by the gate-N rule of §8. n is fixed before C3 and never changed after
  any production value exists (except by the budget cut 5 of §16, also decided before C3).
- **Hosts with earlier DFT** (recorded, not a reason to exclude): m06 and m12 (WP3 training hosts;
  WP2b bands) and m32 (WP3 test host; WP2b bands, WP3b and MD). Under amendment m item 4 the test
  hosts are "used up" for validating a model. S2 uses m32 to measure DFT values, which validates no
  model (amendment n item 3).
- **DFT-free hosts left for a later option C** (no DFT of any kind, reserves counted as used): 15 at
  n = 8 (m00, m01, m03, m07, m09, m11, m17, m19, m24, m25, m28, m29, m31, m34, m35), 13 at n = 10
  [R: 22 DFT-free members, `WP2B_RESULT.md` §1 and amendment m item 1′].
- **Scope statement.** Every member has the same vacancy iodide (I127) and the native Cs in its
  vacancy cage: the Cs lies 4.04–5.13 Å from the member's vacancy site, inside the A first shell
  (< 6.0 Å, §4), in all 36 members [R, census of 2026-11-03]. Measured to the reference vacancy point
  of the 233-atom reference cell instead, the range is 4.26–4.58 Å [R; the panel's judge 2 and refuter
  checks]. S2 therefore spans FA orientational disorder at one Cs-adjacent vacancy site (amendment g
  item 7; amendment m item 4, "What the test spans"), and every S2 value is labelled "Cs-adjacent
  V_I⁺".

## 4. Sites and regions

- **Distances.** True minimum image (`ase.geometry.find_mic`) from the unrelaxed host site atom to
  the member's own vacancy position v, as returned by `scripts/42 vacancy_context` (the iodide nearest
  the reference vacancy point, found with `pp.build_pair` and checked with find_mic)
  (`S2_BUILDERS_DESIGN.md` §§1, 3). "Unrelaxed host" means the pool member file as stored.
- **Eligible sites** (`scripts/42 list_sites`): B every Pb (20); A every intact FA carbon (19; the
  native Cs excluded); X every I except the vacancy iodide (59). No range cut is applied, as in
  `scripts/29` [M]. (`S2_BUILDERS_DESIGN.md` §12 question 9 mentions "up to 12 Å (as in 29)";
  `scripts/29` has no cut, and the farthest X site lies at 12.33–13.03 Å over the pool [R]. Answer 9
  records this.)
- **Ranking.** Sites are ranked by distance rounded to 10⁻⁶ Å; ties go to the lower index (as
  amendment g item 5) [M]. Near-ties occur but no exact tie: the second and third farthest A sites
  differ by 0.0028 Å in m20, the two farthest A sites by 8 × 10⁻⁶ Å in m00, and on m30 the fourth
  farthest Pb (Pb148) leads the fifth (Pb112) by 0.0006 Å [R]. The rounding and lower-index rules
  decide no current set; they are fixed for reproducibility.
- **First shell.**
  - B: the Pb with d < 5.0 Å (amendment d item 1). Over the pool: {Pb124, Pb136} in all 36 members,
    3.17–3.41 Å; the next Pb lies at ≥ 6.72 Å [R].
  - A: the FA with d < 6.0 Å (amendment d item 1; the fourth cage A site is the native Cs). Over the
    pool: {FA28, FA92, FA128} (carbon indices) in all 36 members, ≤ 5.46 Å; the next FA lies at
    ≥ 7.22 Å [R].
  - X: the 8 nearest I, which lie below the 5.12–5.48 Å gap (8th I ≤ 5.119 Å, 9th ≥ 5.484 Å over
    the pool) [R; `S2_BUILDERS_DESIGN.md` §11]. Over the pool: {I49, I53, I90, I102, I125, I126,
    I137, I138} in all 36 members. It always contains the migrating iodide of `scripts/22` (the I
    nearest v after deletion), which varies by host (I126 in 9, I53 in 8, I138 in 7, I49 in 7, I90 in
    2, I125 in 2, I102 in 1 member) [R]; it is built with `mig="allow"`, and such cells never reach a
    path builder (answer 8).
  - The implementation recomputes these sets per host and stops if a set differs from the lists
    above or if the stated gaps are violated [M].
- **Far pair.** The 2 farthest sites of the sublattice, f₁ (farthest) and f₂. They must lie beyond
  8.5 Å (B; amendment c item 3) or 9.0 Å (A; amendment d item 1; X [M]); over the pool the far
  pairs lie at ≥ 11.45 Å (B), ≥ 10.33 Å (A) and ≥ 11.40 Å (X) [R]. The noise pilot (§8) uses the 4
  farthest (≥ 9.73, 10.14 and 10.45 Å over the pool) [R].
- **No mid shell** in S2. 19 sites per host: B 2 + 2, A 3 + 2, X 8 + 2.
- **Executed site lists** [R, census of 2026-11-03; recomputed and asserted by the implementation]:

  | host | role | migrating I | Cs–v (Å) | B far pair (Å) | A far pair (Å) | X far pair (Å) |
  |---|---|---|---|---|---|---|
  | m30 | pilot | I138 | 4.52 | 76 (11.81), 172 (11.55) | 188 (11.25), 164 (10.87) | 175 (12.77), 186 (11.91) |
  | m05 | pilot | I53 | 4.25 | 76 (11.96), 172 (11.47) | 188 (10.86), 164 (10.48) | 175 (12.95), 222 (11.99) |
  | m06 | rank 1 | I53 | 4.22 | 76 (11.77), 172 (11.68) | 200 (10.96), 164 (10.69) | 175 (12.93), 222 (12.00) |
  | m02 | rank 2 | I126 | 4.35 | 76 (11.93), 172 (11.53) | 188 (10.91), 152 (10.87) | 175 (12.70), 186 (11.81) |
  | m16 | rank 3 | I138 | 4.54 | 76 (11.86), 172 (11.58) | 164 (10.80), 188 (10.79) | 175 (12.86), 222 (11.93) |
  | m12 | rank 4 | I126 | 4.17 | 76 (11.96), 172 (11.53) | 68 (10.96), 200 (10.56) | 175 (12.79), 222 (11.95) |
  | m32 | rank 5 | I49 | 4.42 | 76 (11.90), 172 (11.70) | 200 (10.65), 188 (10.57) | 175 (13.02), 222 (11.94) |
  | m26 | rank 6 | I126 | 4.08 | 76 (11.97), 172 (11.54) | 68 (11.12), 164 (10.94) | 175 (12.77), 222 (11.40) |
  | m22 | rank 7 | I53 | 4.54 | 76 (11.79), 172 (11.70) | 16 (10.56), 4 (10.56) | 175 (12.77), 186 (11.83) |
  | m23 | rank 8 | I90 | 4.44 | 172 (11.84), 76 (11.70) | 200 (10.71), 4 (10.48) | 175 (12.84), 186 (11.92) |
  | m33 | rank 9 | I126 | 4.20 | 76 (11.94), 172 (11.59) | 68 (10.87), 200 (10.73) | 175 (12.33), 222 (11.71) |
  | m13 | rank 10 | I126 | 4.15 | 76 (11.86), 172 (11.46) | 188 (10.60), 164 (10.52) | 175 (12.64), 222 (11.79) |
  | m17 | rank 11 | I138 | 4.04 | 76 (11.93), 172 (11.59) | 200 (10.65), 188 (10.62) | 175 (12.79), 222 (11.69) |
  | m03 | rank 12 | I53 | 4.16 | 76 (11.96), 172 (11.67) | 188 (10.75), 68 (10.40) | 175 (13.00), 222 (11.95) |

  Four farthest sites on the pilot hosts (noise pilot, §8):

  | host | B | A | X |
  |---|---|---|---|
  | m30 | Pb76, Pb172, Pb24, Pb148 | FA188, FA164, FA176, FA200 | I175, I186, I222, I174 |
  | m05 | Pb76, Pb172, Pb24, Pb64 | FA188, FA164, FA152, FA68 | I175, I222, I186, I174 |

- **Region R_j [M, from the WP3b construction].** One region per (host, site), fixed on the
  S2-relaxed host (§5) and shared by every cell of that site, whatever the dopant or pose:
  - **Centres.** The relaxed-host positions of the vacancy iodide (I127) and of the site atom j.
  - **Atoms.** Every inorganic atom (Pb, I, Cs) whose relaxed-host position lies within 6.0 Å (true
    MIC) of either centre. Organic molecules (found by bonding, `scripts/38 molecule`) are free or
    fixed whole, by the distance of their carbon. Every dopant atom is always free.
  - **Transfer.** The region is a set of host indices. It is carried into each cell by that cell's
    index map (host → V: j → j for j < 127, else j − 1; host or V → doped: `old_to_new` of
    `scripts/42`). Deleted atoms drop out; appended dopant atoms are free.
  - **Record.** `region_id` = sha256 of the canonical JSON of {member, site, sorted free host
    indices}; every cell record carries it.
  - **Fixed atoms** stay at their relaxed-host positions in every cell (ASE `FixAtoms` at A1; QE
    `if_pos = 0 0 0` at A2).
  - Evidence: WP3b construction (amendment m item 4; `WP3_RESULT.md` §5); WP2e′ (amendment l item 4)
    [R]. The per-atom cut of `scripts/29 --freeze-beyond` is not used (amendment m item 4, Scope).
    Using one region for all cells of a site removes the region-size term between legs (refuter
    objection 6) [I].

## 5. Geometry protocol (A1 geometries)

- **Model.** Zero-shot MACE-MP-0 medium, used only to generate geometries; its energies decide
  nothing (amendment n item 2).
  - The foundation file loaded by `mace_mp(model="medium")`, sha256
    `01bfe22100139f424713cf921144e5509cbe353d67aa9fa1be9c6e1e0ed35845` (amendment m item 2). The node
    copy must have this hash.
  - mace-torch 0.3.16, `default_dtype="float64"`, `device="cpu"`. Versions of ase, numpy, torch and
    e3nn are recorded per campaign [M].
  - Six threads per relaxation and at most ten concurrent relaxations (as WP3b, `WP3_RESULT.md` §5)
    [M]. The thread count is recorded with every relaxation.
  - The fine-tuned WP3 model is not used anywhere, not even for geometry.
- **Host.** Whole-cell, fixed-cell relaxation of the pool member with `scripts/29 relax_staged`:
  FIRE (ASE defaults), stages fmax 0.02 → 0.01 → 0.005 eV/Å, at most 10 000 steps per stage, exactly
  the reference protocol of WP1 production (amendment g item 4; amendment h item 4; amendment i) [M].
  - Valid if the 0.005 stage converges. A host whose relaxation does not converge is missing for
    every dopant; it is not replaced.
  - **Determinism check (reported only).** For m30 and m05 the S2 host energy and positions are
    compared with the WP1 references (energies: `dopant_shell/wp1_production/shell_m30.json`,
    `shell_m05.json`, top-level `E_host`; positions: `v2prod/m30_host_relaxed.extxyz` and
    `v2prod/m05_host_relaxed.extxyz` in `dopant_shell/wp1_production/v2prod_structures.tar.gz`).
    S2 uses its own relaxed host in every case.
- **Cells per site j.**
  - V⁺_Rj: the relaxed host minus I127 (`pp.build_pair`, asserting that the deleted iodide is I127
    and lies within 1.2 Å of v), relaxed in R_j.
  - D_j: `scripts/42 build_paired(relaxed host, relaxed V⁺_Rj, ..., partners="relaxed")`, host leg,
    relaxed in R_j.
  - D_j+V: the V leg of the same call (the host-resolved pose evaluated in the V cell's own frame),
    relaxed in R_j from that warm start.
  - MACE is charge-agnostic, so vacancy cells are relaxed as neutral V and evaluated at q = +1 by DFT
    (§6).
  - If the V leg is `Inadmissible` on the relaxed partners, the pair is rejected and logged, and the
    site is missing for that dopant on that host.
- **Relaxation.** ASE FIRE with default parameters, one stage to fmax 0.01 eV/Å over the free atoms,
  at most 10 000 steps; every atom outside R_j held by `FixAtoms` (the WP3b reading, `WP3_RESULT.md`
  §5, "Readings stated").
- **Validity** (fail-closed; an invalid cell is never re-run with other settings):
  1. **Converged.** FIRE stops with max |F| < 0.01 eV/Å over the free atoms before the cap (ASE's
     strict test; converging on the last allowed step is not a fail).
  2. **No refill.** No X-site atom of any species (I or Cl) lies within 1.2 Å of v (relaxed-host
     position of I127) in any vacancy cell (`S2_BUILDERS_DESIGN.md` §11, row 29:358-360).
  3. **Dopant on site.** The dopant centre atom (registry, `S2_BUILDERS_DESIGN.md` §2) lies less than
     1.0 Å from its unrelaxed builder position (`scripts/29`).
  4. **Topology [M].** A graph check replaces `scripts/35 sane()`. The bond set among organic atoms
     (C, N, H), with bonds C–N < 1.6 Å, C–C < 1.7 Å and N–H, C–H < 1.25 Å (the cut-offs of
     `scripts/38` and `S2_BUILDERS_DESIGN.md` §8 V6), equals that of the unrelaxed start; no H lies
     within 1.25 Å, and no C or N within 1.6 Å, of any inorganic atom (Pb, I, Cl, Cs, Sr, Ca)
     (`BOND_CUT` of `scripts/42` defines organic pairs only, so these cut-offs are set here); no
     interatomic distance is below 0.65 Å; the composition is unchanged.
  5. **Partner check [M; new].** In each child–parent pair (D_j against host; V⁺_Rj against host;
     D_j+V against V⁺_Rj), every free atom more than 6.0 Å from the defect added in that step (the
     relaxed-host position of the site atom j for a dopant, of I127 for the vacancy; organic atoms by
     their molecule's carbon) must stay close to its parent position:
     - inorganic atoms: displacement < 0.25 Å;
     - FA: carbon displacement < 0.25 Å and rigid-body (Kabsch) rotation of the C–N–N skeleton
       < 20°, as `scripts/38` computes it.

     Within 6.0 Å the same quantities are reported, not gated. Evidence: the amendment c item 1
     bounds (< 0.25 Å, < 20°; `scripts/29`, `bok`); refuter objection 9; `WP2E_RESULT.md` (in an
     unconstrained DFT relaxation 12 of 18 FA rotate their C→N axis by > 10°, 15 of 18 by the
     Kabsch measure used here; amendment c item 1 bounded the axis rotation) [R].
- **Records.** Every cell record carries `BUILDER_VERSION`, `GEOM_SHA`, the pose id, the region id,
  the model sha256, the FIRE step count and the validity results. S2 tokens are never passed to
  `scripts/29` (`S2_BUILDERS_DESIGN.md` §11, row 29:203); the S2 driver calls `relax_staged` and
  `basin_dev`-style functions directly.
- **Labels [M].** `s2_<h>_host`; `s2_<h>_V<L><j>` (for example `s2_m30_VB136`);
  `s2_<h>_<TOKEN><j>o<k>_novac` and `..._vac`, where k numbers the distinct minima of §9 (k = 0 is
  the default pose). A2 cells use the prefix `s2r_`; q = 0 rows add `_q0`; G1, spin and throughput
  rows use the prefixes `s2g1_`, `s2spin_` and `s2tp_`. No S2 label matches a pattern of `scripts/33`
  (amendment m item 1b). S2 outputs are written under `s2/`, never under `dopant_shell/`.

## 6. DFT settings

- **Fingerprint.** The `scripts/30` fingerprint, unchanged, written by a new S2 QE writer
  (`scripts/30` itself is not edited; `S2_BUILDERS_DESIGN.md` §11):

  | setting | single points (A1, pilots, G1) | A2 relaxations (§11) |
  |---|---|---|
  | functional | plain PBE, no D3 | same |
  | pseudopotentials | the `scripts/30` PSEUDO set (Pb dn, I n, Cs spn, C n, N n, H, Sr spn; pslibrary 1.0.0 US) plus `Cl.pbe-n-rrkjus_psl.1.0.0.UPF` and `Ca.pbe-spn-rrkjus_psl.1.0.0.UPF` (sha256 in `PSEUDOPOTENTIALS_S2.md`) | same |
  | ecutwfc / ecutrho | 50 / 400 Ry (G1 also 60 / 480 Ry) | 50 / 400 Ry |
  | k-sampling | one k-point at supercell (½, ½, ½), the folded R point (`kpts (1,1,1)`, offset `(1,1,1)`) | same |
  | occupations | Gaussian smearing, degauss 0.005 Ry | same |
  | nspin | 1 (spin row of §7: 2) | 1 |
  | tot_charge | +1 for vacancy cells (0 for the q = 0 link rows of §10), 0 otherwise | same |
  | symmetry | `nosym = .true.` | same |
  | electrons | conv_thr 10⁻⁸ Ry, mixing_beta 0.3, electron_maxstep 200 | same |
  | forces | `tprnfor = .true.`, `tstress = .false.` | same |
  | calculation | `scf` | `relax`, BFGS (QE defaults otherwise) |
  | constraints | none | `if_pos = 0 0 0` for every atom outside R_j |
  | ionic thresholds | — | forc_conv_thr 7.8 × 10⁻⁴ Ry/bohr (0.02 eV/Å; amendment b); etot_conv_thr 10⁻⁵ Ry (the `scripts/30` relax branch and the WP2e input) [M] |
  | ionic configurations | — | at most 201: the start (k = 0) and 200 further (§11) |
  | disk_io | `'none'` (as `scripts/30`) | `'low'`, so that a soft exit writes restart data [M] |
  | energy used | F, the "!" total energy (free energy), −TS logged | F per ionic configuration |

- **Program.** pw.x 7.5, the build used for S1 and WP3 (version string recorded from every output).
  MPI layout: 64 ranks for single points (as WP3); 48 ranks for relaxations (as WP2e) unless the
  throughput row of §16 selects another layout before the first A2 relaxation; one layout for all 36
  relaxations [M].
- **Vacancy detection and charge** [M]. The writer counts X-site units, n_X = n(I) + n(Cl): 60 →
  vacancy-free, tot_charge 0; 59 → vacancy cell, tot_charge +1, except the q = 0 link rows of §10
  (suffix `_q0`), which are written at tot_charge 0 and nspin 1 as in WP2c; anything else → refused.
  It does not use `count("I") == 59` (`S2_BUILDERS_DESIGN.md` §11). It also asserts the
  valence-electron count from z_valence (host 1070; vacancy cells 1062 after the charge, 1063 for
  `_q0` rows; dopant shifts Sr −4, Ca −4, Cl 0, Cs −10, GA +6), which is even for every S2 cell
  except the `_q0` rows.
- **Parsing.** Single points: F and forces with `scripts/32 parse_qe` (last force block); E_F as in
  `scripts/37`. A single point counts as complete only with JOB DONE and "convergence has been
  achieved". A2 relaxations: F(k) and forces for every configuration from the concatenated outputs
  of all parts (ASE `espresso-out`, as `scripts/38`), with k continuing across restarts.
- **UPF identity.** The sha256 of every UPF on the node is checked before the first single point of
  each campaign; on a mismatch the campaign stops [M].

## 7. Elements gate G1 (campaign 1)

- **Cutoff.**
  - Cells: on the S2-relaxed m30 host, the unrelaxed host-leg cell (builder output, no relaxation) of
    Cl at I138 (default pose, `mig="allow"`) and of Ca at Pb136; neutral, nspin 1.
  - Single points: host and both doped cells at 60 / 480 Ry, and both doped cells at 50 / 400 Ry
    (the host at 50 / 400 Ry is the noise-pilot host single point): 5 single points.
  - Statistic: Δ_cut = [F₆₀(D) − F₆₀(host)] − [F₅₀(D) − F₅₀(host)].
  - Pass: |Δ_cut| ≤ 5 meV. 60 / 480 Ry equals max(60 / 480 Ry, the suggested cutoffs), since every
    suggested cutoff is lower (`PSEUDOPOTENTIALS_S2.md` §2) [R].
  - Evidence: the bound proposed in `S2_BUILDERS_DESIGN.md` §11 [M]; at fixed composition a
    far-referenced E_b cancels the substitution-energy cutoff error to first order [I].
- **Valence.** z_valence of the node copy equals the registry value (Cl 7, Ca 10). The header values
  already match (`PSEUDOPOTENTIALS_S2.md` §2); on the node this is verified through the sha256.
- **Spin [M for the cells and the seed].**
  - Cells: the noise-pilot D_f+V⁺ cell at the farthest site of m30 for each element (Cl at I175, Ca
    at Pb76), at its A1 geometry and q = +1, recomputed at nspin 2; its nspin-1 value is the noise-pilot
    single point.
  - Seed: `starting_magnetization` = 0.1 for every species, as in the S1 nspin-2 row
    (`dopant_shell/wp2b/raw/zz_settings/set_m30u_img0_nspin2.in.gz`). The dopant atom is its own
    species with `starting_magnetization` = 1/z_valence (Cl 1/7, Ca 1/10), an initial moment of
    about 1 μB [M]. The writer sets and asserts these values in the input, whatever the ASE version:
    the S1 input carries 0.1 for every species [R], because ASE 3.29 writes an initial moment
    unscaled as `starting_magnetization`, which QE reads as a fraction of the valence charge [S], so
    a moment of 1.0 would fully polarise the dopant.
  - Pass: |F(nspin 2) − F(nspin 1)| ≤ 3 meV and total magnetisation |M| < 0.1 μB per cell (absolute
    magnetisation reported).
  - Evidence: amendment c item 6 used 3 meV; the nspin-1 premise is untested for doped V cells
    (`S2_BUILDERS_DESIGN.md` §2) [R].
- **Fail.** An element that fails any part leaves the decisive family (control C3, §14). Its
  production and A2 cells are not run [M]; its pilot values are reported. No setting is changed to
  rescue it; a later amendment may schedule it at a new fingerprint.

## 8. Noise pilot and gate N (campaign 1)

- **Design.** On each pilot host, at the 4 farthest sites of each sublattice (§4 table):
  - one host single point;
  - V⁺_Rf for each of the 12 sites;
  - D_f and D_f+V⁺ for Sr and Ca at the 4 B sites, Cs and GA at the 4 A sites, and Cl at the 4 X
    sites (40 cells), default poses.

  That is 2 × (1 + 12 + 40) = 106 single points and 2 × 52 frozen MACE relaxations.
- **Statistic.** For each dopant d, from the raw E_b,p(f) of its valid far sites on the two pilot
  hosts:

  σ²_far,d = Σ_p Σ_f [E_b,p(f) − Ē_p]² / Σ_p (k_p − 1),

  where Ē_p is the mean over the k_p valid sites of host p; a host with k_p < 2 contributes nothing
  (df = 6 when all 16 cells are valid). Reported with the host offsets Ē_p, every per-site value,
  and the zero-shot MACE values of the same cells (labelled "zero-shot MACE, not re-admitted").
- **Gate N.**
  - σ_far,d ≤ 25 meV: d stays decisive.
  - σ_far,d > 25 meV, or df < 3 [M]: d is "inconclusive below the DFT noise floor". Its production
    and A2 cells still run and are reported; it receives no class at either tier.
  - If Sr fails (σ_far,Sr > 25 meV or df < 3), the protocol stops before A2 and is re-planned by a new
    amendment.
  - Evidence: criterion 1's SD < 25 meV [R]; MACE far SD 11.1 meV (Sr) and 28.3 meV (GA)
    (`WP1_RESULT.md`) [R]; no DFT noise floor exists (`WP2C_RESULT.md`, Limitations) [R]; refuter
    objection 2.
- **n rule [M for the exact wording].** n = 10 if any member of the decisive family that passes gate
  N (and G1) has 20 meV < σ_far,d ≤ 25 meV; otherwise n = 8. Sr and dopants that fail gate N or G1 do
  not change n.
  - Evidence: once the calibration term is included, n = 10 changes the class thresholds by −5.2 to
    +0.2 meV [I, analytic; §18]; the roadmap's S3 row states that "current host noise suggests ≥ 10"
    hosts [R]. The 20 meV threshold was set knowing the WP1 MACE far SDs (§0, choice 9).
- **Status.** Pilot-host E_b values never enter Ȳ_d; σ_far,d enters only through gate N and the n
  rule.

## 9. Pose pilot (campaign 1, m30)

- **Sites and starts.**
  - Cs at FA128 (the nearest FA) and at FA188 (the farthest FA): the centred `pb8_centroid` start
    and every admissible ±0.30 Å start (`resolve_poses`; at most 7 per site).
  - Cl at I138 (the migrating iodide, `mig="allow"`) and at I175 (the farthest I): the centred start
    and the two shifted starts.
- **Cells.** For every start both legs: D on the S2-relaxed host and D+V on the relaxed V⁺_R of the
  same site (V⁺_R(FA128) and V⁺_R(I138) are A2 start-set cells, §11; V⁺_R(FA188) and V⁺_R(I175) are
  noise-pilot cells). MACE relaxation and validity as §5. The default-pose cells at FA128 and I138 are
  the A2 start-set cells and those at FA188 and I175 are the noise-pilot cells; they are reused, not
  relaxed again [M].
- **Distinct minima (geometry only; no MACE energy is used).** Per leg, the valid relaxed starts are
  taken in start order (default first). A minimum is kept as distinct if, against every minimum kept
  before it, some dopant atom differs by more than 0.25 Å, or some free FA differs by more than
  0.25 Å (carbon) or 20° (Kabsch rotation of C–N–N) [M]. Each kept minimum gets one DFT single point
  (q = +1 for D+V), except the far-site default cells, whose noise-pilot single points are reused. At
  most 40 single points, fewer where minima coincide or cells are reused.
- **Aggregate.** Per leg, F_leg = F_min − k_BT ln Σ_i exp(−(F_i − F_min)/k_BT) over the kept minima
  i (k_BT = 25.7 meV). Δ_pose(j) = E_b(default, j) − E_b(Boltzmann, j)
  = [F_def(D+V) − F_leg(D+V)] − [F_def(D) − F_leg(D)]; the V⁺ and host terms cancel.
  - The numbers of kept minima per leg, N_D and N_D+V, and the count term k_BT ln(N_D/N_D+V) (at
    most ±50.0 meV for Cs, ±28.2 meV for Cl) are reported beside every Δ_pose and aggregated E_b
    [I]: when the legs keep different numbers of near-degenerate minima, the aggregate carries this
    term, which depends on the start set as well as on the energy landscape.
- **Rule, per token (Cs, Cl).**
  - |Δ_pose| ≤ 10 meV at both sites: production uses the default pose, and the allowance
    a_pose,d = max(|Δ_pose(near)|, |Δ_pose(far)|, |Δ_pose(near) − Δ_pose(far)|) is added to every
    interval of d (§14); the last term is the pose residual of the far-referenced value [M]. (With
    Δ_pose(near) = +10 and Δ_pose(far) = −10 meV the default pose biases e_h(j) by 20 meV, which the
    larger single-site residual alone would not cover.)
  - Otherwise: every admissible start is relaxed in production, distinct minima are found as above
    and each leg is aggregated as above; a_pose,d = 0. Cost: at most 100 extra single points per host
    (Cs 5 sites × 2 legs × 6; Cl 10 × 2 × 2), about 11.2 node-h per host [I].
  - If the default minimum of either leg is invalid at either pilot site, the rule is treated as not
    met (fail-closed) [M].
  - Sr, Ca and GA have one start: a_pose = 0. For GA this is labelled "S1 recipe; pose dependence not
    measured" (answer 2).
  - Evidence: Proposal 2 and the judges; `S2_BUILDERS_DESIGN.md` §12 question 6; 10 meV ≈ 0.4 k_BT.

## 10. q = 0 link rows (campaign 1, reported only)

- The 10 vacancy cells of the m30 A2 start set (§11) at q = 0, at their A1 geometries: V⁺_R and the
  D+V of Sr and Ca at Pb136; V⁺_R and Sr D+V at Pb76; V⁺_R and Cl D+V at I138; V⁺_R and the D+V of
  Cs and GA at FA128. 10 single points.
- Reported beside the q = +1 values, labelled; no decision rests on them. Evidence: WP2d continuity.

## 11. A2 calibration (campaigns 2 and 4)

- **Calibration sites (one first-shell site per sublattice on each pilot host; the sites differ
  between the two hosts) [M].**
  - m30: B the hinge Pb, Pb136 (the WP2c hinge on m30, m21 and m05); A FA128 (the nearest FA on
    both pilot hosts); X the migrating iodide, I138 (the `scripts/22` rule) [R].
  - m05: B Pb124, the only other first-shell Pb, so that the two pilot hosts together calibrate both
    B shell sites; A FA28 and X I49, drawn as below [R].
  - **m05 draw.** Among the first-shell sites of the sublattice on m05, excluding the site type used
    on m30 (A: FA128, the nearest FA on both pilot hosts; X: the migrating iodide, I53 on m05), the
    sites are ordered by `zlib.crc32(("S2n-cal-m05-" + label).encode())`, ascending, with labels
    "FA28", "I49" etc. (carbon index for FA). **Executed 2026-11-03** by the analyst, before any S2
    value existed, with this one seed string only (the first and only string tried), Python standard
    library [R]:
    - A: FA28 684900801, FA92 737407252 → FA28;
    - X: I49 299187232, I138 1029408902, I125 1525794170, I137 2917438743, I126 3287848128, I90
      3718773449, I102 4137890395 → I49.
  - **Admissibility on m05.** If a drawn site's required cells (both legs of each dopant of the
    sublattice, default poses) raise `Inadmissible` or `Refused` when built with
    `scripts/42 build_paired(..., partners="unrelaxed")` on the unrelaxed m05 member in the Stage-0
    check (§§3, 17), the next site in draw order is used, recorded before any calculator runs on m05
    [M]. A geometry-only build on 2026-11-03 found every required cell of Pb124 (Sr, Ca), FA28 (Cs,
    GA) and I49 (Cl, `mig="allow"`) admissible [R]. Pb124 is chosen, not drawn, and has no
    fallback; its cells, like those of FA28 and I49, were built with `s2b-2`, whose geometry is
    pinned by `GEOM_SHA`, so the Stage-0 check is expected to repeat that result [I].
  - **Census** (unrelaxed m05, true MIC to v) [R]: Pb124 3.27 Å (Pb136 3.28 Å); FA28 5.03 Å (FA128
    4.78 Å, FA92 5.11 Å); I49 4.63 Å, not the migrating iodide (I53, 4.31 Å). The regions R_j (§4
    rule) hold 70 (Pb124), 58 (FA28) and 59 (I49) host atoms on the unrelaxed member, and 70, 50
    and 59 on the WP1-relaxed m05 host.
  - Evidence: rules review F1, adopted by the analyst (§20). For B both first-shell Pb are
    calibrated, so δ̄ is the B-shell mean in expectation, and a hinge–flank difference of δ, if any,
    enters s_δ (confounded with host) without biasing δ̄. For A and X a site-type effect now enters
    s_δ, confounded with host, and is reduced but not removed in δ̄ (§18, assumption (i)).
    Assumption (i) of §18 is weakened, not removed [I].
- **Cells per region.** host_Rj and V⁺_Rj (shared by the dopants of the region), and D_j and D_j+V⁺
  per dopant: B: 2 + Sr 2 + Ca 2; A: 2 + Cs 2 + GA 2; X: 2 + Cl 2. 16 relaxations per host. Plus the
  Sr far quartet on m30 at the farthest Pb, Pb76 [M] (host_R, V⁺_R, Sr D, Sr D+V⁺): 4. Total 36.
- **Start set (C1).** The A1 geometries of the A2 cells are generated in campaign 1 by MACE as in §5:
  on each pilot host V⁺_R and the dopant cells of the three calibration regions (m30: Pb136, FA128,
  I138; m05: Pb124, FA28, I49; 13 relaxations per host); the Sr far-quartet cells at Pb76 are the
  noise-pilot cells. host_Rj starts from the S2-relaxed host.
- **Protocol.** pw.x `relax` with the settings of §6; start = the A1 geometry of the cell (for host_Rj
  the S2-relaxed host); q = +1 for V⁺ and D+V⁺; atoms outside R_j fixed.
  - Configurations are counted k = 0 (the start), 1, 2, …; at most k = 200. The pw.x `nstep` value
    that gives exactly this cap, and its value after a restart (§13), are fixed by the pw.x smoke
    tests at the start of C1 on the reference vacancy cell (§16) [M].
  - F(k) is the free energy of configuration k. Configurations carry over a restart (§13).
- **End rule.**
  - Converged by QE's criteria at k ≤ 200: accepted.
  - Not converged at k = 200: accepted only if |F(200) − F(180)| ≤ 3 meV (plateau); otherwise the
    cell is unconverged and every quartet that contains it is invalid.
  - Any other end without QE convergence before k = 200 (a BFGS failure, or an SCF not converged
    within electron_maxstep, which stops pw.x) is not an interruption (§13): the cell is
    unconverged, it is not rerun, and every quartet that contains it is invalid [M].
  - Evidence: the cap was raised from k = 120 to k = 200 by the analyst (feasibility review F2,
    §20). Under a lognormal fit to the WP3b frozen/unconstrained FIRE step ratios applied to WP2e's
    282 BFGS steps, a relaxation needs more than 200 steps with probability about 0.0012 at the
    fitted parameters (more than 120: 0.12), and about 0.019 (more than 120: 0.17) when the
    uncertainty of the six-point fit is included (posterior predictive) [I; planning estimate
    resting on the unverified FIRE-to-BFGS transfer; §20, D2]. In WP2e (whole cell) F still fell by
    16.3 meV over configurations 180–200, and |F(k) − F(k − 20)| ≤ 3 meV held at no configuration
    before it converged at configuration 282 (`dopant_shell/wp2e/wp2e_trajectory_m30_GA_img0.csv`)
    [R], so a relaxation that reaches the cap will usually fail the plateau [I].
- **Validity on the final geometries.** §5 checks 2–5 (no refill, dopant on site, topology, and the
  partner check between the final geometries of child and parent cells: D against host_R, V⁺_R
  against host_R, D+V⁺ against V⁺_R). A quartet is valid if its four relaxations are accepted and
  valid.
- **δ.** For dopant d on pilot host p, at the calibration site j of d's sublattice:

  δ_{d,p} = E_b^A2(j) − E_b^A1(j),

  with E_b^A2 from the final F of the four relaxations and E_b^A1 from their k = 0 F (so δ is the
  sum of the four relaxation energies with the signs of E_b).
  - δ_far = the same at the m30 Sr far quartet (Pb76).
  - For a token whose production is multi-pose (§9), δ is measured on the default-pose cells only;
    its calibrated value θ̂_d is labelled "calibration at the default pose", and Δ_pose of the m30
    pose pilot at the m30 calibration site (FA128 for Cs, I138 for Cl) is reported beside it; the
    m05 calibration sites FA28 and I49 have no pose pilot [M].
- **Order (fixed).**
  - **C2** (m30): V⁺_R(Pb136) [K2]; host_R(Pb136); Sr D(136); Sr D+V⁺(136) [cost projection];
    Sr far quartet at Pb76: host_R, V⁺_R, Sr D, Sr D+V⁺ [K3]; Ca D(136); Ca D+V⁺(136).
  - **C4:** m30 X region (I138: host_R, V⁺_R, Cl D, Cl D+V⁺); m30 A region (FA128: host_R, V⁺_R,
    Cs D, Cs D+V⁺, GA D, GA D+V⁺); m05 B region (Pb124: host_R, V⁺_R, Sr D, Sr D+V⁺, Ca D, Ca D+V⁺);
    m05 X region (I49: 4); m05 A region (FA28: 6). 26 relaxations.
- **Step-0 equivalence check.** In C1, standalone single points of m30 V⁺_R(Pb136) and Sr
  D+V⁺(Pb136) at their A1 geometries. At k = 0 of the corresponding C2 relaxations, |F(k = 0) −
  F(single point)| ≤ 0.5 meV is required [M for the tolerance].
  - A failure stops A2 before the next relaxation starts. It is treated as a writer or input error;
    after a fix that changes no rule (recorded in a dated note), the check is repeated once on the
    same cells. If no error is found, or if the repeated check fails, A2 stops and S2 reports the A1
    tier only, as under K2.
- **Gates.**
  - **K2 (cost kill).** The first relaxation, m30 V⁺_R(Pb136), must be accepted by the end rule.
    Otherwise A2 stops, S2 reports the A1 tier only, and any further A2 needs a new amendment.
  - **Cost projection** after the first 4 relaxations: §16.
  - **K3 (control after relaxation).** E_b^A2(Pb136) − E_b^A2(Pb76) for Sr on m30 must exceed
    +25.7 meV. If it does not, or if either quartet is invalid by validity checks 2–5, A1 is not
    admissible as a proxy: A2 and production stop and S2 is re-planned (fail-closed) [M]. If either
    quartet is invalid only because a relaxation failed the end rule, K3 cannot be evaluated; A2
    stops, and C3 runs and S2 reports the A1 tier only, as under K2 [M].
  - **Separability (evaluated after C4).** If |δ_far| > t_{df_δ}(0.975)·s_δ (§14), the allowance
    a_far = |δ_far| is added to every calibrated interval; otherwise a_far = 0. If the far quartet is
    invalid, no dopant receives a validated class (C5 fails) [M]; in practice K3 has already stopped
    A2 in that case.
    - Evidence: the far-site relaxations separate to first order only where S(v, 6 Å) and
      S(f, 6 Å) are disjoint, i.e. for f more than 12.0 Å from v [I]; over the pool this holds for
      every farthest X site (12.33–13.03 Å) but for no A far site (10.33–11.25 Å), for no B f₂
      (11.45–11.78 Å) and for only 4 of 36 B f₁ (11.73–12.15 Å) [R, census of 2026-11-03]. The
      test uses Sr at Pb76 on m30 (11.81 Å) and does not test the A or X sublattice or any other
      dopant. Under δ_far ~ N(0, s_δ) the allowance fires in about 5% of realisations; under a far
      bias of mean 10 / 20 meV the coverage of the nominal 98.75% interval is 0.95 / 0.85 with this
      rule [MC, review of 2026-11-03]; refuter objection 6.
  - Evidence for the whole rule: refuter objection 1 (one host cannot bound the bias); the WP3b DFT
    dopant − undoped relaxation-energy differences at fine-tuned frozen minima have RMS 15.0 meV,
    against 47.6 meV unconstrained (recomputed from `WP3_RESULT.md` §5: +21.8, −10.2, +7.2, +16.5
    and +76.3, −45.4, −3.9, +34.1 meV) [R]; the power figures of §18 [MC].

## 12. Production (campaign 3)

- **Hosts.** The production list of §3 (n = 8 or 10).
- **Per host.** One whole-cell host relaxation and 75 frozen relaxations (19 V⁺_Rj; Sr and Ca at the
  4 B sites, Cs and GA at the 5 A sites, Cl at the 10 X sites: 56 dopant cells), then 76 single
  points (host 1, V⁺ 19, Sr 8, Ca 8, Cs 10, GA 10, Cl 20). Multi-pose tokens (§9) add up to 100
  single points per host.
- **Completeness** (amendment m item 1d, adapted).
  - A QE job without JOB DONE is resubmitted once with the identical input; if the retry also ends
    without JOB DONE, the cell is missing.
  - A JOB DONE single point whose SCF did not converge is missing; it is not rerun (amendment m item
    1d: "A frame whose SCF does not converge is dropped").
- **Valid quartet.** Its four cells are complete, and the three MACE relaxations and the host
  relaxation are valid (§5).
- **Valid host for dopant d.** Both far quartets of d are valid, and so are, on d's sublattice, 2 of
  the 2 (B), at least 2 of the 3 (A) or at least 6 of the 8 (X) first-shell quartets. Y_h then
  averages the valid first-shell sites. n_d denotes the number of valid hosts for d.
- **Dopant-specific failures [M].** A failure is dopant-specific if a D_j or D_j+V cell fails §5
  check 2, 3 or 5 (or the A2 checks of §11) while V⁺_Rj and the host of that site are valid. If, for
  dopant d, dopant-specific failures occur at one first-shell site on more than a quarter of the
  production hosts, or in more than 10% of d's first-shell cells over all production hosts, d
  receives no class at either tier and is reported as "first shell not stable under the S2
  protocol", with the failed geometries described. (These checks are most likely to fail where the
  interaction is strongest, for example Cl at the migrating iodide moving into the vacancy, so
  treating such failures as missing at random would bias Y_h towards zero.)

## 13. Interruptions

- **MACE relaxations.** A relaxation stopped by a spot reclaim, node loss, OOM or wall time is rerun
  from the start with the identical script, model, seed, input and thread count, at most twice;
  partial outputs are discarded unread (amendment m item 4 (d), "Interrupted jobs").
- **Single points** follow §12: one resubmission with the identical input (amendment m items 1d and
  4 (d)); a job the queue gives up on is missing, and so is a JOB DONE output whose SCF did not
  converge (not rerun).
- **A2 relaxations.**
  - On a spot termination notice the driver creates `<prefix>.EXIT` in `outdir`, so that pw.x stops
    cleanly and writes its restart data (QE `INPUT_PW` [S]; that pw.x 7.5 honours it with
    `disk_io = 'low'` is confirmed by the pw.x smoke tests at the start of C1, §16) [M].
  - The run then continues with `restart_mode = 'restart'` and the same MPI layout. Its input
    differs from the original only in `restart_mode` and in `nstep`, set to the configurations
    still allowed (201 minus those completed; the interrupted one is not counted as completed; the
    exact mapping is fixed by the smoke tests, since `nstep` counts the steps of one run [S]). The
    BFGS history is kept and the configuration count continues. The driver also stops, by the exit
    file in `outdir`, any part that reaches k = 200, and never reads a configuration beyond it [M].
  - Without usable restart data the relaxation is rerun from the start with the identical input, at
    most twice; partial outputs are discarded unread.
  - Each interruption is logged with its configuration index, time and cause.
  - Evidence: refuter objection 10; the notice came about 5 min before termination in the WP3 run
    (`WP3_RESULT.md` §5, run record), and one ionic step takes 6.15 min (WP2e) [R].
- None of these is a fail. A cell that still has no complete output is missing; this is never
  resolved by changing settings.

## 14. Decisive statistics and classes (rule V)

All statistics use unrounded values; results are reported to 0.1 meV. SD uses ddof = 1. t_ν(q) is the
q-quantile of Student's t with ν degrees of freedom (non-integer ν allowed). The family quantile is
q* = 1 − 0.05/(2·4) = 0.99375 (two-sided Bonferroni over the 4 decisive dopants); the control uses
the same quantile.

- **A1 tier** (reported, pre-registered, never called "validated"), for each d with n_d ≥ 2:
  - Ȳ_d = mean of Y_h,d over the n_d valid hosts; s_Y,d their SD.
  - I^A1_d = Ȳ_d ± (t_{n_d−1}(q*)·s_Y,d/√n_d + a_pose,d) [M: the pose allowance is carried at both
    tiers].
  - Classes as below with Ȳ_d, I^A1_d and the host values Y_h,d. Label: "fixed-geometry DFT;
    relaxation bias not bounded".
- **Calibrated tier.**
  - m_d = the number of valid δ_{d,p} (0, 1 or 2); δ̄_d = their mean.
  - s²_δ = Σ_d Σ_p (δ_{d,p} − δ̄_d)² / df_δ, with df_δ = Σ_d (m_d − 1) over the five dopants with
    m_d ≥ 1 (Sr included).
  - θ̂_d = Ȳ_d + δ̄_d; a = s²_Y,d/n_d; b = s²_δ/m_d; SE_d = √(a + b).
  - ν_d = (a + b)² / (a²/(n_d − 1) + b²/df_δ) (Welch–Satterthwaite).
  - t*_d = t_{ν_d}(q*).
  - I_d = θ̂_d ± (t*_d·SE_d + a_far + a_pose,d).
- **Classes** (at either tier, with the tier's interval and host values):
  - **"repels"**: I_d lies entirely above +25.7 meV, and the calibrated host values Y_h,d + δ̄_d (A1
    tier: Y_h,d) are positive in at least ⌈0.75 n_d⌉ hosts (6 of 7 or 8; 7 of 9; 8 of 10);
  - **"binds"**: the mirror image (I_d entirely below −25.7 meV; negative in ≥ ⌈0.75 n_d⌉ hosts);
  - **"no first-shell interaction beyond k_BT"**: I_d lies inside (−25.7, +25.7) meV and the
    Boltzmann shell value of the tier, G_d (heterogeneity flag below), lies above −25.7 meV [M]
    (without the G_d condition one X site at −80 meV among eight is never flagged, and the class is
    awarded with probability 0.42–0.60 at A1 and 0.30–0.41 calibrated; with it, 0.06–0.12, with no
    measurable change at θ = 0 [MC, review of 2026-11-03]);
  - otherwise **"not resolved"**, reported with the upper bound U_d = |θ̂_d| + t*_d·SE_d + a_far +
    a_pose,d (A1 tier: |Ȳ_d| + t_{n_d−1}(q*)·s_Y,d/√n_d + a_pose,d).
- **Heterogeneity flag** (both tiers).
  - Ē_d(j) = mean of e_h(j) over the valid hosts for d (§12) at which site j is valid, plus δ̄_d at
    the calibrated tier; k = the number of first-shell sites with at least one such host. Adding
    δ̄_d shifts G_d and mean_j Ē_d(j) equally, so the flag is the same at both tiers.
  - G_d = −k_BT ln[(1/k) Σ_j exp(−Ē_d(j)/k_BT)].
  - If |G_d − mean_j Ē_d(j)| > k_BT, the shell is "heterogeneous": no class is awarded, and the
    per-site values Ē_d(j) are reported with t_{n_j−1}(0.975) intervals (n_j valid hosts at site j).
  - Evidence: refuter objection 3. Noise alone shifts G by about −σ²/(2k_BT) ≈ −1.5 meV at a per-site
    host-mean noise of σ = 8.8 meV (25/√8) [I]. With one trapping site and the others at 0 the flag
    fires only beyond a trap depth of 85.2 meV (k = 2), 77.3 meV (k = 3) or 83.4 meV (k = 8)
    (arithmetic of the flag formula); shallower traps are caught, for the null class, by the G_d
    condition above.
- **Controls (fail-closed), calibrated tier.**
  - **C1 (global).** Sr is classified "repels" at the calibrated tier, with C2, C4 and C5 passing for
    Sr and no heterogeneity flag. Otherwise no dopant receives a validated class.
  - **C2 (noise).** d passed gate N (§8), and over its valid production hosts the far-pair
    differences Δ_h = E_b,h(f₁) − E_b,h(f₂) satisfy SD(Δ_h)/√2 < 25 meV and |mean(Δ_h)| < 15 meV
    (the criterion-1 analogue; Proposal 2).
  - **C3 (elements).** G1 passed for d's element (Cl, Ca). Sr, Cs and GA contain only S1 elements and
    pass by definition.
  - **C4 (hosts).** n_d ≥ n − 1.
  - **C5 (calibration).** m_d ≥ 1, df_δ ≥ 3, |δ̄_d| ≤ 50 meV (Proposal 2's admission bound), and
    δ_far valid.
  - **Pose.** If the pose rule required multi-pose production for d and budget cut 6 or 7 of §16
    removed it, d receives no class at either tier ("pose-dependent; not classified").
- **Validated class.** A class of rule V at the calibrated tier, with C1–C5 passing and no
  heterogeneity flag. It validates the class, not the value; values are reported as θ̂_d with I_d.
  It carries the label of `S2_DECISION.md` §7.
- **A1-tier controls (reported with the A1 classes).** Sr "repels" at the A1 tier; C2, C3 and C4 for
  d; no heterogeneity flag. An A1-tier class is never called validated.
- **Dopants without classes.** A dopant that failed gate N or G1, or that meets the
  dopant-specific failure rule of §12, receives no class at either tier; its values are reported.
- **Ranking (reported only).** Host-paired differences between dopants, D_h = Y_h,d − Y_h,d′ over
  the hosts valid for both, with t_{n′−1}(1 − 0.05/20) intervals (Bonferroni over the 10 pairs of the
  5 dopants), at the A1 tier; and, when both are calibrated, at the calibrated tier, adding
  δ̄_d − δ̄_d′ with variance s²_δ(1/m_d + 1/m_d′) and Welch–Satterthwaite degrees of freedom.
- **Output.** Unrounded values in `s2/s2_eval.json`, written by the S2 analysis script (§17).

## 15. Reported only (no decision rests on these)

- Per-site values e_h(j), per-site host means Ē_d(j), the Boltzmann shell value G_d, raw E_b and the
  far-site values.
- The sensitivity of every calibrated interval to the shared region terms: I_d recomputed with s²_δ
  unchanged and with df_δ in ν_d and in the a_far threshold replaced by the number of regions (B, A,
  X) with two valid pilot-host quartets (at most 3) [M]. Sr and Ca share host_R and V⁺_R relaxations
  in the B region, and Cs and GA in the A region, so their δ deviations are positively correlated
  (§18).
- Every invalid cell, tabulated by dopant, host, site and failed check (§§5, 11, 12).
- Every calibrated interval also with the δ values that use a plateau-accepted relaxation (§11)
  excluded; such δ values are flagged (`CURRENT_STATUS.md`: pools of different relaxation depth are
  never merged).
- Zero-shot MACE E_b of every cell, from the MACE energies of the A1 minima: the per-chemistry error
  ledger for a possible option B at S4a, labelled "zero-shot MACE, not re-admitted".
- DFT residual forces on the free atoms of every A1 cell (per-atom norms, RMS and max).
- Per A2 cell: the relaxation energy F(final) − F(0), the configuration count, the restarts, and the
  displacement and path-work attribution by shell (`scripts/38` style).
- The q = 0 link rows (§10), and the comparison with WP2c at Pb136 (Sr) and FA128 (GA) on m30 and
  at Pb124 (Sr) on m05, where the S2 A1 and A2 cells of the calibration quartets exist (different
  protocol: whole-cell geometry, q = 0, one far site), labelled. WP2c's Pb124 on m30, and its Pb136
  (Sr) and FA128 (GA) on m05, have no S2 cell.
- A fixed-geometry D3(BJ) correction to every E_b, computed on the laptop with the PBE D3(BJ)
  parameters of QE `dftd3_version = 4` as used by Objective 1 (`scripts/05`: `vdw_corr = 'dft-d3'`;
  s6 1.0, s8 0.7875, a1 0.4289, a2 4.4407 bohr [S]; checked against Grimme, Ehrlich & Goerigk 2011
  and the chosen implementation in Stage 0), two-body only. Unlike Objective 1, whose QE default
  `dftd3_threebody` is true [S], no three-body term is included, so these values are not that
  fingerprint and are never compared with it (standing rule 1). The implementation and its version
  are fixed in Stage 0 [M].
- Required hosts per dopant: the smallest n at which t_{n−1}(q*)·s_Y,d/√n would fall below k_BT
  and below k_BT/2, from the measured s_Y,d (the roadmap S3 deliverable; a planning estimate) [M].
- The pose-pilot spreads and the noise-pilot per-site values; the determinism check of §5; the
  throughput row of §16.

## 16. Stopping rules and budget

- **Gates.** K1 = G1 (§7); gate N (§8); the step-0 check, K2 and K3 (§11); the hard budget cap below.
  Each is evaluated by a committed script on the node or the laptop before the next stage starts.
- **Node-hours [M].** Node-hours are the wall time during which the S2 node is running (boot to stop),
  summed over campaigns from the campaign logs. Idle time and outages while the node runs count; time
  while it is stopped does not. No currency figure is used anywhere.
- **Unit costs.**
  - Single point: 6.74 min at 64 ranks (153 single points in 1031.5 min,
    `dopant_shell/wp3/run2/node_logs/step2.log`, 2026-10-29 02:50:44 → 20:02:15) [R].
  - DFT ionic configuration: 6.15 min at 48 ranks (WP2e: 283 SCF cycles in 29.0 h,
    `dopant_shell/wp2e/relax_m30_GA_img0.out.gz`) [R].
  - A2 relaxation: 64–140 BFGS steps, i.e. 65–141 configurations, 6.7–14.5 h, median 9.1 h; at the
    cap, 201 configurations and 20.6 h [I: the WP3b frozen/unconstrained FIRE step ratios
    0.228–0.496 (median 0.311; `WP3_RESULT.md` §5) applied to WP2e's 282 BFGS steps; no observed
    ratio reaches the cap of 200 steps].
  - Frozen-region MACE relaxation: about 2 min of node time (17–27 min at 6 threads with 10 concurrent,
    WP3b, fine-tuned model) [I].
  - Host relaxation: 2285–4928 FIRE steps and 1.6–3.3 h wall (m30 2436 steps, 1.7 h; m05 2285,
    1.6 h; m21 4928, 3.3 h; WP1 production references, `dopant_shell/wp1_production/shell_m*.json`,
    `E_host`) [R]. Every frozen cell of a host waits for its relaxed host, so this stage is on the
    critical path and costs its wall time in node time: about 1.7 h in C1 (two pilot hosts
    concurrently) and up to 3.3 h in C3 (the production hosts concurrently) [I].
- **Expected cost** [I, from the unit costs]:

  | campaign | content | node-h |
  |---|---|---|
  | C1 | pw.x smoke tests 1.0 (below); G1 (5 single points, 3 at 1.31× cost) 0.7; spin row 0.45; throughput row 1.5; step-0 check 0.2; noise pilot 106 single points 11.9; pose pilot ≤ 40 single points 4.5; q = 0 rows 1.1; MACE about 170 frozen relaxations 5.7 and 2 host relaxations 1.7 | ≈ 29 |
  | C2 | 10 A2 relaxations | 67–145, median 91 |
  | C3 | n = 8: 608 single points 68.3 + MACE 23.3 (600 frozen relaxations 20.0, host relaxations ≤ 3.3); n = 10: 85.4 + 28.3; multi-pose up to +11.2 single-point and +3.3 MACE node-h per host | ≈ 92 (n = 10: 114) |
  | C4 | 26 A2 relaxations | 173–376, median 237 |
  | total | n = 8, default poses | ≈ 449 (360–641); n = 10: 471 (382–663) |

  The upper ends of the full plan exceed the 520 node-h hard cap, so the cut order below applies.
  With only the 24 protected relaxations (below), n = 8: 280–467 h, below the hard cap even at the
  largest observed step ratio (615 h if all 24 reached the cap of 200 steps). No allowance for
  interruptions is included: a node loss during an A2 relaxation costs up to 20.6 h (rerun from
  k = 0, §13), and each spot reclaim needs a console restart (the WP3 run lost its node on 2026-10-30,
  `dopant_shell/wp3/run2/node_logs/restarts.txt`, and was reclaimed on 2026-11-03, `WP3_RESULT.md`
  §5) [R].
- **Keep-alive [M].** The node drivers keep the keep-alive file of `dopant_shell/WP3_RUNBOOK.md`
  (step 4) present for the whole of each campaign, so that the idle cron (which counts pw.x, a 1-min
  load above 1 or a login as busy, and stops the node after 60 idle minutes) cannot stop it during a
  gate evaluation or a pause between stages; they remove it when the campaign ends. Idle time with
  the file present counts as node time (above).
- **pw.x smoke tests (start of C1, before any S2 cell) [M].** On the reference vacancy cell, at the
  node's pw.x 7.5 and the A2 MPI layout: the `nstep` value that caps a relaxation at k = 200 and its
  value after a restart (§§11, 13); a stop by the exit file in `outdir`; and a restart with
  `disk_io = 'low'` and `restart_mode = 'restart'`. About 1 node-h [I], counted in H_spent; only
  configuration counts, files and wall times are read, and the energies are discarded unread. If a
  restart is not possible, every interruption of an A2 relaxation is handled by the rerun rule of
  §13.
- **Throughput row (C1; operational).** On the reference vacancy cell, at q = +1 with a frozen region
  built as for Pb136, five ionic configurations each at 48 ranks, at 64 ranks, and as two concurrent
  32-rank copies; only wall times are read, the energies are discarded unread. The layout with the
  highest configurations per node-hour is used for all A2 relaxations if it beats 48 ranks by at
  least 15%; otherwise 48 ranks [M]. If the two-copy layout is chosen, relaxations start in the
  fixed order of §11, two at a time. A gate evaluated on a finished relaxation (step-0 check, K2,
  projection, K3) applies at once, and a running partner it stops is killed and its output
  discarded unread [M].
- **Cost projection (after the first 4 A2 relaxations; repeated at the start of C3 and of C4) [M for
  the formula and the repeats].**

  P = H_spent + N_relax × c̄ × τ̄ + N_SP × τ_SP + H_MACE,

  where H_spent is the node-hours spent so far; N_relax the A2 relaxations still planned; c̄ and τ̄
  the mean configuration count and mean wall minutes per configuration of the A2 relaxations
  completed so far; N_SP the single points still planned (including multi-pose) and τ_SP their mean
  wall time in C1; and H_MACE the remaining MACE node time at the C1 mean per relaxation. Only step
  counts and timings enter P, never an energy.
- **Cut order** while P > 520 node-h, recomputing P after each cut; cuts are never undone:
  1. GA on m05 (2 relaxations);
  2. Cs and the A region on m05 (4);
  3. GA on m30 (2);
  4. Cs and the A region on m30 (4);
  5. [M] if n = 10: n becomes 8 (the last two hosts of the production list, m33 and m13 if every
     host is admissible, are dropped before any calculator runs on them);
  6. [M] Cs multi-pose production, if required: Cs runs at the default pose and is "pose-dependent;
     not classified";
  7. [M] Cl multi-pose production, if required: likewise;
  8. [M] C4 is not run. Cuts remove whole regions; once cuts 1–4 apply, C4 holds the m30 X, m05 B and
     m05 X regions, and removing any of them leaves df_δ ≤ 2 (2 without the m30 or the m05 X region,
     1 without the m05 B region), so C5 fails and no shorter C4 can give a validated class. If cut 8
     is reached, S2 reports the A1 tier, with the C2 δ reported only.

  Sr, Ca and Cl on both pilot hosts (24 relaxations, including the Sr far quartet) are protected by
  cuts 1–4. With cuts 1–4 applied, df_δ = 3 exactly: one invalid Sr, Ca or Cl quartet ends the
  validated tier; at df_δ = 3 the class threshold is 56.1 / 94.0 meV (s_Y 13, s_δ 10 / 20 meV,
  n = 8) and Sr is classified "repels" with probability 0.82 at s_δ = 20 meV (0.97 at df_δ = 5)
  [MC, review of 2026-11-03]. Cuts 5–7 are available at the projection after the first 4 A2
  relaxations and at the projection at the start of C3, made before any C3 job starts; no
  production host or pose is removed once a production value exists. A dopant that loses one
  calibration host is calibrated with m_d = 1; one that loses both stays at the A1 tier.
- **Hard cap.** 520 node-h. No job starts if H_spent plus the job's expected duration (measured mean)
  would exceed 520 h; jobs already running finish [M]. Whatever is then incomplete is missing.
- **Other stops.**
  - If df_δ < 3 at the end, no validated class is awarded; the A1 tier is reported.
  - No host, site, dopant or pose is added after any S2 value exists; no cell is rerun with other
    settings; every deviation is written as a dated amendment before the affected values are read.

## 17. Order of work and blinding

1. **Commit** this file, PLAN amendment n, the roadmap update 2026-11-03 (d), `S2_DECISION.md`,
   `PSEUDOPOTENTIALS_S2.md`, `S2_BUILDERS_DESIGN.md` §16 with the 2026-11-03 corrections of its §11,
   and the dated note in `CURRENT_STATUS.md`, before any S2 calculation.
2. **Stage 0 code**, committed with self-tests that use synthetic cells or the reference cell only:
   - the region builder, the cell construction and the validity checks of §5, including the partner
     check and the graph topology check;
   - the S2 QE writer (§6) with the X-unit vacancy detection, the `_q0` exception, the
     electron-count assertion and the spin seed of §7;
   - the node drivers: resumable, under `flock`, with the spot-notice soft exit and the k = 200 stop
     of §13, the keep-alive rule of §16, the completeness rules of §12 and the gates of §§7–11 and
     §16 scripted on the node;
   - the S2 analysis script (§14). Its self-test recomputes every statistic of §14 on a fixed
     synthetic data set with an independent implementation (agreement to 10⁻⁶ meV; total energies of
     about −8 × 10⁴ eV carry a rounding unit of 1.5 × 10⁻⁸ meV), and recovers planted classes on
     synthetic data with known effects: a repelling control, a binder, a null dopant at low noise
     ("no interaction"), a heterogeneous shell (one X site at −100 meV, the others at 0), which must
     be flagged, and one X site at −80 meV with the others at 0, which is not flagged and must not
     receive "no first-shell interaction beyond k_BT". It must also refuse a validated class when
     the control does not repel, when df_δ < 3, when |δ̄_d| > 50 meV and when the dopant-specific
     failure rule of §12 applies.
3. **Laptop checks.** Regenerate and archive the `s2b-2` T4 admissibility report, then freeze
   `s2b-2` (answer 3); record the host draw (§3, done), the m05 calibration-site draw (§11, done),
   and the Stage-0 admissibility check of ranks 1–12 and of the m05 calibration cells (§11); verify
   Pb–Cl 2.837 Å, use the source value, or label the shifted Cl starts [M] (§2;
   answer 4); check that the node's MACE file has the sha256 of §5 (coverage of Z = 16, 17, 20, 37
   was read on the laptop, §0).
4. **Pre-flight.** Before the node is booted: the throughput-row and smoke-test inputs (reference
   cell) are built and checked. Every C1 cell (all sites and poses of §§7–10 and the C1 start set of
   §11, both legs) is built as a dry run with `partners="unrelaxed"` on the unrelaxed m30 and m05
   members and checked (builder, labels, region ids, electron count, writer output); the dry-run
   outputs are not used. The G1 cells and every C1 cell that is calculated are built on the node
   from the S2-relaxed host and V⁺_R (§§5, 7).
5. **Campaigns.** C1 → G1, gate N, n, pose rule → C2 → step-0 check, K2, projection, K3 → C3 → C4 →
   one evaluation by the analysis script → adversarial check → S2 result note → roadmap update. The
   node is stopped after each campaign.
6. **One evaluation.** The analysis script is committed before C3 and run once after C4 at a
   recorded commit. A rerun after a code error that changes no rule is not a second evaluation; its
   cause and diff are listed in the result note. The error must be shown by a self-test case,
   committed before the rerun, that fails on the first code and passes on the fixed code; both
   outputs are archived and reported.
- **Blinding (operational).** Until C4 ends, production and A2-II outputs are read only for
  completeness, validity and the end rule; no E_b (DFT or zero-shot MACE), Y_h or δ of a production
  host or of an A2-II cell is computed, and the MACE ledger of §15 is computed only in the one
  evaluation. Pilot values are read as
  the gates of §§7–11 require: the C1 pilots, the step-0 check, K2 and K3 (which reads the m30 Sr
  hinge and Pb76 A2 quartets). The raw energies remain visible in the output files; the blinding
  rests on not combining them, and the result note states this.

## 18. Power statement [MC]

- **Model.** Host values Y_h ~ N(θ − μ_δ, s_Y), independent, n = 8; δ_{d,p} ~ N(μ_δ, s_δ) for 5
  dopants × 2 pilot hosts, independent; δ_far ~ N(0, s_δ); rule V of §14 with C5 (|δ̄_d| ≤ 50 meV
  only; df_δ = 5 throughout) and a_far, without C1, C2–C4, the heterogeneity flag, the G_d condition
  or a pose allowance. 6000 draws per case from one generator seeded 20261103 (panel synthesis
  check). The thresholds below are analytic: 25.7 meV + t*·SE at the true s_Y and s_δ, i.e. the
  true |θ| at which a class is reached with about 50% probability (0.48–0.52 by MC, review of
  2026-11-03), recomputed for this plan.
- **Class thresholds (meV), n = 8, m_d = 2, df_δ = 5:**

  | s_Y \ s_δ | 5 | 10 | 15 | 20 |
  |---|---|---|---|---|
  | 13 | 42.7 | 52.0 | 64.5 | 77.8 |
  | 20 | 49.7 | 55.2 | 65.2 | 77.4 |
  | 30 | 61.0 | 63.4 | 69.9 | 79.5 |

  - n = 10 changes these by −5.2 to +0.2 meV (largest gain at s_Y 30, s_δ 5; at s_δ = 20 meV less
    than 1.4 meV). The synthesis draft's "≤ 4 meV" is corrected here.
  - A1 tier (no calibration), n = 8: 41.0 / 49.3 / 61.1 meV at s_Y = 13 / 20 / 30 meV.
- **Probabilities.**
  - Sr control (θ = +119 meV): "repels" with probability ≥ 0.957 for s_δ ≤ 20 meV (s_Y 13 or 20).
  - A −75 meV binder (s_Y 20): "binds" with probability 0.99 / 0.92 / 0.71 / 0.46 at s_δ = 5 / 10 /
    15 / 20 meV; a −50 meV binder 0.52 / 0.30 / 0.16 / 0.10; a +60 meV repeller "repels" 0.84 /
    0.62 / 0.36 / 0.21.
  - θ = 0: no false "repels" or "binds" in any case. "No interaction beyond k_BT" is reached with
    probability 0.95 / 0.27 at s_Y = 8 meV and s_δ = 5 / 10 meV, and 0.28 / 0.06 at s_Y = 20 meV.
  - A dopant-specific bias μ_δ = +20 meV is removed by the calibration (binder −75 meV: 0.935 at
    s_δ = 10 meV, against 0.924 without the bias).
  - The far allowance is added in 4.5–5.5% of draws.
  - These are probabilities of rule V alone. A validated class also needs gate N and C2 for the
    dopant and for Sr (C1): at a per-site far noise σ_far of 11 / 15 / 20 / 25 meV they pass jointly
    with probability 0.99 / 0.94 / 0.63 / 0.25 (n = 8, f₁ and f₂ equivalent), and 0.82 / 0.74 /
    0.50 / 0.21 if E_b(f₁) − E_b(f₂) has mean 10 meV [MC, review of 2026-11-03]; Sr "repels" with
    gate N and C2 jointly has probability 0.90–0.94 at σ_far = 15 meV and 0.60–0.64 at 20 meV. C4,
    the heterogeneity flag and the dopant-specific failure rule lower them further.
- **Beyond the planning range.** At s_δ = 25 / 30 meV (s_Y 13, n = 8) the class threshold is
  91.4 / 105.1 meV, Sr is classified "repels" with probability 0.86 / 0.68, and a −75 meV binder
  (s_Y 20) "binds" with probability 0.30 / 0.19 [MC, review of 2026-11-03]. s_δ ≈ 21 meV is as
  consistent with the WP3b data as the planning range (§0, choice 6).
- **Shared region terms.** In the design, Sr and Ca (and Cs and GA) share the host_R and V⁺_R
  relaxations of their calibration region, which the model above ignores. With a common region term
  carrying 0, ½ or all of the δ variance (s_Y 20, n = 8), the coverage for Ca (which shares the B
  region with Sr) of the nominal 98.75% interval is 0.991 / 0.988 / 0.985 at s_δ = 10 meV and
  0.985 / 0.984 / 0.973 at s_δ = 20 meV [MC, 40 000 draws, seed 20261103, computed for this plan].
  The reported-only sensitivity of §15 shows the effect on the actual intervals.
- **Assumptions.** Independent normal errors; equal δ noise across chemistries; zero-mean δ_far
  (tested only for Sr at Pb76 on m30, §11). The single-site noise of the calibration site bounds the
  random part of the shell-level δ conservatively. Two assumptions are not tested and do not enter
  s_δ in full:
  - (i) the expected δ of the calibration sites equals the shell-mean δ of their sublattice. For B
    both first-shell Pb are calibrated, Pb136 on m30 and Pb124 on m05, so δ̄ averages the B shell,
    with site confounded with host. For A and X the m30 site is of one type (FA128, the nearest FA on
    both pilot hosts; I138, the migrating iodide) and the m05 site was drawn from the other
    first-shell sites (FA28, I49; §11), so a site-type effect enters s_δ, confounded with host. An
    offset s* of the m30-type site biases δ̄ by s*/2 if the drawn m05 site carries the shell-mean δ,
    by s*/4 (A) or 3s*/7 (X) if the compensating offset is shared equally by the other first-shell
    sites, and by s* (not reduced) if the drawn site carries the same offset as the m30 site; it is
    not removed [R, census of 2026-11-03; I];
  - (ii) the pilot hosts, chosen and not drawn (§0, choice 1), have the expected δ of the
    production hosts.

  A systematic offset s* between the expected δ of the m30-type site and the shell-mean δ, carried
  by the m30 δ of Cs, GA and Cl and by neither B dopant (no hinge–flank difference is modelled; one
  would inflate s_δ and raise the coverage), gives, if the drawn m05 site carries the shell-mean δ,
  a coverage of the nominal 98.75% interval of 0.98–0.99 for Cl and for Cs at s* = 10 meV and at
  s* = 20 meV (s_Y 13–20, s_δ 10–20 meV, n = 8, df_δ = 5). With the offset on the tested dopant's
  sublattice only, or on the tested dopant only (the least inflation of s_δ), it is 0.98 at 10 meV
  and 0.96–0.98 at 20 meV; if the compensating offset is shared equally, so that the drawn m05 site
  carries −s*/2 (A) or −s*/7 (X), it is 0.99–1.00 [MC, 40 000 draws per case, seed 20261103, common
  random numbers across designs; interval θ̂_d ± t*_d·SE_d without a_far, as in the review of
  2026-11-03; with a_far each figure rises by at most 0.005 (0.025 for the design before D1);
  computed for the analyst's decision D1 and checked by the review of D1, §20]. If the drawn m05
  site carried the same offset as the m30 site, the coverage would be that of the design before
  D1, with the same kind of site on both pilot hosts: 0.93–0.97 at s* = 10 meV and 0.70–0.92 at
  s* = 20 meV [MC, review of 2026-11-03; reproduced in the same run].

  The offset raises the expected s²_δ by 0.3·s*² for every dopant and shifts δ̄ of Cs, GA and Cl by
  s*/2, so it costs mainly power; coverage falls below the nominal level only in the least
  favourable reading above. At s* = 0 / 10 / 20 meV, with the drawn m05 site at the shell-mean δ:
  - Sr (θ = +119 meV, s_Y 13 or 20, s_δ = 20 meV) is classified "repels" with probability 0.96 /
    0.95 / 0.92 (1.00 at s_δ = 10 meV);
  - a −75 meV Cl binder (s_Y 20, s_δ 10 meV) "binds" with probability 0.93 / 0.82 / 0.51 when the
    shift of δ̄ points towards zero, and 0.93 / 0.95 / 0.93 when it points away;
  - the separability allowance fires in 5.0 / 3.1 / 0.8% of draws at zero far bias (s_δ = 10 meV),
    because the offset inflates the estimated s_δ

  [MC, 40 000 draws per case, seed 20261103, rule V with C5, a_far and the sign rule; review of D1,
  §20; reproduced within MC error by an independent run]. The class thresholds and probabilities
  given above in this section are for s* = 0. A validated class is conditional on (i) and (ii).
- **Wording.** A pass is "consistent with" the class at the stated level. A fail is reported as a
  fail, with the sample size beside it; it is never a reason to add hosts, rerun, or change a
  threshold. Under the worst shared-region case tested (no site-type offset) the per-dopant coverage
  is 0.973, so the familywise error over the four decisive dopants is bounded by about 11%, not 5%.

## 19. Rules added or made precise relative to the panel outline

Each is marked [M] where it appears above. Items 13, 15 and 17 state the rule as corrected by the
reviews of 2026-11-03; every rule added or changed by those reviews is listed in §20. Items 11, 27
and 28 state the analyst's decisions on the reviews' open issues, also recorded in §20.

1. Tag legend: [R] for measured values (the drafts' [M]); [M] for modelling choices.
2. k_BT = 25.7 meV exactly, in every formula and Boltzmann sum (§0 symbols).
3. Admissibility for the host lists is decided on the unrelaxed pool members of ranks 1–12 in
   Stage 0; the production list is the first n admissible hosts; later build failures make cells
   missing (§3).
4. No range cut on sites; ranking by distance rounded to 10⁻⁶ Å with ties to the lower index; X far
   bound 9.0 Å; the executed site lists are asserted (§4).
5. Region centres, index transfer and region id (§4).
6. The host relaxation is the `scripts/29` staged reference protocol; the m30/m05 determinism check
   is reported only (§5).
7. Thread counts, model hash and versions recorded (§5).
8. The partner check covers inorganic atoms as well as FA, measures FA rotation as the Kabsch
   rotation of C–N–N, and measures distances from the relaxed-host centre of the defect added in the
   step (§5).
9. The graph topology check, with the 0.65 Å floor and the composition test (§5).
10. Labels and output location (§5).
11. etot_conv_thr 10⁻⁵ Ry (the outline said 10⁻⁴ Ry; the `scripts/30` relax branch and the WP2e
    input use 10⁻⁵); `disk_io = 'low'` for A2; the 201-configuration cap with the plateau window
    F(200) − F(180) (analyst decision D2, §20); MPI layouts (§§6, 11).
12. The electron-count assertion and the UPF sha256 check per campaign (§6).
13. G1 cells: the host 50/400 single point is shared with the noise pilot; the spin row uses the
    farthest-site noise-pilot D+V⁺ cells and a seed of about 1 μB on the dopant
    (`starting_magnetization` = 1/z_valence); a failing element's production and A2 cells are not
    run (§7).
14. Gate N with df < 3 is a fail; the n rule counts only decisive dopants that pass gate N and G1
    (§8).
15. Pose pilot: reuse of the default cells, greedy distinct-minimum rule, a_pose = the largest of
    the two site residuals and their difference, and a fail-closed rule for invalid default minima
    (§9).
16. The Sr far quartet at Pb76; the internal order of every region (host_R, V⁺_R, then dopants)
    (§11).
17. K3 fails closed if either quartet is invalid by validity checks 2–5; if a quartet is invalid
    only by the end rule, A2 stops and the A1 tier is delivered, as under K2; a missing δ_far fails
    C5 (§11, §14).
18. Step-0 check tolerance and failure handling (§11).
19. The pose allowance is carried at the A1 tier too; n_d replaces n in the sign rule and the t
    quantiles; the heterogeneity flag at both tiers with k = sites with a valid host (§14).
20. C1 requires C2, C4 and C5 for Sr; A1-tier controls; pose-dependent dopants receive no class
    (§14).
21. Reported-only sensitivity to shared region terms (§15).
22. D3(BJ) parameters; the required-hosts estimate (§15).
23. Node-hour accounting; projection formula and its repeats at C3 and C4; cuts 5–8; the hard-cap
    job-start rule; the throughput-row protocol (§16).
24. Specification of the analysis self-test (§17).
25. Smoke tests may also use the 232-atom reference vacancy cell, whose energies are likewise
    discarded unread (header; the throughput row of §16 needs a q = +1 vacancy cell).
26. v is taken in the unrelaxed member for site distances and in the S2-relaxed host for regions and
    the refill check (symbols).
27. The m05 calibration sites Pb124, FA28 and I49, the seeded m05 draw and its admissibility fallback
    (§11); the pre-flight dry run includes the C1 start set of §11 (§17) (analyst decision D1, §20).
28. A JOB DONE single point whose SCF did not converge is missing, not rerun (§§12, 13; analyst
    decision D3, §20).

## 20. Review record (2026-11-03, before commit)

**Reviews.** Three reviews of the uncommitted pre-registration (this file, `S2_DECISION.md`, PLAN
amendment n, roadmap update 2026-11-03 (d), `S2_BUILDERS_DESIGN.md` §16 and
`PSEUDOPOTENTIALS_S2.md`). Each re-derived its checks from the repository with geometry only (ase
and numpy, `"mace" not in sys.modules`), the Python standard library and Monte Carlo; none evaluated
an S2 cell, and no S2 value existed. Their scripts and outputs, and the recomputed node-hour table of
§16, are kept off-repository in the private record folder.

| review | findings | applied |
|---|---|---|
| facts (figures, sources, information state) | 22: 1 error, 10 minor, 11 suggestions | all; F19 with the recorded wall times of feasibility F12 |
| rules and statistics | 21: 4 errors, 10 minor, 7 suggestions | all; F1 first as an assumption disclosure, then adopted by the analyst (D1, below) |
| feasibility and conformance | 25: 6 errors, 11 minor, 8 suggestions | all; F2 first for K3 only, then adopted with a larger cap by the analyst (D2, below); F13 with a corrected premise; F25 as a note only |

**Merged findings.** Facts F1 and rules F5 (m15); facts F2 and rules F5 (Pb124); facts F3 and
feasibility F16 (5.13 Å); facts F6 and feasibility F9 (lattice); facts F7 and feasibility F10
(region sizes); facts F9 and rules F21 (power model); facts F19 and feasibility F12 (host
relaxation); rules F12 and feasibility F19 (default-pose calibration).

**Corrections to findings.**
- Facts F19 estimated the host relaxation at 20–50 min wall from the per-call MACE time; the WP1
  records give 1.6–3.3 h (`E_host.wall_s`), which §16 uses.
- Feasibility F13 assumed that the idle cron stops the node whenever no QE process runs. It also
  counts a 1-min load above 1 or a login as busy (`dopant_shell/WP3_RUNBOOK.md` step 4); the
  keep-alive rule is kept for gate evaluations and pauses between stages.
- The feasibility census reported an exact tie between the two farthest A sites of m00; at full
  precision they differ by 8 × 10⁻⁶ Å (§4).
- Facts F8's replacement said that the C1 first-shell pilot cells enter no decisive statistic; the
  pose pilot enters through a_pose (feasibility F1), and `S2_DECISION.md` §4 row 2 says so.

**Rules added or changed by the reviews** (each marked [M] or tagged where it appears):
1. §0: the m15 v1 map, Pb124, the WP2d charge, the half-δ basis of s_δ and the n-rule threshold
   disclosed; the pilot-host quantities that enter the decisive rules named (§§3, 8).
2. §5: explicit organic–inorganic cut-offs; strict partner bounds (< 0.25 Å, < 20°).
3. §6: the `_q0` charge and electron-count exception; per-configuration parsing of relaxations.
4. §7: spin seed `starting_magnetization` = 1/z_valence on the dopant.
5. §9: a_pose = max(|Δ_pose(near)|, |Δ_pose(far)|, |Δ_pose(near) − Δ_pose(far)|); the
   minimum-count term reported.
6. §11: early non-converged ends are unconverged; default-pose calibration label; the step-0 check
   repeated once; K3 delivers the A1 tier when a quartet fails only the end rule; the separability
   evidence restricted to what the geometry supports.
7. §12: the dopant-specific failure rule.
8. §13: MACE relaxations and single points under separate rules; restarts with a reduced `nstep`
   and a driver stop at the cap (k = 200 after D2, below).
9. §14: "no first-shell interaction beyond k_BT" also requires G_d > −k_BT; the host set of the
   heterogeneity flag.
10. §15: the shared-region sensitivity specified; the invalid-cell table; intervals without
    plateau-accepted δ; the D3(BJ) row separated from the Objective-1 fingerprint.
11. §16: host relaxations on the critical path; pw.x smoke tests in C1 (about 1 node-h); no
    interruption allowance stated; the keep-alive rule; the two-copy layout; cut 8 means C4 is not
    run; cuts 5–7 only before any C3 job. Totals, as revised by D2 (below): ≈ 449 (360–641) node-h,
    n = 10: 471 (382–663).
12. §17: the joint-commit list; pre-flight as dry-run builds; self-test tolerance 10⁻⁶ meV and the
    planted −80 meV single-site trap; the rerun guard; blinding of the MACE ledger.
13. §18: the model as simulated; 77.8 meV; the joint pass probability of gate N and C2; the range
    beyond s_δ = 20 meV; the coverage for Ca; assumptions (i) and (ii); the familywise bound of
    about 11% under shared region terms.

**Raised and not adopted in this revision.**
- **Pre-existing text (feasibility F25).** The currency figure in the roadmap stage table and the
  node paths in PLAN amendments j and m are committed text in append-only files and are not edited;
  roadmap update (d) states that costs are given in node-hours only. It stays a note (D4, below).

Rules F1 (calibration sites on m05) and feasibility F2 (the A2 end rule), which the reviewed
revision listed here as not adopted, were adopted by the analyst before the commit (D1 and D2,
below).

**Analyst decisions on the open issues (2026-11-03, before commit).** Made by the analyst (an AI
assistant, to whom the PI delegated the S2 research direction; `S2_DECISION.md`, "Who decided")
after the three reviews, before the commit and before any S2 energy value existed. The checks
behind them used geometry only (ase, numpy and `scripts/42`; `"mace" not in sys.modules`
asserted), the Python standard library and Monte Carlo. Their scripts and outputs, and the review
reports, are kept off-repository in the private record folder.

- **D1. Calibration sites on m05 (rules F1, adopted).**
  - Decision: on m30 the calibration sites stay Pb136 (B), FA128 (A) and I138 (X, the migrating
    iodide); K3, the Sr far quartet at Pb76, the step-0 check, the pose pilot and the q = 0 link
    rows are unchanged. On m05 they become Pb124 (B), FA28 (A) and I49 (X) (§11).
  - Reasons: the two first-shell Pb are both B shell sites, so the two pilot hosts together
    calibrate the whole B shell; for A and X the m05 site is drawn from the first-shell sites of
    another type than the m30 site, so a site-type effect enters s_δ (confounded with host) and is
    halved in δ̄ if the drawn site carries the shell-mean δ (§18). Assumption (i) of §18 is
    weakened, not removed [I]. The 36 relaxations and the §16 cost estimate, which does not depend
    on region size, are unchanged; the m05 regions hold 70 (Pb124), 58 (FA28; 50 on the WP1-relaxed
    host) and 59 (I49) host atoms, against 62 (Pb136), 57 (FA128) and 60 (I53) for the sites they
    replace [R, geometry census].
  - The m05 draw (§11) was executed once, by the analyst, with one seed string (the first and only
    string tried), before any S2 value existed [R]. WP2c measured Sr at Pb124 on m05 (q = 0; §0,
    choice 2); δ uses none of these values.
  - Checks [R, geometry only]: on the unrelaxed m05 member Pb124, FA28 and I49 are first-shell
    sites (3.27, 5.03 and 4.63 Å from v), I49 is not the migrating iodide (I53), and FA128 is the
    nearest FA on both pilot hosts; every required cell (Sr, Ca at Pb124; Cs, GA at FA28; Cl at
    I49; both legs, default poses, `partners="unrelaxed"`) is admissible; the three regions hold 70,
    58 and 59 host atoms (70, 50 and 59 on the WP1-relaxed m05 host), within the 48–71 of the
    first-shell regions (`S2_DECISION.md` §11).
  - Coverage under a systematic site-type offset, if the drawn site carries the shell-mean δ:
    0.98–0.99 for Cl and Cs at s* = 10 and 20 meV, against 0.93–0.97 and 0.70–0.92 with the same
    kind of site on both hosts; the offset costs mainly power instead (at s* = 20 meV, Sr "repels"
    with probability 0.92 instead of 0.96 at s_δ = 20 meV; §18) [MC].
  - Consequences elsewhere: the C1 start set and the C4 order (§11), the WP2c comparison (§15), the
    Stage-0 checks of §17 item 3, and the pre-flight of §17 item 4, which now names the C1 start set
    of §11 so that the m05 calibration cells are dry-run built (that start set was not covered by
    §§7–10 before D1 either).
- **D2. A2 end rule (feasibility F2, adopted with a larger cap).**
  - Decision: the cap rises from k = 120 to k = 200, i.e. at most 201 ionic configurations (the
    start k = 0 and 200 further); at the cap a relaxation is accepted if |F(200) − F(180)| ≤ 3 meV
    (the same 20-configuration window and 3 meV). The rest of the end rule, K2 and K3 (an end-rule
    failure alone at K3 delivers the A1 tier) are unchanged (§§6, 11, 13, 16).
  - Reasons [I]: a lognormal fit to the six WP3b frozen/unconstrained FIRE step ratios (mean of
    ln −1.169, SD 0.272, ddof = 1; `WP3_RESULT.md` §5), applied to WP2e's 282 BFGS steps, gives
    P(more than 120 steps) ≈ 0.12 per relaxation, so all eight K3 relaxations would be accepted
    without the plateau with probability ≈ 0.35; P(more than 200 steps) ≈ 0.0012, ≈ 0.99 for eight,
    at the fitted parameters. With the step count scaled by the free-atom ratio of the largest region
    (m30 Pb76, 100–107 free atoms against 81–83 in WP3b) it is still at most about 0.02 per
    relaxation; four of the eight K3 relaxations (the Sr far quartet) lie in that region, so with
    each region scaled by its ratio (Pb76 100/83 to 107/81, Pb136 70/81) all eight are accepted
    without the plateau with probability ≈ 0.91–0.96. With the
    uncertainty of the six-point fit included (posterior predictive, the eight sharing the unknown
    parameters), P(more than 200 steps) ≈ 0.019 per relaxation and all eight ≈ 0.89 (0.79–0.85
    scaled); at the former cap ≈ 0.35 (0.11–0.21 scaled). These are planning estimates resting on
    the unverified transfer of FIRE step ratios to BFGS.
  - Cost [I]: 6.7–14.5 h per relaxation at the observed ratios (median 9.1 h), at most 20.6 h at
    the cap; totals ≈ 449 (360–641) node-h, n = 10: 471 (382–663) (§16). The upper ends exceed the
    520 node-h hard cap, so the cut order of §16 applies; the 24 protected relaxations stay below it
    at the largest observed ratio (n = 8: 280–467 node-h). A node loss during an A2 relaxation now
    costs up to 20.6 h.
- **D3. Completeness of single points (§12).** A JOB DONE single point whose SCF did not converge
  is missing and is not rerun, in conformance with amendment m item 1d ("A frame whose SCF does not
  converge is dropped"). The one resubmission of a job without JOB DONE stays (§§12, 13).
- **D4. Pre-existing committed text (feasibility F25, open issue 3).** Left as it is. Committed text
  in append-only files is not edited and no history is rewritten; new text states costs in
  node-hours only (roadmap update (d), item 4).
- **D5. Rules adopted on the reviewers' wording, confirmed by the analyst.** The dopant-specific
  failure rule of §12; the G_d > −k_BT condition of §14; cut 8 meaning "C4 is not run" (§16); the
  keep-alive rule (§16); the 1 node-h pw.x smoke tests [I] (§16).
- **Review of D1–D5 (2026-11-03, before commit).** A consistency review and a numbers-and-statistics
  review, without any calculator: 21 findings (11 minor, 10 suggestions, no error); 21 applied, 0
  rejected; none changes D1–D5.
