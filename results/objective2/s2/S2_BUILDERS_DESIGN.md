# S2 dopant builders: design of `scripts/42_s2_builders.py`

Status: design (2026-10-29), revised after the critic review (section 13), implemented as `s2b-1` (section 14) and revised to `s2b-2` after the code and chemistry review of 2026-10-30 (section 15). The open questions of section 12 are answered in section 16 (2026-11-03), and the pseudopotential bullet of section 11 was corrected on that date; neither changes `s2b-2`. Where `s2b-2` changed a rule, the text below gives the `s2b-2` rule and marks it (s2b-2); section 15 lists every change. Roadmap stage S2 (`results/objective2/SCREENING_ROADMAP.md`). Numbers marked [R] were measured with ase/numpy only (no calculator) on `results/fa_host/pool_v3_harmonised` m00–m35. S1 files and `results/objective2/dopant_shell/` are not touched.

Evidence tags: **[V]** checked against a primary source or deposited coordinates; **[S]** secondary source only, so recheck before production; **[U]** unverified provisional value; **[M]** modelling choice; **[R]** measured on repository structures.

## 1. Purpose and contract

`42` is a geometry-only library, CLI and `--self-test`. It builds **unrelaxed** isovalent substitutions in the 233-atom FA19Cs1Pb20I60 host and its 232-atom V_I partner. It loads `22_paired_pilot.py` as `pp` and `29_dopant_shell_scan.py` as `s29` via importlib, as 29:66-70 does; importing 29 evaluates no model. The contract generalises `ga_at_carbon` (29:115-138):

```python
BUILDER_VERSION = "s2b-2"; DOPANT_TAG = 77            # [M] any tag other than 0 and pp.MIG_TAG (99)
@dataclass(frozen=True)
class Built:
    atoms: Atoms        # calc None; no constraints; no masses/initial_magmoms/charges arrays
    token: str          # registry key (section 2)
    site: int           # input index of the replaced site atom: FA carbon / Pb / I
    centre: int         # dopant-centre index in atoms (1.0 A displacement test 29:406-411; free-region anchor)
    members: tuple      # every dopant atom in atoms (whole-molecule grouping, never pp.fa_molecule)
    deleted: tuple      # sorted input indices removed
    added: tuple        # range(len(input) - len(deleted), len(atoms)), in the template's atom order
    modified: tuple     # retained input indices whose symbol or position changed (Sr, Ca, Cl)
    old_to_new: dict    # every surviving input index -> new index (for checks.check_index_map)
    delta: dict         # exact element-count change (for checks.check_composition)
    pose: dict          # resolved orientation/anchor record (section 5), JSON-serialisable
    report: dict        # validity checks V1-V10 (section 8)

build_a_molecular(at, c, token, pose="inherit", *, anchor=None)  # GA, DMA, AA; None = fa_centroid; GA refuses an anchor
build_a_atomic(at, c, token, pose="inherit", *, anchor=None)     # Cs, Rb; None = pb8_centroid
build_b(at, pb, token)                                           # Sr, Ca
build_x_atomic(at, i, token, pose="inherit", *, vpos, mig="forbid")   # Cl; vpos required (s2b-2)
build_x_molecular(at, i, token, pose, *, vpos, mig="forbid")          # SCN; vpos required (s2b-2)
build(at, token, site, pose="inherit", **kw)            # dispatch through REGISTRY
resolve_poses(host, token, site, *, label, n_random=0)  # the "sampled" set; label = seed key f"{member}_{token}{site}"
build_paired(host, vac, vi, token, site, pose, **kw)    # -> (Built D_j, Built D_j+V)
list_sites(host, token, *, vi, vpos)                    # [(index, true-MIC distance to vpos)]
validate(base, built, *, vpos=None)                     # V1-V10
```

CLI:
- `--self-test`;
- `sites --host F --dopant T`;
- `build --host F --dopant T --site J --pose inherit|sampled|<class> --label L --out DIR [--member M] [--n-random N] [--allow-provisional]`. This writes the two unrelaxed legs (extxyz) and a JSON manifest with the index maps, pose, `BUILDER_VERSION` and `GEOM_SHA`, using relative paths only. Outputs go outside `results/objective2/dopant_shell/` (s2b-2: checked on the resolved path, so case variants and symlinks are refused too). `--label` names files only; the random-pose seed is `{member}_{TOKEN}{site}`, with the member defaulting to the host file stem (s2b-2). An `--out` that already holds files of the label is refused, and so is an option that does not apply to the token (`--anchor` for GA or a non-A token, `--n-random` for a token without random poses, `--mig` for a non-X token) (s2b-2).

Rules:
- **Atom order.** Retained atoms keep their order, numbers, positions and tags bit for bit, except `modified` atoms and the tags of `members`. New atoms are appended. Thus `keep = sorted(old_to_new)` gives the `basin_dev` correspondence (29:172-197) unchanged.
- **Wrapping.** Appended atoms that fall outside [0,1) are folded back by `pos - floor(s) @ cell`; a folded coordinate that rounds to 1.0 (s = −ε) is set to 0.0. Retained atoms are never wrapped. The hosts are not strictly wrapped: up to 18 atoms per member (m12) lie outside the cell, by at most 0.044 in fractional coordinates (m16) [R].
- **Distances.** Every distance, ranking and frame uses `ase.geometry.find_mic`. Never use `pp.mic` (22:39-43) or the mic of 16 and 18, which overestimate far distances on this cell by up to 11.2 Å (vacancy-to-atom distances over the pool; worst m30 pair 20.69 Å against a true 9.48 Å) [R]. Rounding MIC is exact below half the smallest perpendicular height (7.28 Å), so the nearest-atom searches inside `pp.build_pair` (< 1 Å and about 4.3 Å) are safe; `build_paired` still asserts their result (section 7).
- **Rejection.** An inadmissible pose raises `Inadmissible(report)`. It is never shifted or re-oriented silently.

## 2. Registry

| token | site | replaced → added (append order) | Δ composition | atoms host / V | Δ valence e⁻ | centre atom |
|---|---|---|---|---|---|---|
| GA | A | FA C–H hydrogen → N, H, H (S1 recipe) | N+1 H+1 | 235 / 234 | +6 | retained FA C |
| DMA | A | FA (8) → N, C, C, H(N)×2, H(C)×3, H(C′)×3 | C+1 N−1 H+3 | 236 / 235 | +2 | N |
| AA | A | FA (8) → C1, Na, Nb, C2, H(Na)×2, H(Nb)×2, H(C2)×3 | C+1 H+2 | 236 / 235 | +6 | C1 (amidinium) |
| Cs | A | FA (8) → Cs | C−1 N−2 H−5 Cs+1 | 226 / 225 | −10 | Cs |
| Rb | A | FA (8) → Rb | C−1 N−2 H−5 Rb+1 | 226 / 225 | −10 | Rb |
| Sr | B | Pb → Sr (symbol swap) | Pb−1 Sr+1 | 233 / 232 | −4 | site |
| Ca | B | Pb → Ca (symbol swap) | Pb−1 Ca+1 | 233 / 232 | −4 | site |
| Cl | X | I → Cl (symbol swap) | I−1 Cl+1 | 233 / 232 | 0 | site |
| SCN | X | I → S, C, N | I−1 S+1 C+1 N+1 | 235 / 234 | +8 | C |

- **Valences.** Pb 14, I 7, C 4, N 5, H 1, Cs 9 and Sr 10 are confirmed by archived S1 inputs. Cl 7, S 6, Ca 10 and Rb 9 are expected values; verify them against each UPF `z_valence`.
- **Parity.** The host has 1070 electrons (even) and the V cell 1063 (odd). Every Δ is even, so parity is preserved and the nspin 1 argument (30:16-18) still applies formally. Its physical premise (a delocalised vacancy electron with no competing magnetic solution) was established for undoped cells only, so one nspin 2 sensitivity row per new species is needed before it is assumed for doped V cells.
- **Charge.** The formal charge of the removed unit equals that of the added unit: +1 on A, +2 on B, −1 on X. No cell charge is set.
- **Tokens.** They are alphabetic and distinct from host/vac/undoped/pristine (label grammar of 33:87-89, 32:78, 39:216/510). "Cs" means a Cs⁺ dopant on an FA site; the native Cs belongs to the host.

## 3. Sites, anchors and local frames

- **A site: the host FA carbon index.**
  - Only carbons of intact FA units are eligible: sorted symbols C,N,N,H×5 under `pp.fa_molecule` (the 29:121 assertion), and no DOPANT_TAG.
  - The native Cs is excluded, as in 29:363 (scripts/16 includes it).
- **B site: the Pb index.** All 20 Pb are eligible.
- **X site: the I index.**
  - `vi` raises `ValueError`. For j = vi, 29:273 would silently return another atom. The X builders and `scn_search` require `vpos` (s2b-2); in `s2b-1` a direct call without it skipped the test and substituted the vacancy iodide.
  - The MIG_TAG iodide follows `mig`: `"forbid"` (default, for path/NEB use): `migrating_index` asserts I (22:146-153). `"allow"` (binding maps): the dopant takes DOPANT_TAG, the manifest records `replaced_migrating_iodide: true`, and the cell must not reach a path builder.
  - `pp.build_pair` tags only the V cell (22:137-139); the pool hosts carry no tags. On the host leg the MIG iodide is therefore found by index, mig_host = mig + (mig ≥ vi), and the `mig` policy applies to it as well. On m30 the MIG iodide (I138) is also the nearest non-vacancy I (4.285 Å) [R].
- **d_dopant_vacancy.** The true-MIC distance from the **unrelaxed host site atom** to the member's own `vpos` (`pp.build_pair`), as in 29.
- **Anchors [M], recorded in every pose.**
  - `fa_centroid`: C plus the mean find_mic vector to the 8 FA atoms (the 16:83 convention, with true MIC).
  - `fa_carbon`: the carbon itself (07:296-299).
  - `pb8_centroid`: C plus the mean find_mic vector to the 8 nearest Pb. It is accepted only if, in frame Q, the 8 vectors occupy the 8 octants once each.
  - Default for molecules: `fa_centroid`. The molecule's unweighted centroid is placed on it, so the molecule inherits the FA's off-centring from the pb8 point, 0.235 ± 0.102 Å (n = 684) [R]. Attributing this offset to N–H···I hydrogen bonding is plausible but untested.
  - Default for atomic ions: `pb8_centroid`. The relaxed native Cs lies 0.132 ± 0.055 Å from this point (n = 36, one per member; an earlier n = 37 also counted the 233-atom reference cell) [R], and it has the largest nearest-I clearance of the three anchors (3.88–4.52 Å) [R].
- **Pseudo-cubic frame Q.** Q = UVᵀ, the polar factor of A = P⁻¹·cell = UΣVᵀ. P = `supercell_P` in `results/fa_host/fa_host_build.json` = [[-2,1,2],[2,1,2],[2,2,-1]]. The rows of Q are the pc axes. All 36 pool cells are identical [R], so one Q serves the pool.
- **FA frame (`inherit`).** Na < Nb by index; v denotes the find_mic vectors from C; e1 = unit(v(Nb) − v(Na)). h = v(H_C), where H_C is the H nearest to C; e2 = unit(h − (h·e1)e1); e3 = e1 × e2.
- **X frame.** Pba < Pbb are the two nearest Pb, ordered by index. Assert that the third-nearest Pb is farther than 5.0 Å (the minimum non-bonded I–Pb in the host is 6.518 Å [R]). a = unit(find_mic(Pbb − Pba)). k = argmax |q_k·a|, the pc axis along the bond (|q_k·a| ≥ 0.9977, next largest ≤ 0.068 over the 2160 pool X sites [R]). b = Q row (k+1) mod 3, projected ⟂ a and normalised; c = a × b. A global choice is needed because the Pb–I–Pb plane is undefined on near-linear bonds (up to 179.8° [R]). The first draft took "the Q axis with the smallest |q·a|", which is ill-conditioned: two Q axes are nearly ⟂ a, and their |q·a| differ by < 0.01 at 54% of X sites (by 3.5 × 10⁻⁶ at worst) [R], so b could turn by 90° between relaxed partners.

## 4. Geometry per dopant

Templates are rigid. In the body frame y is the polar (C2) axis, xy is the molecular plane and z = x × y.

| ion | parameter | value | source / status |
|---|---|---|---|
| GA | S1 recipe, frozen | N_new = C + 1.33 û(C→H_C); H = N_new + 1.01(0.34û ± 0.95ŵ), ŵ = n̂(NCN) × û; delete H_C | Repo constants 22:96-103 = 29:128-132, uncited. Gives C–N–H 109.7° and H–N–H 140.6° [R]. Reproduce only, never reuse |
| DMA | C–N; C–N–C | 1.49 Å; 114° | **[U] provisional.** Neutral (CH₃)₂NH: 1.462(5) Å, 112.2(2)° (Wollrab & Laurie 1968 [S]). Check the cation against (CH₃)₂NH₂Cl or the CSD; the citation "Lindgren & Arran 1972" could not be verified by the critic (author list and year), so confirm it before use |
| DMA | N–H; H–N–H | 1.020 Å; 109.47°. NH₂ in the yz plane, bisector along +y (away from the C atoms) | Host FA mean N–H 1.0198 Å [R]; ideal tetrahedral angle [M] |
| DMA | methyl | C–H 1.094 Å; N–C–H 109.47°; one H anti to the other C (H–C–N–C′ = 180°). Point group C2v | Host FA mean C–H 1.0939 Å [R]; conformer [M] |
| AA | C1–N; C1–C2 | 1.307 Å; 1.477 Å | Cannon, White & Willis 1976, acetamidinium chloride [S] |
| AA | N–C1–N; N–C1–C2 | 121°; 119.5° (planar CCN₂, C2 bisecting) | 120.9(3)° in another acetamidinium salt [S], rounded [M] |
| AA | NH₂ | N–H 1.020 Å; C1–N–H = H–N–H = 120°; coplanar | [R]; 120° as in make_guanidinium (04:98-111) |
| AA | methyl | C–H 1.094 Å, tetrahedral; one H ⟂ the plane (H–C2–C1–N = 90°). Point group Cs | [R]; [M]. Of the staggered rotamers this one maximises H(N)···H(C) in the template (2.32 Å, against 2.20 Å with an in-plane H) [R] |
| Cs, Rb | position | the anchor point (+ offset, section 5). A displaced start may not bring the ion closer to an X than min(4.000 Å, the centred start's nearest A–X) (s2b-2) | [M]; 4.000 Å is the shortest Cs–I of the relaxed native Cs over the pool [R] |
| Sr, Ca | position | the replaced Pb's own position (symbol swap) | S1 Sr construction, 29:376-379 |
| Cl | position | centred: the I position. Shifted: Pb_t + 2.837 Å · unit(X − Pb_t) | 2.837 Å = Pb–Cl in cubic MAPbCl₃ (Poglitsch & Weber 1987 [S]). The one-sided shift itself, which leaves the other Pb–Cl at about 3.7 Å, is [M] |
| SCN | S–C; C–N; S–C–N | 1.639 Å; 1.172 Å; 180° | Pb(SCN)₂: Mokuolu & Speakman 1975, COD 2106398, computed from the deposited coordinates [V]. Observed 178.6°; linear [M]. Neither the CIF nor the computation is archived in the repository: store the CIF sha256 and the computing snippet beside the first manifest, or treat these values as [S] |
| SCN | bound contact | r_ref(S) 3.066 Å, r_ref(N) 2.734 Å, ±0.15 Å. s2b-2: an end is bound iff it lies in this distance window; an end in the window of Pba or Pbb with ∠Pb–E–C < 90° is ambiguous and rejects the pose | Means of Pb–S 2.996×2/3.135×2 and Pb–N 2.687×2/2.781×2 in Pb(SCN)₂ [V]. The ±0.15 Å covers that spread [M]. The 90° floor is [M]: it lies below the observed 106–132°, and the chosen starts sit at 90–106° (section 5). These are contacts of 8-coordinate Pb (4 S + 4 N); transferring them to 6-coordinate Pb in the perovskite is [M] |

- **Provisional entries.** Entries tagged [S] or [U] are provisional. CLI `build` refuses DMA, AA and the shifted Cl starts without `--allow-provisional`, and records the flag when it is given. The self-test always runs. Verifying a primary source flips the tag.
- **GEOM_SHA.** It is the sha256, as canonical JSON, of the numeric parameters of this table together with the section 6 clash parameters (f, f_w, the class map and the thresholds), not of the Markdown text. Every manifest carries it with `BUILDER_VERSION`, because 29's protocol has no builder field (29:280).

## 5. Orientation: `inherit` and `sampled`

**The pose is resolved once, on the host leg.** The V leg evaluates the same parameters in its own local frame, as Sr sits on each partner's own Pb and GA follows each partner's own FA in 29. On unrelaxed partners the frames coincide, so the appended atoms are bitwise identical.

- **`inherit`.**
  - A-site molecules use R = [e1 e2 e3]: DMA: C–N–C on the FA N–C–N, with the NH₂ bisector along the former C–H. AA: C1–C2 along the former C–H, with the N atoms on the FA N side. GA: the S1 recipe. The match is by shape [M]: for DMA it puts the methyl groups, not the N–H donors, where the FA N–H···I contacts were, so `inherit` does not preserve the host's hydrogen-bond pattern.
  - Atomic ions sit centred on the anchor; Cl is centred; Sr and Ca have only this mode.
  - SCN has no `inherit` (there is no molecular frame to inherit) and raises.
- **`sampled` (`resolve_poses`).** Poses come in a fixed order. Only poses admissible on the host leg are kept, and every rejection is logged. Which poses are relaxed is the scan's decision.
  - **DMA, AA:** `inherit`; `inherit_flip` (R·C2(ẑ) = C2(e3)·R, a 180° turn about the plane normal that reverses the polar axis; ẑ is the body axis, so the body-frame C2 multiplies R on the right, and a lab-frame C2(e3) on the left); the six classes below; `n_random` Haar draws (default 0).
  - **Cs, Rb:** centred, plus 6 starts displaced 0.30 Å along ±Q axes [M]. The value 0.30 Å is about the largest relaxed off-centring of the native Cs in the pool (0.294 Å [R]). That figure bounds the step length only, not the contacts: the native Cs moves where the cage allows (its nearest I is longer than at its pb8 point in only 25 of 36 members [R]), whereas a blind ±Q step can close an A–X contact. s2b-2 therefore rejects a displaced start whose nearest A–X is shorter than min(4.000 Å, the centred start's nearest A–X); 4.000 Å is the shortest Cs–I of any relaxed native Cs in the pool [R]. On m30 / m05 / m12 this keeps 124 / 115 / 124 of 133 Cs (and Rb) starts, every centred one included [R]; in `s2b-1` 11 / 18 displaced starts on m30 / m05 had Cs–I < 4.000 Å, down to 3.707 Å.
  - **Cl:** centred, shifted towards Pba, and shifted towards Pbb.
  - **SCN:** one pose per binding class.
  - **Sr, Ca:** one pose.

High-symmetry classes for the C2v-like ions. Body axes are given in Q coordinates. Orbit sizes count distinct poses under O; the count under O_h is the same because both ions are achiral (inversion equals a molecular C2 that reverses y). These equivalences hold for an ideal cubic cage only. The real A site has no symmetry, so a class is a sampling label and only one member of its orbit is built [M]. **Corrected in s2b-2.** Only c100f, c100d, c110a and c110b are isolated special orientations: their stabiliser in O_h has order 4 (y on a site C2 axis and both molecular mirrors on site mirrors). c111m and c111n have order 2. Each is an interior point of a one-parameter family that keeps one molecular mirror on a cube mirror (rotation about body z for c111m, about body x for c111n); the order stays 2 along the family and rises to 4 only at its ends, y ∥ [001] (a c100d-type pose) and y ∥ [110] (c110a for c111m, c110b for c111n) [R]. The ⟨100⟩ and ⟨110⟩ C2 families (rotation about y) are not sampled either. The first draft's completeness claim is therefore withdrawn: y ∥ ⟨111⟩ is a sampling convention, not a symmetry-fixed pose. It is kept because it completes the three principal directions of the cuboctahedral cage for the polar axis: ⟨100⟩ towards a face (the open window), ⟨110⟩ towards an I, ⟨111⟩ towards a Pb corner. The two ⟨111⟩ members are 30° or more from every other class modulo O and G [R]. The mirror and C2 families between the classes are covered only by the `n_random` Haar draws; sampling each family at a fixed angular step, deduplicated by the 20° rule, is an open option (section 12).

| class | body y | body x | orbit |
|---|---|---|---|
| c100f | [100] | [010] | 12 |
| c100d | [100] | [011]/√2 | 12 |
| c110a | [110]/√2 | [001] | 12 |
| c110b | [110]/√2 | [1-10]/√2 | 12 |
| c111m | [111]/√3 | [11-2]/√6 (plane = {110} mirror) | 24 |
| c111n | [111]/√3 | [1-10]/√2 (plane = {112}) | 24 |

- **Orbits.** The orbit of a class is {Qᵀ·g·F : g ∈ O}, with O the 24 proper signed permutations. For the orbit-12 classes these 24 matrices coincide in pairs modulo G (g·F and g·F·C2(y)), so the orbit is deduplicated modulo G before ranking.
- **Class realisation.** A class is realised by the orbit member with the smallest misorientation ω from the inherit frame. Ties (|Δω| < 10⁻⁹ rad) go by a fixed enumeration of O. If that member is inadmissible, the next one is tried; if none is admissible, the class is logged as "infeasible at site".
- **Redundancy.**
  - ω(R1,R2) = min over h ∈ G of arccos((tr(R1ᵀR2h) − 1)/2).
  - G = C2(y) for DMA, and C2(y) of the skeleton for AA, ignoring the methyl rotor [M].
  - A pose counts as new only if ω ≥ 20° to every earlier pose. The 20° is [M]. It is not the tolerance of 29:410, which bounds the rotation of far-field FA axes (atoms > 6 Å from the dopant and the vacancy; an axis angle with two degrees of freedom). Script 29 never checks the dopant's own orientation, only the displacement of its centre (< 1.0 Å).
- **Random poses.**
  - The generator is `default_rng(zlib.crc32(label.encode()))`, with label = `f"{member}_{token}{site}"`, shared by both legs (as 35:42). s2b-2: this seed key is independent of the CLI `--label` and of the host file name (`--member`, default the host stem), and `resolve_poses` refuses `n_random > 0` with a key that does not end in `_{token}{site}`, or for a token without random poses.
  - Each draw is a Shoemake quaternion from `rng.random(3)` (as 07:221). It is kept if admissible and new; at most 50·n_random draws are made.
  - Numpy does not guarantee its streams across versions, so the manifest stores each resolved R and the numpy version.
- **SCN search (deterministic, no seed).**
  - C = X + s·a + ℓ(cos ψ b + sin ψ c); the rod direction (S→N) is cos θ a + sin θ (cos φ b + sin φ c).
  - Grid: s from −1.2 to 1.2 Å in steps of 0.3; ℓ ∈ {0, 0.25, 0.5, 1.0, 1.5, 2.0} Å; ψ, φ in steps of 15°; θ from 0° to 180° in steps of 10°. That is 590 976 poses per site, including the degenerate ψ at ℓ = 0 and φ at θ = 0° or 180°, which are kept for a fixed grid order (about 0.5 s per site, vectorised).
  - The first draft cited an unarchived exploratory m30 scan with clash-free starts in every class at every X site. This is not reproduced. With SCN atoms in class X (first draft), only 2 of 60 m30 X sites admit any class [R], and S:ab is excluded by geometry at most sites (below). With the `s2b-1` class Y rule (f_w × Bondi for every Y pair), m30 / m05 gave at least one class at 60/60 / 60/60 sites, but every start pressed an SCN atom against an I⁻ (N···I down to 2.84 Å) and about 20% carried an unlabelled Pb contact (section 15).
  - **s2b-2 feasibility** (revised class Y rule of section 6 and distance-based bound state below), over the 59 non-vacancy X sites [R]:

    | host | sites with ≥ 1 class | S:a | S:b | S:ab | N:a | N:b | SN:ab | SN:ba |
    |---|---|---|---|---|---|---|---|---|
    | m30 | 47 | 37 | 41 | 0 | 15 | 14 | 16 | 16 |
    | m05 | 52 | 45 | 39 | 1 | 15 | 15 | 15 | 12 |
    | m12 | 48 | 40 | 39 | 1 | 9 | 10 | 14 | 14 |

    On m30 the two X sites nearest the vacancy, I138 (the MIG iodide) and I49, admit **no** class; at I49 this follows from the Y–I and C(SCN)···H rules together [R]. T4 therefore asserts the class set per site (I49 and I138 empty, I175 S:a, S:b, N:b) and no longer requires a class at every site. SCN binding at the first-shell sites cannot be started from an unrelaxed cage under these thresholds (section 10).
  - End E is bound to Pb_t iff |d(E,Pb_t) − r_ref(E)| ≤ 0.15 Å (s2b-2: distance only). A pose with an end in the window of Pba or Pbb at ∠Pb–E–C < 90° is ambiguous and rejected. In `s2b-1` the angle entered the bound test, so such an end was labelled unbound: 72 / 68 / 72 of 335 / 343 / 342 starts on m30 / m05 / m12, mostly N:a and N:b [R] had a 'non-bound' S inside the Pb–S window, down to 2.916 Å, shorter than both Pb–S distances of Pb(SCN)₂.
  - The classes are the bound-end sets: S:a, S:b, S:ab (μ-S), N:a, N:b, SN:ab (S on a, N on b) and SN:ba.
  - Impossible classes: μ-N: 2 × (2.734 + 0.15) = 5.77 Å, which is less than 6.318 Å, the shortest Pb–Pb in the pool [R]. Both ends on one Pb: impossible for a linear rod with both angles ≥ 90°.
  - Rare class: μ-S needs d(Pba, Pbb) ≤ 2 × (3.066 + 0.15) = 6.432 Å, which holds at only 293 of the 2160 pool X sites (13.6%; mean Pb–Pb 6.514 Å) [R]. Elsewhere S:ab is logged as infeasible without a search.
  - Every pose keeps each end ≥ r_ref(E) − 0.15 Å, and C ≥ 3.066 Å, from every Pb [M]. Poses with no bound end are discarded, and so are poses with an end inside its bound window of any Pb other than Pba and Pbb (this never happens on the m30 or m05 grids [R]; V10 asserts it).
  - Within a class, the pose with the largest minimum clearance (section 6) is taken. Ties within 10⁻⁶ Å go by grid order, so a translated or round-off-perturbed input selects the same pose. The clearance pushes the bound ends to the angle floor: the chosen bound Pb–E–C angles have medians of 93.5–94.7° on m30, m05 and m12, and almost all lie below the 106° of Pb(SCN)₂ [R]. Raising the floor to 100° or 106° leaves 37 or 8 of 59 m30 sites feasible [R], so the floor stays at 90° [M] and every manifest records the bound distances and angles (V10). The angle is not otherwise penalised.

## 6. Clash filter

The threshold thr(p,q) is **0.90 ×** the shortest non-bonded, intermolecular contact of that class pair over the relaxed pool [R, 36 members]. The factor 0.90 is [M].

Classes:
- H; for the H–X pair only, split by the heavy atom the H is bonded to (its nearest C or N): H(N), the N–H donors, and H(C) (s2b-2);
- O: organic heavy atoms (C, N of a cation);
- A: Cs, Rb;
- X: I and Cl;
- Y: S, C and N of SCN (no host analogue; thresholds by the vdW rule below);
- B: Pb, Sr, Ca.

The minima exclude bonds: the Pb–I first shell (the 6 nearest I of each Pb) and FA intramolecular pairs (C–N < 1.6, X–H < 1.25 Å, as 38:59-66).

| pair | H(N)–X | H(C)–X | H–H | H–O | H–B | H–A | O–X | O–O | O–B | O–A | A–X | A–B | X–X |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| host min (Å) | 2.571 | 2.876 | 2.818 | 3.339 | 3.544 | 4.534 | 3.548 | 3.995 | 4.362 | 5.198 | 4.000 | 5.342 | 4.045 |
| thr (Å) | 2.314 | 2.588 | 2.536 | 3.005 | 3.190 | 4.081 | 3.193 | 3.596 | 3.926 | 4.678 | 3.600 | 4.808 | 3.641 |

- **H split (s2b-2).** In the host only the N–H donors make short H···I contacts: over the 36 members, H(N)···I has minimum 2.571 Å and median 2.911 Å (n = 2736), and H(C)···I has minimum 2.876 Å and median 3.246 Å (n = 684); 677 of 684 FA have at least one N–H···I below 3.0 Å [R]. The single `s2b-1` H–X threshold (2.314 Å) was therefore set by hydrogen bonds and let methyl C–H sit at N–H···I distances (down to 2.45 Å among the DMA poses at m30 C128 alone [R]; 2.32 Å over all m05 sites according to the review). Only H–X is split. The other H pairs are set by cage spacing rather than by contacts, and splitting them would tighten them further without a contact rationale, so they stay pooled over both kinds of H (their pooled minimum is the H(N) value).

- **What is tested.** Appended and moved atoms against every retained non-member atom, by true MIC, in both legs. s2b-2: V7 also records the minimum distance of every tested-atom/environment-class pair (for example H(C)–X, H(N)–X, S–X, C–H(N)) and the hydrogen-bond diagnostic `donor_H_X_lt_3A` = [dopant N–H with an X within 3.0 Å, dopant N–H] [M; 3.0 Å is a diagnostic cut, not a threshold]. Both go into every manifest leg.
- **Absolute limits.** A floor of 0.65 Å holds for all pairs (35:71). No appended atom may lie within 1.2 Å of `vpos` (29:411, extended beyond I).
- **Class Y (SCN).** The 0.90 × host-minimum rule cannot be applied to SCN atoms. The X thresholds (X–X 3.641, H(N)–X 2.314, O–X 3.193 Å) come from I–I spacing and I···H/C/N contacts, and with them SCN is admissible at only 2 of 60 m30 X sites [R]. They would also reject physical N(SCN)···H–N hydrogen bonds. Y pairs therefore use Bondi sums, with the radii H 1.20, C 1.70, N 1.55, S 1.80 and I 1.98 Å (Bondi 1964 [S]; recheck against the primary table). **s2b-2 rule.** The hydrogen-bond pairs, the acceptor ends S and N against H, use thr = f_w (r_E + r_H) with f_w = 0.80 [M] (N···H 2.20, S···H 2.40 Å). Every other Y pair (the central C against H, and S, C, N against organic C/N and against I⁻) uses thr = f (r_E + r_h) with the global f = 0.90 (C···H 2.61, N···I 3.177, C···I 3.312, S···I 3.402 Å). The justification is the host itself: its closest non-hydrogen-bonded contacts lie at 0.90–1.06 of their Bondi sums (H(C)···I 0.904, N···I 1.005, I···I 1.021, C···I 1.057), while the N–H···I hydrogen bond lies at 0.808 [R]. `s2b-1` applied f_w to every Y pair, including anion–anion pairs (N···I 2.82 Å) and the central C against N–H, which the hydrogen-bond argument does not cover. Y–A uses the A–X value (3.600 Å), and Y–B follows section 5. f_w and f are frozen (below).
- **Calibration.** f = 0.90 gives an H(N)–I threshold of 2.31 Å, which agrees with the 2.3 Å chosen independently in the exploratory clash checks (not archived).
- **Which thresholds are contacts.** Only H(N)–X (the N–H···I hydrogen bond), H(C)–X and O–X (and, in part, X–X) are close contacts in the host. H–H, H–O, O–O, H–B, O–B and every pair involving A are set by cage spacing rather than by repulsion, so they are strict. For example, O–O 3.596 Å would reject a C···C van der Waals contact of 3.4 Å. Measured consequences under `s2b-1` (critic's re-implementation of sections 4–6) [R]: centred and ±0.30 Å Cs pass at 19/19 m30 FA sites (smallest margin 0.11 Å); shifted Cl passes at 240/240 starts on m30 and m05 (margin ≥ 0.26 Å); DMA `inherit` passes at 19/19 sites on m30 and m05; every DMA class, and every AA class except c110a at one site, has an admissible orbit member at all 19 m30 sites. Under `s2b-2` (m30 / m05 / m12, `resolve_poses` with `n_random` 0) [R]: DMA keeps 141 / 141 / 145 of 152 poses, with `inherit` admissible at 15 / 16 / 19 of 19 sites; AA keeps 112 / 116 / 112, with `inherit` at 4 / 7 / 4; Cs and Rb keep 124 / 115 / 124 of 133; every host keeps at least one DMA, AA, Cs and Rb pose at 19/19 sites. A class whose nearest orbit member now clashes is realised by the next one (section 5), so the class survives at most sites.
- **GA exemption.** The S1 GA recipe reaches H–I 1.99 Å [R], so **GA is exempt from the clash thresholds (report only)**, keeping it comparable with S1. s2b-2: the exemption does not cover the absolute limits; the 0.65 Å floor and the 1.2 Å vacancy exclusion hold for GA as for every token (`s2b-1` let an exempt GA pass both, although no pool GA approaches them).
- **Pairs not tested.**
  - X–B and Y–B: SCN–Pb follows the rules of section 5; Sr, Ca and centred Cl sit on existing sites, and shifted Cl is fixed at 2.837 Å from Pb_t.
  - A–A has no host analogue; the separation of a Cs dopant from the native Cs is recorded instead.
- **Freeze.** The T4 admissibility report is the freeze record: f, f_w, the class map with the H split, the class Y rule and the table are frozen at `s2b-2` (they enter GEOM_SHA, which the self-test pins), and any change must come before any S2 E_b is read. They were first frozen at `s2b-1` and changed once, before any E_b existed (section 15).

## 7. Host/vacancy pairing

- **Index map.** The vacancy cell is the host with only `vi` deleted (22:121), so to_vac(j) = j if j < vi, else j − 1 (29:273). `check_index_map` covers host→V with removed = {vi}.
- **`build_paired`** builds D_j at host site j and D_j+V at to_vac(j). It asserts that:
  - the V cell is the host with only vi deleted (positions and numbers bitwise). `pp.build_pair` picks vi with `pp.mic` and 29:272 with find_mic, so this is checked, not assumed;
  - (s2b-2, both partner modes) the host atom vi lies within 1.2 Å (`vac_excl`) of `vpos` by true MIC. The numbers test alone cannot tell two iodides apart: on m30, host indices 125–127 are all I;
  - (s2b-2, relaxed partners) every inorganic atom (B, X and A ions) lies within 2.0 Å of its counterpart in the host minus vi [M]. Once the numbers agree, an index shift between two iodides moves at least one I slot by the I···I distance (≥ 4.045 Å in the host [R]), so the bound always catches it; organic atoms are excluded because molecular reorientation may move them further;
  - to_vac(deleted_host) == deleted_vac, and the same holds for `modified`;
  - the `added` counts are equal, and the centre maps: for a retained centre c, centre_V = old_to_new_V[to_vac(c)] where centre_H = old_to_new_H[c]; for an appended centre, centre_H − centre_V = 1;
  - the MIG iodide is translated to the host leg (section 3) and the `mig` policy holds on both legs;
  - `check_index_map` passes for each partner→doped map.
- **Unrelaxed partners.** The appended atoms are bitwise identical (`np.array_equal`), the property that `ga_at_carbon` shows on 684 of 684 FA [R].
- **Relaxed partners.** The same parameters are applied in each partner's own frames. The V leg is re-checked for admissibility; if it fails, the pair is rejected and logged. s2b-2: an `Inadmissible` raised by `build_paired` carries `leg` = `host` or `V`.
- **Order.** X builders run on the vacancy cell after `pp.build_pair`, never before it. The order of 28:121-122 would let an X builder substitute the vacancy iodide.

## 8. Validity checks (every built structure)

| id | check |
|---|---|
| V1 | `checks.check_composition(base, atoms, delta)` passes: exact Δ and a changed hash (the Cs_A no-op incident) |
| V2 | len = len(base) − \|deleted\| + \|added\|, equal to the registry's host or V count |
| V3 | isovalence: formal charge removed equals formal charge added; valence electrons even (no vacancy) or odd (V) |
| V4 | `checks.check_index_map(old_to_new, …, removed=deleted)` passes; retained non-member atoms bitwise unchanged, tags included; MIG 99 survives unless `mig="allow"` replaced it |
| V5 | every template bond and angle within 1e-6 Å / 1e-4° by find_mic (rigid placement is exact to round-off); GA against its own recipe constants |
| V6 | topology: the dopant bond graph equals the template's (C–N < 1.6 and X–H < 1.25 Å as 38:59-66; C–C < 1.7 and C–S < 2.0 Å [M]); no dopant–host bond under the same cutoffs; intact-FA count = host − 1 (A) or unchanged (B, X) |
| V7 | the clash filter of section 6 (thresholds report only for GA; the floor and the vacancy exclusion hold for GA too, s2b-2); pair minima and the donor diagnostic recorded; for displaced Cs/Rb, the A–X rule of section 5 (s2b-2) |
| V8 | cell and pbc `array_equal` to the input; calc None; no constraints; no masses, initial_magmoms or charges arrays |
| V9 | appended atoms satisfy −10⁻¹² ≤ s < 1 (round-off of recomputed fractional coordinates after the fold of section 1) |
| V10 | site checks: an A target is an intact, untagged FA and passes the pb8 octant test; an X target ≠ vi (vpos required, s2b-2), obeys the MIG policy on both legs and has the Pb gap; SCN class constraints hold with the distance-based bound state and no ambiguous end (s2b-2), no SCN end is bound to a Pb other than Pba or Pbb, and S:ab occurs only if d(Pba, Pbb) ≤ 6.432 Å. Records Pba/Pbb in both index spaces (`*_input`, `*_out`, s2b-2) and the bound distances and angles |

## 9. Self-test (`python scripts/42_s2_builders.py --self-test [--members all]`)

- **Inputs.** Real files only, with m30 as the default (`all` = 36 members). The reference vacancy comes from `s29.ref_vacancy_position` with `results/fa_host/fa19cs1_pb20i60_233.extxyz` and `fa19cspb20i59_232_vI.extxyz`; the unrelaxed V partner comes from `pp.build_pair`.
- **Output.** PASS/FAIL per case, exit code 1 on any failure (`rb_model_note.py` style). The test ends by asserting `"mace" not in sys.modules`.

| case | content |
|---|---|
| T1 | each template reproduces the table to 1e-9 Å and is invariant, with atom permutation, under its exact proper group. DMA: C2(y) on all 11 atoms. AA: C2(y) on the 8 skeleton atoms only; the full AA template has Cs symmetry (proper group C1), and C2(y) maps its methyl onto the 60°-rotated rotamer that G ignores. GEOM_SHA printed. s2b-2 adds: GEOM equals a literal copy of the section 4 table and GEOM_SHA equals the value pinned for the BUILDER_VERSION; every section 6 threshold and class-Y sum is pinned; the six class frames are ≥ 20° apart modulo O and G; the O_h stabiliser orders are 4, 4, 4, 4, 2, 2, with order 4 only at the ends of the c111m and c111n families; ω(inherit, inherit_flip) = 180°; `fold` keeps points within 10⁻¹⁶–10⁻¹² of a lattice plane in [−10⁻¹², 1); the m30 host has 76 H(N) and 19 H(C) |
| T2 | **GA regression**: every FA carbon (19 per member), host and V legs, against `s29.ga_at_carbon`: numbers and positions of retained atoms bitwise; tags bitwise on non-members, with member tags 77 in 42 against 0 in 29 asserted explicitly; appended atoms ≤ 1e-12 Å raw (`wrap_new=False`) and ≤ 1e-12 Å by find_mic (default); centre == c_new; deleted == (i_ch,) |
| T3 | **Sr regression**: every Pb, both legs, numbers and positions exactly equal (difference 0) to copy-and-swap (29:376-379); tags equal except DOPANT_TAG on the Sr |
| T4 | every token on m30, inherit and sampled poses. Sites: A = FA128 (nearest C) and the farthest FA; B = Pb124, Pb136 and the farthest Pb; X = I49 (the nearest I that is neither vi nor the MIG iodide, 4.327 Å), I138 (the MIG iodide, built with `mig="allow"`; under the default it must raise, T6) and the farthest I (I175). V1–V10 pass for every admissible pose; registry Δ and counts asserted; admissibility report written. s2b-2: the kept poses of every case equal a pinned list; SCN classes are I49: none, I138: none, I175: S:a, S:b, N:b [R]. Orientation definitions: at all 19 m30 FA sites the `inherit` DMA has its NH₂ bisector within 1° of the former C–H and C–N–C on the FA N–C–N, and the `inherit` AA has C1→C2 within 1° of the former C–H with its N on the FA N side (recomputed from the host); `inherit` builds equal anchor + body·Rᵀ; every `inherit_flip` is R·C2(ẑ) at 180°; for every realised class, each orbit member (deduplicated modulo G independently) nearer the inherit frame is built and must be inadmissible |
| T5 | pairing for every T4 case: to_vac mapping, `check_index_map` in both directions, keep correspondence, bitwise-identical appended atoms, and `pp.migrating_index` still resolving an I in the V leg |
| T6 | refusals: X at vi; the MIG iodide under "forbid"; A on the native Cs, on a dopant carbon or on a non-FA C; an unknown token; provisional entries without the flag. A pose rotated into a clash raises `Inadmissible` and leaves the input unchanged. s2b-2 adds, each checked by its message or failing rule: X builders and `scn_search` without vpos; an intact FA carrying tag 77 (only the tag rule can refuse it); a GA anchor, `n_random` for Cs and a malformed seed key; V cells with one atom moved by 10⁻⁶ Å or with the wrong iodide deleted; a wrong vi in unrelaxed and relaxed mode (also with vpos-consistent positions); the vacancy exclusion (DMA on the V leg, GA) and the 0.65 Å floor (Cs on a moved native Cs, GA); a pb8 octant failure; CLI: options that do not apply, a second run into the same label, case-variant and symlinked `--out` paths into `dopant_shell` (whose listing must not change), and a random-pose seed independent of `--label` |
| T7 | PBC: every m30 FA that straddles the boundary (267 of 684 over the pool [R]), with every A token. Translation equivariance: shift the host so that a test FA C and a test I sit at fractional 0.999 on each axis in turn, and shift the reference vacancy position by the same vector (otherwise `pp.build_pair` may pick another vi); the result must equal the translated build modulo the lattice to ≤ 1e-10 Å, with the same SCN class and parameters |
| T8 | determinism: `resolve_poses` twice gives identical output; two labels give different random members; pairwise ω ≥ 20°; class representatives do not depend on `n_random` |
| T9 | recomputed pool class minima equal the section 6 table to 1e-3 Å, H(N)–X and H(C)–X separately (only a WARN if the pool is absent). s2b-2: the section 3 anchor figures, computed with `a_anchor`, equal 0.235 ± 0.102 Å (FA, n = 684), 0.132 Å (Cs mean, max 0.294, n = 36) and 3.881–4.521 Å (nearest I to pb8) to 1e-3 |
| T10 | the parity and formal-charge table for every token, both legs |
| T11 | **relaxed-partner emulation**. 29:381-382 applies `ga_at_carbon` to relaxed partners, which differ, so T2 alone tests only the coincident case. Rattle the host and V legs independently (seeded, σ = 0.05 Å). GA must match `s29.ga_at_carbon` on each rattled leg. For every token, the V leg must evaluate the host-leg parameters in its own frame and be re-checked for admissibility, and the X-frame b must not jump (b_H·b_V > 0.99). s2b-2: only `Inadmissible` counts as a rejection, split into host-leg and V-leg rejections; `Refused` fails the case |
| T12 | **non-template geometry**: shifted Cl is 2.837 Å ± 1e-9 from Pb_t and collinear with Pb_t–X; displaced Cs/Rb lie exactly 0.30 Å from the anchor along ±Q; SCN rod lengths and linearity, bound windows and angles; μ-N and third-Pb binding never occur; S:ab only within the 6.432 Å bound; X frame well conditioned (|q_k·a| > 0.95, and a 1e-4 Å rattle of the two Pb changes b by < 1e-3). s2b-2 adds: both anchors equal an independent recomputation (ase `get_distances`) to 1e-12 Å at every m30 FA; no admissible displaced Cs/Rb is closer to an X than min(4.000 Å, centred), and the rule fires at least once on m30; each SCN class label equals the coordination recomputed from the atoms by distance, with non-bound ends outside the windows; `*_out` indices name the bound Pb and the MIG iodide in the written cells; each SCN class takes the largest admissible clearance and the first grid point within 10⁻⁶ Å (recomputed from the full grid), with the I175 grid points pinned |

## 10. Chemistry caveats; what the builder claims

- **Claims and non-claims.** Output is an **unrelaxed starting structure**.
  - Claimed: composition, isovalent bookkeeping, topology, contacts above the frozen thresholds, and deterministic paired placement.
  - Not claimed: that a pose is a minimum, that a relaxation stays in its basin, any energy, or experimental incorporation.
- **Cl⁻.** Shannon CN6 radii: Cl⁻ 1.81 Å, I⁻ 2.20 Å [V]. A centred Cl has Pb–Cl 3.26 Å, against 2.837 Å in MAPbCl₃ [S]: 0.42 Å too long. Large relaxation and several basins are possible, hence the shifted starts.
- **Ca²⁺.** Shannon CN6 radii: Ca²⁺ 1.00 Å, Pb²⁺ 1.19 Å [V]. Ca has no 6s² lone pair. Its octahedral factor (0.418 with Travis radii [V]) is near the stability bound.
- **DMA⁺.** r_eff 272 pm (Kieslich et al. 2015 [S]). t = 1.026 with the Shannon Pb radius, 1.077 with the Travis Pb radius. Only the Travis-radius value, which is the consistent comparison, exceeds Travis's tentative upper limit of 1.06 for iodides (Travis et al. 2016 [V]); the Shannon-radius value does not. DMAPbI₃ is hexagonal and incorporation is limited [S]. Strain is expected on relaxation. **Hydrogen-bond inversion (s2b-2).** The `s2b-1` statement that clashes are not expected is withdrawn: it rested on an H–X threshold set by N–H···I hydrogen bonds, which let methyl C–H sit as close as 2.45 Å to I at m30 C128 alone [R] (2.32–2.35 Å over all sites of three hosts, according to the review). With the H split, DMA keeps 141 / 141 / 145 of 152 m30 / m05 / m12 poses, but the starts invert the host's hydrogen-bond pattern: only 25 / 27 / 28 of them have a DMA N–H within 3.0 Å of an I⁻, whereas 677 of 684 host FA have one [R]. The `inherit` match puts the methyl groups where the FA N–H···I contacts were (section 5), and the clearance-limited classes do not seek donor contacts. A DMA E_b from these starts therefore depends on the relaxation finding the N–H···I contacts. AA keeps its donors in contact (111 / 114 / 109 of 112 / 116 / 112 poses) [R]. Every manifest records the donor count; an anchor or a short translation search that brings the NH₂ donors to I is an open option (section 12).
- **AA⁺.** With r_eff 277 pm (Kieslich et al. 2015 [S]), t = 1.037 / 1.088 (Travis 2016 [V]). Under the `s2b-1` thresholds the in-place `inherit` clashes at 14 of 19 sites on m30 and 12 of 19 on m05 (critic's re-implementation [R]; the first draft's 9–12 was not reproduced); under `s2b-2` at 15 / 12 / 15 of 19 on m30 / m05 / m12 [R]. The binding contacts are mainly H(N)···I at 2.05–2.28 Å. With centroids matched, AA's C1 sits 0.65 Å from the former FA carbon towards the N side, and putting C1 on the carbon instead is worse (1–2 of 19 admissible) [R]. The sampled classes are therefore needed.
- **Cs⁺, Rb⁺.** t(CsPbI₃) = 0.851 / 0.893. t(RbPbI₃) = 0.818 / 0.858, below Travis's lower boundary of 0.875. The cavity is under-filled: Shannon contacts of 4.08 Å (Cs–I) and 3.92 Å (Rb–I), against 4.62 Å from cavity centre to I [R]. Rb is not incorporated into the 3D lattice experimentally (Kubicki et al. 2017 [S]), so Rb rows are hypothetical. A Cs dopant makes a second Cs in the cell; their separation is recorded.
- **SCN⁻.** It adds 2 atoms and 8 valence electrons. A linear Pb–N–C–S–Pb bridge needs 8.5–8.7 Å, but only 6.52 Å is available [R]. The binding class at a 3D APbI₃ X site is unknown [U], and sterics cannot choose it [R], except that μ-S is geometrically excluded at 86% of X sites (section 5). In PBE-D3 FAPbI₃, Pb–Pb across the SCN site widens from 6.35 to 6.57 Å (Lu et al. 2023 [V]). **Anion–anion contacts (s2b-2).** No unrelaxed SCN start avoids short contacts with the neighbouring I⁻: the best start per site keeps an SCN atom within 3.18–3.74 Å of an I⁻ (medians 3.43 / 3.42 / 3.41 Å on m30 / m05 / m12), against 4.045 Å for the shortest host I···I [R]. Under the `s2b-2` thresholds (N···I ≥ 3.177, S···I ≥ 3.402 Å) SCN is infeasible at 12 / 7 / 11 of 59 sites, including both first-shell sites of m30 (I138, I49) [R]. The rigid cage, not the builder, sets this limit. SCN E_b values should not be compared until the starts are made physical on the node, for example by a constrained pre-relaxation of the neighbouring iodides with the SCN held, or by building into a cage whose two Pb and nearest I are first moved outward; both are outside this geometry-only builder (section 12).
- **Host.** a_pc is 6.512 Å, against 6.362 Å experimentally (Weller et al. 2015 [S]), i.e. +2.4%. Small ions (Cl, Ca, Rb) are therefore more under-bound than in experiment. Host FA orientations differ from the room-temperature picture [S], and `inherit` carries that artefact.

## 11. Out of scope and pending

- **Relaxation protocol.** Staged fmax, and a frozen far field taken by whole molecule, including two-carbon cations and the S of SCN (PLAN amendment m; 40:9-23).
  - The energy level follows the WP3 outcome. The WP3 model cannot evaluate Cl, S, Ca or Rb (PLAN.md:1179-1186).
  - On the node, confirm that zero-shot MACE-MP-0 covers Z = 16, 17, 20 and 37 (`calc.models[0].atomic_numbers`, as at 33:525-527). (2026-11-03: read on the laptop for the foundation file of sha256 `01bfe221…`, 89 elements, all four covered; no structure was evaluated. The node copy is checked by its sha256, `S2_PLAN.md` §5.)
- **Binding-map automation.** A new numbered script that loads 29 for `relax_staged`, `basin_dev` and `ref_vacancy_position`. It should: take sites by registry sublattice; run the refill check over every X species; record the builder id and pose in its protocol; use labels such as `{h}_{TOKEN}{j}o{k}_{novac|vac}` (a proposal); pre-register the X-site shells (first shell 8 I, cut in the 5.12–5.48 Å gap [R]).
- **Also out of scope.**
  - Hop classes, including whether dopant-migration hops count.
  - A generalised topology check to replace `35 sane()`; this needs a PLAN amendment.
- **Pseudopotentials** (corrected 2026-11-03).
  - pslibrary 1.0.0 US PBE files, following the repository's spn/-n- pattern: `Cl.pbe-n-rrkjus_psl.1.0.0.UPF`, `S.pbe-n-rrkjus_psl.1.0.0.UPF`, `Ca.pbe-spn-rrkjus_psl.1.0.0.UPF`, `Rb.pbe-spn-rrkjus_psl.1.0.0.UPF`.
  - **All four exist; S exists as an `-n-` file** (and also as `S.pbe-nl-rrkjus_psl.1.0.0.UPF`). The earlier statement that S might exist only as `-nl-` is withdrawn.
  - **Downloaded 2026-11-03 with approval** (the PI's delegation of that date, `S2_DECISION.md`), from the source of the S1 set (`ehpc/EHPC_REBUILD_GUIDE.md` §A5): the four files above and the S `-nl-` variant. Their sha256 and header fields are recorded in `PSEUDOPOTENTIALS_S2.md`. They are kept off-repository and are not yet on the node. The Pb(SCN)₂ CIF has not been downloaded (SCN is deferred).
  - `z_valence` (Cl 7, S 6, Ca 10, Rb 9, equal to section 2) and the suggested cutoffs were read from the downloaded files; every suggested cutoff lies below 50/400 Ry (the S1 set suggests 46/326 Ry, 30:12). The node copies are checked against the recorded sha256.
  - Put the extended PSEUDO in a new QE writer. `30` stays unchanged, and the 30:32-34 fingerprint is kept.
  - **Cutoff spot check** for each new element: E(doped) − E(host) for one unrelaxed host-leg cell at 50/400 Ry and at max(60/480 Ry, the suggested cutoff), i.e. 60/480 Ry. The pass is ≤ 5 meV [M], pre-registered as gate G1 in `S2_PLAN.md` §7. No suggested cutoff exceeds 50/400 Ry, so the standing-rule-1 case does not arise.
  - Isolated-atom moments for a 31-style MOMENT: Cl 1, S 2, Ca 0, Rb 1 (Hund's rules).

**Downstream hard-coded assumptions that S2 must generalise later (not changed now):**

| location | assumption | S2 needs |
|---|---|---|
| 29:203, 363, 376-384 | any name other than Sr builds GA on every C | never pass S2 tokens to 29; dispatch by registry |
| 29:358-360, 411 | the refill check counts only I | every X species |
| 29:280-306 | protocol and resume carry no builder identity | BUILDER_VERSION, GEOM_SHA, pose |
| 29:386-390; 40:264-267 | per-atom freeze cut; organic mask = C/N/H grouped by C | whole molecules by centre atom, S included |
| 29:184-187; 22:46-56; 16:54-85 | FA = each C plus its 2 nearest N (by rank) | skip DOPANT_TAG atoms; partners stay undoped |
| 22:32-36, 70, 80, 84; 28:121-122 | SYSTEMS = GA/Sr; `pp.mic`; dopant applied before `build_pair` | a new path builder that uses 42 |
| checks.py:151-168 | exactly one atom moves > 1 Å between endpoints | methyl or SCN rotation may trip it (plausible, not observed) |
| 13:104-108; 11:42-44, 67-72 | nearest Pb–I only; Objective-1 NEB defaults | the new contacts; a new neb.x writer |
| 30:27-30, 56-57; 31:27 | PSEUDO and MOMENT lack Cl, S, Ca, Rb | the new writer and MOMENT entries above |
| 33:85, 87-102, 271-274, 308-317, 662-663; 32:78; 39:138-141, 216, 510 | Z = 7; Sr/GA labels; 28 exclusions; c_D only for Sr and GA; comp() family | S2 outputs outside `dopant_shell/`; new dataset code |
| 34:34-35, 40, 131-132 | shells keyed by dopant name; (host, dopant, site) unique | key by sublattice; add the pose id |
| 35:38, 52-72, 93 | FRAMEWORK = Pb, I, Cs, Sr; sane() accepts only FA and GA | add Ca, Rb, Cl; a graph check |
| 36:58-103; 37:109; 38:45-66, 82; 40:110-117, 205-215, 255-258; 41:63, 129-170, 487 | Sr- and GA-specific centres and selection | the registry centre atom |
| 39:870, 958; 33:311 | vacancy detected as count("I") == 59 | count X-site units |
| 16:29-48 | labels with underscores; Rb only as Rb_int | registry tokens |

## 12. Open questions (PI decisions)

1. Anchor defaults: `fa_centroid` for molecules, `pb8_centroid` for ions.
2. GA in S2: keep the S1 recipe for comparability (this design), or switch to ideal D3h? Sampled GA is not in `s2b-1` or `s2b-2`.
3. Clash calibration: f = 0.90, the class mapping with the `s2b-2` H(N)/H(C) split, and the `s2b-2` class Y rule for SCN (f_w = 0.80 × Bondi for S/N···H only, f × Bondi otherwise; SCN-as-X admits SCN at 2 of 60 m30 sites). The cage-spacing entries (section 6) are conservative. Freeze only after the T4 admissibility report.
4. Primary-source checks: the DMA cation geometry, AA (Cannon 1976) and Pb–Cl (Poglitsch & Weber 1987). Alternatively, take these values from a gas-phase optimisation on the node.
5. SCN: keep every feasible class per site (S:ab exists at only 13.6% of X sites), or fix the class from a one-host DFT pilot?
6. Poses per site entering relaxation. Is each pose a row (which breaks 34:131-132), or is the minimum-energy pose chosen by a pre-registered rule? A one-host pilot could first measure the spread against the 20–25 meV resolution.
7. Rb: keep it as a hypothetical A-site dopant; should it also replace the native Cs?
8. The MIG iodide: "allow" in binding maps, "forbid" for paths.
9. The X-site far shell, and the site range: up to 12 Å (as in 29) or within 7.28 Å (as in 16).
10. (s2b-2) SCN at the first-shell X sites: no unrelaxed start meets the `s2b-2` thresholds at m30 I49 and I138. Choose a node-side remedy before any SCN E_b is compared: a constrained pre-relaxation (SCN held, neighbouring I free), a cage with the two Pb and nearest I moved outward, or a pre-registered looser Y–I threshold with its consequences stated.
11. (s2b-2) DMA donors: add an anchor or a short translation search that brings the NH₂ donors into N–H···I contact (only 25 of 141 m30 starts have one), or accept the inverted starts and rely on relaxation?
12. (s2b-2) Orientation families: sample the c111 mirror families and the ⟨100⟩/⟨110⟩ C2 families at a fixed angular step (deduplicated by the 20° rule), or keep the six labels plus Haar draws?
13. (s2b-2) SCN bound angle: the chosen starts sit at 90–106°, below the 106–132° of Pb(SCN)₂; a 106° floor leaves 8 of 59 m30 sites. Keep the 90° floor, or penalise the angle in the selection?

## 13. Design review (critic)

The critic reviewed the design for chemistry and rigour on 2026-10-29. Checks used ase and numpy only, on `pool_v3_harmonised` m00–m35, and nothing was relaxed. The critic re-implemented the templates (section 4), the clash rules (section 6) and the SCN grid (section 5) in scratch code, which is not archived. Confirmed without change:
- the registry compositions, H counts, atom counts, valence Δ and parity;
- the GA recipe angles (109.7°, 140.6°), H–I 1.99 Å, and bitwise host/V identity on 684/684 FA;
- the identity of all 36 cells and the 267/684 boundary-straddling FA;
- the anchor clearances, the pb8 octant test (684/684), and the twelve class minima of section 6 (all reproduced to 1e-3 Å);
- the 6.318 Å Pb–Pb, 6.518 Å third-Pb and 5.12–5.48 Å vacancy-shell figures;
- the tolerance factors, and the orbit sizes and completeness of the six orientation classes.

Changes:
1. §1 Wrapping: the host overhang is up to 18 atoms (m12) and up to 0.044 fractional (m16), not 17 and 0.022. A fold that rounds to s = 1.0 is reset to 0; V9 allows a −1e-12 round-off.
2. §1 Distances: `pp.mic` overestimates by up to 11.2 Å, not 7.5 Å. The design now states why `pp.build_pair`'s short searches remain exact.
3. §2 Parity: the physical premise of nspin 1 is flagged as untested for doped V cells.
4. §3 MIG: the pool hosts and the host leg carry no MIG tag, so the "forbid" policy could not be enforced on the host leg. It now uses mig_host = mig + (mig ≥ vi).
5. §3 Anchors: Cs off-centring is 0.132 ± 0.055 Å for n = 36 (the n = 37 figure mixed in the reference cell); FA off-centring is 0.235 ± 0.102 Å. The hydrogen-bond attribution is marked untested.
6. §3 X frame: "the Q axis with the smallest |q·a|" was ill-conditioned. Two axes tie to within 0.01 at 54% of X sites, so b could rotate by 90° between relaxed partners. b is now taken from the axis cyclically after the bond axis.
7. §4: the one-sided Cl shift is tagged [M]. The SCN [V] values need archived CIF provenance. The transfer of r_ref from 8- to 6-coordinate Pb is tagged [M]. The unverifiable DMA chloride citation is flagged. The AA methyl rotamer is justified by an intramolecular H···H distance. GEOM_SHA now covers the clash parameters.
8. §5 `inherit`: marked as a shape match [M] that does not preserve the FA N–H···I pattern for DMA.
9. §5 `inherit_flip`: the notation R·C2(e3) was ambiguous and could be implemented about the wrong axis. It is now R·C2(ẑ) = C2(e3)·R.
10. §5 Classes: O_h equivalence is stated as an ideal-cage idealisation. A completeness argument was added. Orbits are deduplicated modulo G, and ties have a tolerance.
11. §5 Redundancy: the 20° threshold was justified by 29:410, but that bounds far-field FA axes, not the dopant. It is now [M].
12. §5 SCN: the claim that every class is clash-free at every X site was refuted. Under the first-draft rules only 2/60 m30 sites admit any class, and μ-S needs Pb–Pb ≤ 6.432 Å (13.6% of sites). The section adds per-class feasibility from measurements, a third-Pb exclusion and a tie tolerance.
13. §6: a new class Y gives SCN atoms vdW-sum thresholds (Bondi [S], f_w = 0.80 [M]). The I-derived thresholds rejected almost all SCN starts and physical N···H–N contacts. The section also says which thresholds are true contacts and reports measured admissibility for Cs, Cl, DMA and AA.
14. §7: `build_paired` also asserts V = host minus vi bitwise, MIG translation and an explicit centre mapping.
15. §8 V10: SCN third-Pb and μ-S bound checks.
16. §9 T1: AA invariance is tested on the skeleton only; the full template is Cs, so the old test would have failed.
17. §9 T2, T3: 42 tags dopant members 77 and 29 does not, so "bitwise" now excludes member tags explicitly.
18. §9 T4: the nearest non-vacancy I on m30 is the MIG iodide (I138), which the default policy refuses. T4 now uses I49, I138 under "allow", and I175, with expected SCN classes.
19. §9 T7: the reference vacancy is translated with the host.
20. §9 new T11 (rattled, non-identical partners, as 29 uses relaxed ones) and T12 (Cl shift, Cs displacement, SCN geometry, X-frame conditioning).
21. §10 DMA: "both t values exceed 1.06" was wrong, because the Shannon value 1.026 does not. The expected rejections are replaced by measured admissibility.
22. §10 AA: the r_eff source is added, and the inherit clash count is corrected to 14/19 (m30) and 12/19 (m05), with the binding contacts.
23. §12: questions 3 and 5 are updated for class Y and the rarity of μ-S.

## 14. Implementation notes (`scripts/42_s2_builders.py`, s2b-1)

This section records `s2b-1` as implemented. Statements that `s2b-2` supersedes are corrected in place only where they would mislead; section 15 lists every change and gives the `s2b-2` figures.

Implemented 2026-10-29, geometry only (ase/numpy; no calculator is created, and the self-test asserts that `mace` was never imported). `python scripts/42_s2_builders.py --self-test` passes all twelve cases on m30 (about 60 s); `--members all` runs T2, T3 and T7 over m00–m35 and also passes (about 390 s). Over the pool, GA matches `s29.ga_at_carbon` at 684/684 FA, with host/V appended atoms bitwise identical; Sr matches copy-and-swap at 720/720 Pb; and the 267 boundary-straddling FA give 1335 A-token builds, all valid (1154 admissible, 181 clashing). GEOM_SHA at s2b-1: `76809b4fd1a79f633af916945b5a0baf686b8c7744ddf50a3cd013689dba1dea` (it also covers the V6 bond cut-offs and the SCN grid and tie tolerances).

**Deviations and resolutions.** Where the design was silent, ambiguous or unworkable, the closest correct behaviour was implemented:

1. **Builder keywords.** The host leg carries no MIG tag (section 3), so a builder cannot apply the `mig` policy unaided. The X builders therefore take `mig_index` (default: the MIG-tagged atom, if any), and `build_paired` passes mig_host = mig + (mig ≥ vi) and mig on the V leg. All builders take `vpos` (the 1.2 Å rule and the X ≠ vi test; required by the X builders since s2b-2) and, where atoms are appended, `wrap_new`. `build_paired` also takes `partners="unrelaxed" | "relaxed"`: the relaxed mode drops the bitwise V = host − vi position check (numbers are still checked) and needs the member's unrelaxed `vpos`. `validate` takes `wrapped`, because V9 applies only to folded atoms (the raw GA builds of T2 are unfolded by design).
2. **A-site eligibility is stricter than the 29:121 symbol test.** `pp.fa_molecule` takes the two nearest N, the nearest H and two H per N. For every untagged GA carbon in the pool (684/684 [R]) this returns C, N, N, H×5, so the symbol test alone accepts GA as FA. An A target must also pass a bonding test (38:59-66 cut-offs): exactly 2 N, 1 H on C and 2 H on each N, forming the same 8 atoms. The same blind spot affects 29:184-187 and 22:46-56 on any cell that contains an untagged GA. This is recorded here only; those files are unchanged.
3. **GA in V5.** The S1 recipe's w = n̂(NCN) × û is not unit length when the C–H bond leaves the NCN plane. N–H and the angles therefore vary from site to site: N–H 1.0186–1.0191 Å, C–N–H 109.69–109.70° and H–N–H 140.59–140.62° over 684 FA [R]. Only C–N (1.33 Å) is fixed. V5 re-evaluates the recipe from the input and requires agreement to 1e-6 Å. The recipe is reproduced unchanged.
4. **Frames of the pose parameters.** The rule that the V leg evaluates "the same parameters in its own local frame" is realised per mode:
   - `inherit` and `inherit_flip`: R = R_FA·M, in the leg's own FA frame;
   - classes and random draws: R = Qᵀ·M, in Q, so random draws are Haar in Q;
   - Cs/Rb offsets: ±0.30 Å along Q rows, from the leg's own anchor;
   - Cl and SCN: the leg's own X frame (Pba, Pbb, a, b, c).

   The anchor type is part of the pose.
5. **Class redundancy.** A realised class within 20° of an earlier pose is dropped and logged as redundant. It is not replaced by the next orbit member. On m30 this never happened for DMA. AA keeps 6 classed poses at C128, because `inherit` and c110a are infeasible there.
6. **SCN.**
   - *Selection.* The "minimum clearance" is min(d − thr) over the section 6 pairs only (Y–H, Y–O, Y–X, Y–A). The Y–B rules are constraints and do not enter the clearance: a bound end lies within ±0.15 Å of r_ref by construction, so counting it would push the selection to the far edge of the window.
   - *Grid order.* s is the outer index, then ℓ, ψ, θ and φ (inner); the design did not fix the nesting.
   - *Arithmetic.* The search uses local vectors from X to the atoms within 8.5 Å. It is exact because the shortest lattice vector (19.33 Å) exceeds 2 × 8.5 Å, which is asserted. Each chosen pose is re-validated with `find_mic`. A search takes about 0.35 s per site.
   - *Third Pb.* The third-Pb exclusion uses the distance window only, which is stricter than also requiring the angle.
7. **SCN rules decide admissibility, not validity.** The V10 class identity, the third-Pb rule and the S:ab bound make up the SCN pose rule. They decide admissibility (`Inadmissible`), not validity (`BuildError`). A host-resolved pose may then lose its binding class on a relaxed V leg, which then rejects the pair (section 7). The site parts of V10 remain validity checks.
8. **SCN is provisional in the CLI.** Section 4 says to treat the SCN values as [S] while no CIF is archived, and class Y uses the Bondi radii [S]. `build` therefore also requires `--allow-provisional` for SCN, as for DMA, AA and the shifted Cl starts. `--pose sampled` for Cl needs the flag as well, because the sampled set contains the shifted starts.
9. **Scope guards.**
   - The X frame and the pb8 anchor use the B-site cations {Pb, Sr, Ca}. In an undoped host this set is the same as "Pb".
   - Class Y has no threshold against Cl (no Bondi Cl radius is given in this design), and an SCN atom in the environment is refused. Multi-dopant cells are therefore refused outside s2b-1.
10. **Folding.** A coordinate with s = −ε is shifted by one more lattice vector, so its recomputed s is −ε (≥ −1e-12, as V9 allows) rather than a literal 0.0.
11. **CLI outputs.**
    - The legs are written as `{label}o{k}_novac.extxyz` and `{label}o{k}_vac.extxyz`, with `{label}_manifest.json` beside them. The default label is `{host stem}_{TOKEN}{site}`.
    - `--out` under `results/objective2/dopant_shell/` is refused. Manifests hold repository-relative paths or bare file names only.
    - extxyz stores positions to 1e-8 Å, so the bitwise identity of the two legs' appended atoms is exact in memory. The written files of the two legs are identical text.
    - Further options: `--mig`, `--anchor`, `--pool`, `--vac-ref`. `sites` flags the MIG iodide.
12. **Self-test outputs.** The T4 admissibility report goes to `--report FILE`, by default a temporary directory, and the self-test writes nothing into the repository. T6 also checks the CLI refusals: the five provisional requests, `--out` under `dopant_shell`, and the MIG iodide under the default policy. It also checks that `--allow-provisional` works and is recorded.
13. **T11 (σ = 0.05 Å per Cartesian component, uncorrelated).** On the rattled m30 host, 2 of 19 FA fail the bonding cut-offs: an artefact of independent rattling, so the GA comparison covers 17 FA. Accepted pairs, and rejections split by the leg that raised `Inadmissible` (corrected in s2b-2: the first version of this table put all rejections on the V leg, but five of the six AA rejections happen on the rattled host leg; `Refused` occurred in neither run):

    | token | accepted s2b-1 | rejected host / V, s2b-1 | accepted s2b-2 | rejected host / V, s2b-2 |
    |---|---|---|---|---|
    | GA | 2 | 0 / 0 | 2 | 0 / 0 |
    | DMA | 15 | 0 / 1 | 14 | 0 / 2 |
    | AA | 10 | 5 / 1 | 10 | 5 / 1 |
    | Cs | 14 | 0 / 0 | 14 | 0 / 0 |
    | Rb | 14 | 0 / 0 | 14 | 0 / 0 |
    | Sr | 3 | 0 / 0 | 3 | 0 / 0 |
    | Ca | 3 | 0 / 0 | 3 | 0 / 0 |
    | Cl | 9 | 0 / 0 | 9 | 0 / 0 |
    | SCN | 4 | 0 / 10 | 3 | 0 / 1 |

    The smallest b_H·b_V is 0.99977. SCN tries only the classes feasible on the rattled host, which `s2b-2` reduces to four over the three T4 X sites.

**Reproduction of the design's [R] figures** (this implementation, ase/numpy only). All are reproduced:
- **Pool.**
  - The twelve class minima of section 6 agree to 5e-4 Å. B–B is 6.318 Å; the third-Pb (X–B) distance is 6.518 Å.
  - 267/684 FA straddle the boundary.
  - X frame over 2160 sites: |q_k·a| ≥ 0.9977, next largest ≤ 0.0679, and the two smallest |q·a| lie within 0.01 at 1175/2160 sites (54.4%).
  - μ-S is geometrically possible at 293/2160 sites; the mean Pb–Pb is 6.514 Å.
  - FA off-centring is 0.235 ± 0.102 Å (n = 684). Cs off-centring is 0.132 ± 0.054 Å (population SD; 0.055 in section 3), with a maximum of 0.294 Å (n = 36).
  - The nearest I to the pb8 anchor lies at 3.881–4.521 Å.
- **AA template.** H(N)···H(C) is 2.324 Å, against 2.200 Å for the in-plane rotamer.
- **Admissibility, m30 / m05.**
  - DMA `inherit`: 19/19 / 19/19. AA `inherit` clashes at 14/19 / 12/19.
  - On m30 every DMA class is admissible at 19/19 sites, and every AA class except c110a, which is admissible at 18/19.
  - Cs and Rb, centred and ±0.30 Å: 133/133 on each host. The smallest margin is 0.107 Å on m30 and 0.059 Å on m05; section 6 quotes only m30.
  - Shifted Cl: 240/240 starts, smallest margin 0.260 Å.
  - SCN, with at least one class at 60/60 / 60/60 sites:

    | class | S:a | S:b | N:a | N:b | SN:ab | SN:ba | S:ab |
    |---|---|---|---|---|---|---|---|
    | sites, m30 / m05 | 60/60 | 60/59 | 58/60 | 60/59 | 51/53 | 49/54 | 4/3 |

  - SCN classes at I49, I138 and I175 are exactly as in T4.

**Observations for the PI (no change made).**
- The largest-clearance SCN poses have small margins: 0.009–0.19 Å at the T4 sites. Under the 0.05 Å rattle of T11, 10 of 14 host-resolved SCN poses were rejected on the V leg. Comparable losses should be expected with genuinely relaxed partners, which bears on questions 5 and 6.
- The T4 admissibility report is the freeze record of section 6. It should be regenerated with `--report` into a location the PI chooses to archive before any S2 E_b is read.

## 15. Review and fixes (2026-10-30, `s2b-1` → `s2b-2`)

A chemistry, code and regression review of `scripts/42_s2_builders.py` and this design returned 23 findings. Each was first reproduced on an unchanged copy of `s2b-1` with ase/numpy only (scratch scripts and mutants, not archived; no calculator, relaxation or MD). A finding was then accepted and fixed, or rejected with evidence; none was rejected. The fixes change the clash parameters, so `BUILDER_VERSION` is now `s2b-2` and `GEOM_SHA` is `58ebbd29fdf179417269818f6fc31b7d55622164929a40778c49208e1cdafedf` (`s2b-1`: `76809b4f…`). Both values are pinned in the self-test. No S2 E_b had been read, so the section 6 freeze rule allowed the change.

| # | lens | finding | verdict | change |
|---|---|---|---|---|
| 1 | chemistry | DMA (and AA) starts point methyl C–H at I⁻ and leave the N–H donors without hydrogen bonds, because one H class treats every H as a donor | accepted | Reproduced: pool H(N)···I min 2.571 Å (n = 2736), H(C)···I min 2.876 Å (n = 684), 677/684 FA with N–H···I < 3.0 Å; at m30 C128 all eight DMA poses (`inherit`, `inherit_flip`, six classes) have their nearest N–H···I at ≥ 3.09 Å and their nearest methyl H···I at 2.45–2.93 Å. H–X is split into H(N)–X (2.314 Å) and H(C)–X (2.588 Å); the other H pairs stay pooled (section 6). V7 and every manifest leg record the pair minima and the N–H···X < 3.0 Å donor count. Section 10 now states the hydrogen-bond inversion (25 / 27 / 28 of 141 / 141 / 145 DMA starts on m30 / m05 / m12 have a donor contact). A donor-seeking anchor or translation search is left open (question 11). T1 and T9 pin the split thresholds and minima |
| 2 | chemistry | Every SCN start presses an SCN atom against an I⁻, because class Y applied the hydrogen-bond Bondi factor to pairs that are not hydrogen bonds | accepted | Reproduced on m30: N···I min 2.836 Å, S···I 3.024 Å, every pose with an SCN atom < 4.045 Å from I⁻, best per site 3.127–3.757 Å (median 3.407), central C within 3.005 Å of an H in 196/335 poses. f_w × Bondi is kept only for S/N···H; every other Y pair, including Y–I and C(SCN)···H, uses f × Bondi, justified by the host's own non-hydrogen-bonded contacts at 0.90–1.06 of their Bondi sums (section 6). The fit is infeasible at the m30 first shell: SCN is admissible at 47 / 52 / 48 of 59 sites on m30 / m05 / m12, and at neither I49 nor I138. Section 10 states that no unrelaxed start avoids anion–anion contacts below about 3.7 Å and recommends a node-side remedy before SCN E_b are compared (question 10). Manifests record S–X, C–X, N–X and C–H minima |
| 3 | chemistry | SCN binding classes are not what the labels say: chosen poses sit at the 90° edge and about 20% have a "non-bound" end inside the Pb window | accepted in part | Reproduced on m30: bound Pb–S–C < 106° in 210/222 ends (median 96.2°), Pb–N–C < 106° in 198/214; 72/335 starts with an in-window end labelled unbound (N:a 35, N:b 32), and 68/343 and 72/342 on m05 and m12; shortest such Pb–S 2.916 Å. The bound state is now decided by distance only; an in-window end of Pba or Pbb at an angle below 90° rejects the pose, in the search and in V10; T12 recomputes each label from the atoms and checks that non-bound ends lie outside the windows; manifests carry the bound distances and angles. Not adopted: raising the 90° floor, because 100° and 106° leave 37 and 8 of 59 m30 sites feasible; the angle edge is stated in sections 4 and 5 and left as question 13 |
| 4 | chemistry | c111m and c111n are not isolated special orientations, so the completeness claim for the six classes is wrong | accepted | Reproduced: O_h stabiliser orders 4, 4, 4, 4, 2, 2; along the c111m (c111n) family the order is 2 and reaches 4 only at y ∥ [001] and y ∥ [110]. Section 5 is corrected: four isolated orientations; the ⟨111⟩ pair is a sampling convention, kept because ⟨111⟩ points the polar axis at a Pb corner; the families are covered only by Haar draws (question 12). T1 asserts the orders, the family ends and a separation of ≥ 20° (measured 30.0°) between class frames modulo O and G |
| 5 | chemistry | Displaced Cs⁺ starts reach Cs–I distances below every native Cs–I contact in the pool | accepted | Reproduced: m30 11 displaced starts below 4.000 Å (shortest 3.707 Å, C164 q0−), m05 18; the relaxed native Cs is farther from its nearest I than its pb8 point is in only 25 of 36 members. A displaced start whose nearest A–X is below min(4.000 Å, centred nearest A–X) is now inadmissible (V7 rule `A-X displaced`); 124 / 115 / 124 of 133 starts remain on m30 / m05 / m12, all centred ones included. Section 5 states that the 0.30 Å step bounds the length, not the contacts. T12 asserts the rule and that it fires on m30 |
| 6 | code | Relaxed-mode pairing accepts a wrong vacancy index | accepted | Reproduced: with vi = 125 on rattled m30 partners the pair was built, its two Cl 4.781 Å apart, host[125] 4.43 Å from vpos. `build_paired` now requires host[vi] within 1.2 Å of vpos in both modes and, for relaxed partners, every inorganic atom within 2.0 Å of its counterpart (section 7); T6 covers both, the second with vpos-consistent positions |
| 7 | code | Pose and V10 records mix index spaces | accepted | Reproduced: SCN at m30 I49 recorded pbb = 124, which is an I in the built cell (the Pb is 123); the MIG iodide recorded as 138 sits at 136 on the V leg. Every index in a pose or V10 record is now `*_input` with an `*_out` partner (None if deleted), and the manifest's `index_map_note` states the index space of every field. T12 checks that `pba_out`, `pbb_out` and `pb_t_out` name a Pb and `mig_index_out` the MIG iodide in the written cells |
| 8 | code | The CLI random-pose seed depends on `--label` and the host file stem | accepted | Reproduced: the same member, token and site gave different R with `--label m30_DMA128_rep`. The seed key is `{member}_{TOKEN}{site}` (`--member`, default the host stem) and is written to the manifest; `--label` names files only; `resolve_poses` refuses a malformed key when `n_random > 0`. T6 builds both labels and requires identical random poses |
| 9 | code | The `dopant_shell` output guard is bypassed by case variants | accepted | Reproduced: `Dopant_Shell` and `Objective2` variants passed the string test and resolve to the protected directory on this file system (only the expression was evaluated; nothing was written). `out_is_forbidden` resolves the path and tests `os.path.samefile` on every existing ancestor. T6 checks both case variants (where the file system is case-insensitive) and a symlink, by the function and by the CLI, and asserts that the directory listing is unchanged |
| 10 | code | Re-running `build` with the same label leaves stale legs and replaces o0 silently | accepted | Reproduced in a scratch directory: 16 leg files after a sampled run and a single-pose run, the manifest listing one leg. `build` now refuses an `--out` that already holds any file of the label, before building and again before writing; files are never overwritten or deleted. T6 checks the refusal and that the first run's files are byte-identical afterwards |
| 11 | code | The GA exemption also disables the 0.65 Å floor and the 1.2 Å vacancy exclusion | accepted | Reproduced: GA with vpos 0.5 Å from its new N was admissible. Admissibility is now (V7 passed) or (GA exempt and floor and vacancy both passed). T6 builds GA next to a fake vpos and next to a moved atom (0.4 Å) and requires `Inadmissible` |
| 12 | code | Options that do not apply are silently ignored but recorded | accepted | Reproduced: a GA anchor and `n_random = 5` for Cs were accepted. GA refuses an anchor; `resolve_poses` and the CLI refuse `n_random` for tokens without random poses; the CLI also refuses `--anchor` for non-A tokens, `--mig` for non-X tokens and `--n-random` without `--pose sampled`. T6 covers the library and CLI cases |
| 13 | code | `fold()` can return s = 1.0 within about 1e-14 of a lattice plane | accepted | Reproduced: out-of-range s in 594 / 178 / 23 / 1 of 20 000 trials at ε = 0 / 1e-15 / 1e-14 / 1e-13. `fold` recomputes s from the folded positions and corrects any component ≥ 1 or < −1e-12 by one lattice vector. T1 folds 18 000 points within 1e-16–1e-12 of a plane |
| 14 | regression | Not a defect: the GA and Sr regression holds | accepted (no change needed) | Confirmed: T2 and T3 pass on m30 and with `--members all` (684 FA, 720 Pb). The `s2b-2` timings are given below |
| 15 | regression | The self-test does not pin the orientation definitions; four non-equivalent mutants pass | accepted | Reproduced: mutants M08–M11 passed the `s2b-1` self-test. T1 and T4 now assert the inherit geometry against the FA at all 19 m30 sites, `inherit` = anchor + body·Rᵀ, the flip at 180°, the class representative against an independently deduplicated orbit (every nearer member built and inadmissible), the class separation, and the kept poses of every T4 case (pinned). All four mutants now fail |
| 16 | regression | Anchor definitions are checked only against themselves | accepted | Reproduced: M12, M13 and M37 passed. T12 recomputes both anchors independently to 1e-12 Å at every m30 FA; T9 asserts the section 3 anchor statistics to 1e-3; T6 refuses a site whose 8 Pb fail the octant test. All three mutants now fail |
| 17 | regression | The SCN largest-clearance rule is untested | accepted | Reproduced: M36 passed. T12 recomputes, from the full grid, the largest admissible clearance per class and the first grid point within 10⁻⁶ Å, and pins the I175 grid points (I49 and I138 now have no class). M36 now fails |
| 18 | regression | The section 6 absolute limits are never exercised | accepted | Reproduced: M14 and M15 passed, and the `s2b-1` report contained no vacancy or floor failure. T6 adds a DMA on the V leg 0.5 Å from a fake vpos (fail rule exactly `vacancy`) and a Cs 0.3 Å from a moved native Cs (fail rule exactly `floor`), plus the GA cases of finding 11. Both mutants now fail |
| 19 | regression | An X dopant at vi is accepted when vpos is omitted | accepted | Reproduced: `build(host, 'Cl', vi)`, `build_x_atomic(host, vi, 'Cl')` and `build(host, 'SCN', vi, 'S:a')` succeeded on m30. The X builders and `scn_search` now require vpos, and V10 fails without it. T6 checks each refusal by its message |
| 20 | regression | Note 13 counts host-leg rejections as V-leg rejections; T11 counts `Refused` as a rejection | accepted | Reproduced: of the six AA rejections, five were on the rattled host leg; DMA 1 and SCN 10 were V-leg; `Refused` did not occur. `build_paired` tags each `Inadmissible` with its leg; T11 counts host and V rejections separately and lets `Refused` fail the case; note 13 of section 14 is corrected |
| 21 | regression | The section 4 parameters and `GEOM_SHA` are not pinned | accepted | Reproduced: M28 (DMA C–N 1.50 Å) passed. T1 compares GEOM with a literal copy of the section 4 table and requires the pinned `GEOM_SHA` of the current `BUILDER_VERSION`, and the threshold table must match its literal copy key for key. M28 now fails |
| 22 | regression | The `build_paired` guard that V = host − vi is never exercised | accepted | Reproduced: M31 passed. T6 passes a V cell with one atom moved by 10⁻⁶ Å and one with the wrong iodide deleted; both must be refused by the position check. M31 now fails |
| 23 | regression | The DOPANT_TAG eligibility rule is not tested on its own | accepted | Reproduced: M07 passed. T6 tags the 8 atoms of an intact FA with 77 and requires a refusal that names the tag. M07 now fails |

**Further changes made while fixing.**
- The H subclass of an H is its nearest C or N, not the 1.25 Å bond cut-off, so a rattled N–H keeps its class (T11); an H with no C or N within 1.6 Å is refused.
- T7 now translates I175 instead of I49, because SCN has no admissible class at I49.
- The self-test prints the elapsed time of failing cases as well as passing ones.

**Mutation check of the revised self-test.** The 13 reviewer mutants (M07–M15, M28, M31, M36, M37) were re-applied to `s2b-2`, together with 14 mutants that each undo one fix (N01–N14: H split, class Y rule, ambiguous-end rejection, displaced A–X rule, relaxed displacement bound, vpos check, GA absolute limits, second fold pass, samefile guard, stale-file refusal, seed key, X-builder vpos requirement, GA anchor refusal, output indices). All 13 reviewer mutants passed the `s2b-1` self-test. Under `s2b-2` all 27 mutants fail at least one case: T1 catches M11, M28, N02 and N08; T4 catches M08, M09, M10, M13, N01, N03 and N14; T6 catches M07, M14, M15, M31, M37, N05, N06, N07, N09, N10, N11, N12 and N13; T9 catches M12; T12 catches M36 and N04 (first failing case listed; several mutants fail more than one).

**s2b-2 self-test.** `python scripts/42_s2_builders.py --self-test` passes all 13 cases on m30 in 82 s. The pool-wide cases were run as three `--members` lists of 12 members (m00–m11, m12–m23, m24–m35), each passing all 13 cases. Together they cover T2 at 684/684 FA, T3 at 720/720 Pb, and T7 at the 267 boundary-straddling FA: 1335 A-token builds, all valid, of which 1113 are admissible and 222 clash (`s2b-1`: 1154 and 181). The machine was memory-bound during these runs, so their wall times (1074–2036 s) cannot be compared with the 390 s of section 14. Every run asserts `'mace' not in sys.modules`.

**Not changed, for the PI.** Questions 10–13 of section 12 (the SCN first shell, DMA donors, orientation families and the SCN angle floor) are decisions, not defects. Regenerate the T4 admissibility report with `--report` before any S2 E_b is read, because the frozen thresholds changed.

## 16. Answers to the open questions (2026-11-03)

Decided 2026-11-03 by the analyst (an AI assistant), to whom the PI delegated the choice of the S2
research direction on that date (`S2_DECISION.md`, "Who decided"). Each answer gives the decision,
the reason and, where one exists, the pilot that decides it; the binding rules are in `S2_PLAN.md`
(section numbers below). Tags as in this file, plus **[I]** for interpretation. "S2" means the route
of `S2_DECISION.md`: dopants Sr (control), Ca, Cl, Cs and GA; Rb, DMA, AA and SCN deferred. No S2
energy value existed when these answers were written.

| # | question (section 12) | decision | reason | pilot that decides it |
|---|---|---|---|---|
| 1 | Anchor defaults | **Accept**: `fa_centroid` for molecules, `pb8_centroid` for atomic ions. | The relaxed native Cs sits 0.132 ± 0.055 Å from the pb8 point (n = 36), and pb8 has the largest nearest-I clearance, 3.88–4.52 Å [R]; FA molecules sit 0.235 ± 0.102 Å off it (n = 684) [R]. In S2 only Cs uses an anchor (GA refuses one; DMA and AA are deferred). | The m30 pose pilot (`S2_PLAN.md` §9) relaxes the centred start and the admissible ±0.30 Å starts and keeps the default only if the Boltzmann aggregate is within 10 meV. |
| 2 | GA: S1 recipe or ideal D3h | **Keep the S1 recipe, frozen**; no sampled GA in S2. | GA is in S2 for continuity with WP1/WP2c and to test whether the frozen far field cures the S1 noise (`WP1_RESULT.md`, "What follows"). A new GA geometry would confound both. D3h would be a new pose needing its own pilot. | None in S2; GA carries a_pose = 0, labelled "S1 recipe; pose dependence not measured". If GA ends "not resolved", an S3 GA pose pilot (D3h against the recipe, DFT spread against 10 meV) decides. |
| 3 | Clash calibration | **Freeze `s2b-2`** (f = 0.90, the H(N)/H(C) split, the class-Y rule) after archiving the regenerated T4 admissibility report, in Stage 0 and before any S2 energy. | The thresholds filter unrelaxed starts, not energies; `GEOM_SHA` already pins them; a change after any E_b exists would be a forking path (section 6, "Freeze"). The atomic tokens of S2 are not limited by these thresholds on the hosts measured: under `s2b-1` shifted Cl passed at 240/240 starts on m30 and m05, and under `s2b-2` every centred Cs start is kept and m30, m05 and m12 each keep at least one Cs pose at all 19 FA sites [R] (sections 5–6). The archived T4 report re-confirms this for `s2b-2` before the freeze, and the Stage-0 admissibility check covers the 12 drawn hosts and the m05 calibration cells (`S2_PLAN.md` §§3, 11). | — |
| 4 | Primary-source checks (DMA, AA, Pb–Cl) | **Pb–Cl: verify 2.837 Å (Poglitsch & Weber 1987) on the laptop before the shifted Cl starts are built.** If the source gives another distance, the shifted starts use it (dated note before any is built); if no value can be verified, run them at 2.837 Å with `--allow-provisional`, labelled [M] starting points. **DMA, AA: deferred**; check against the CSD when they enter. **No gas-phase DFT.** | The value only seeds a starting geometry, and the 0.42 Å Pb–Cl mismatch of a centred Cl (section 10) makes a lower shifted basin plausible [I], so the starts should not be dropped. A gas-phase optimum is not the in-crystal geometry. | The pose pilot (`S2_PLAN.md` §9) decides whether the shifted Cl minima matter (≤ 10 meV rule). |
| 5 | SCN binding classes | **Deferred.** When SCN enters: keep every feasible class per site and aggregate each leg by Boltzmann weights at 298 K. | Fixing the class from one host assumes that the class preference does not depend on host or site; aggregation needs no such assumption. S:ab exists at only 13.6% of X sites [R]. | When SCN enters: a one-host class-spread pilot. If the DFT spread across feasible classes is ≤ 10 meV at its sites, one class may be used, under a rule written before the pilot. |
| 6 | Poses per site | **One row per (host, dopant, site)**, so `34:131-132` stays unique. Each leg's energy is either the default pose or the per-leg Boltzmann aggregate over geometrically distinct relaxed minima. **No MACE energy selects a pose.** | Per-leg Boltzmann aggregation is the configurational free energy at 298 K. Distinct minima are defined by geometry (> 0.25 Å or 20°). MACE energies are not re-admitted (PLAN amendment m item 4; amendment n item 2); Proposal 3's MACE pre-selection is rejected. | **m30 pose pilot (`S2_PLAN.md` §9):** Cs at FA128 and the farthest FA (FA188), Cl at I138 and I175, both legs, ≤ 40 single points. Default kept if \|E_b(default) − E_b(Boltzmann)\| ≤ 10 meV at both sites; the larger of the two residuals and their difference is then carried as an allowance. Otherwise all starts are used in production (≤ +100 single points per host). |
| 7 | Rb; replace the native Cs? | **Rb outside S2**; kept in the registry, labelled hypothetical. **Never replace the native Cs.** | t(RbPbI₃) = 0.818 / 0.858, below 0.875; Rb is not incorporated into the 3D lattice experimentally (Kubicki et al. 2017 [S]; section 10). Replacing the native Cs changes the host family and breaks pairing with S1. The Rb UPF is downloaded and its `z_valence` (9) recorded for later (`PSEUDOPOTENTIALS_S2.md`). | — |
| 8 | Migrating iodide | **"allow" in binding maps; "forbid" for paths.** | I138 is a first-shell X site on m30 (4.285 Å) [R]; more generally the migrating iodide is one of the 8 first-shell X sites in all 36 members (census of 2026-11-03, `S2_PLAN.md` §4) [R]. Excluding it would bias the first-shell mean. Cells with `replaced_migrating_iodide: true` never reach a path builder (section 3). | — |
| 9 | X-site shells and range | **First shell: the 8 I below the 5.12–5.48 Å gap** (true MIC, unrelaxed host), including the migrating iodide. **Far: the 2 farthest X sites** (all > 9.0 Å). **No range cut**, as in `scripts/29`. No mid shell in S2. | The gap is wide and geometric [R]. 7.28 Å only bounds where rounding MIC is exact; it is not a physical range (section 1). The far rule matches B and A (amendment d). Correction to section 12 question 9 ("up to 12 Å (as in 29)") and to the draft of this answer, which said "range up to 12 Å as in `scripts/29`": `scripts/29` applies no range cut, and the farthest X site lies at 12.33–13.03 Å in every member, so a 12 Å cut would remove it [R, census of 2026-11-03]. | The noise pilot (`S2_PLAN.md` §8) uses the 4 farthest X sites and measures σ_far for Cl; it gates Cl and fixes n. |
| 10 | SCN at first-shell X sites | **Deferred.** When SCN enters: a **constrained pre-relaxation** (SCN held, neighbouring I free) as the first remedy; moving the two Pb and nearest I outward as the second. **No looser Y–I threshold.** | No unrelaxed start avoids SCN···I contacts of 3.18–3.74 Å against 4.045 Å for the shortest host I···I [R]; a looser threshold would admit contacts the host never shows. | When SCN enters: a pilot of the pre-relaxation (validity checks, then the class-spread rule of answer 5). |
| 11 | DMA donors | **Deferred.** When DMA enters: **add a donor-contact pose family** (a short anchor or translation search bringing an N–H within 3.0 Å of an I⁻) beside the inverted starts, and aggregate per leg as in answer 6. | Only 25 of 141 m30 DMA starts have an N–H···I contact, against 677 of 684 host FA [R]. Relying on relaxation to find the contact is the S1 soft-landscape failure (`WP1_PILOT_RESULT.md`). | When DMA enters: a geometric check that reports the fraction of relaxed minima with N–H···I < 3.0 Å, plus the answer-6 pose rule. |
| 12 | Orientation families | **Moot in S2** (no sampled molecular token; GA uses its recipe). For later molecular tokens: the six labels plus `inherit` / `inherit_flip`, with a fixed `n_random` set in that token's amendment. **Fixed-step family sampling only if a pose pilot shows a DFT spread above 10 meV.** | 10 meV (≈ 0.4 k_BT) matches answer 6; Proposal 3's 30 meV exceeds k_BT and would hide relevant spread. | A molecular-token pose pilot when DMA, AA or SCN enter. |
| 13 | SCN bound angle | **Keep the 90° floor and record the angles; no penalty.** Deferred with SCN. | A 106° floor leaves 8 of 59 m30 sites [R]. An angle penalty would be an arbitrary energy weight in a geometry builder. | When SCN enters, the recorded angles are reported beside the class-spread pilot. |

**Effect on the builders.** None of these answers changes `s2b-2` geometry or `GEOM_SHA`. The Stage-0
work is downstream (section 11; `S2_PLAN.md` §17): a new binding-map driver keyed by sublattice that
never passes S2 tokens to `scripts/29`; a refill check over every X species; a graph topology check
replacing `35 sane()` (`S2_PLAN.md` §5); X-unit vacancy detection instead of `count("I") == 59`; the
whole-molecule free region by centre atom (`S2_PLAN.md` §4); a QE writer with the Cl and Ca entries
(S and Rb recorded); and MOMENT entries (Cl 1, Ca 0) for any isolated-atom use.
