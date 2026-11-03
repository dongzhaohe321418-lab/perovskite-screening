# S2 pseudopotentials: Cl, S, Ca and Rb (record of 2026-11-03)

**Status: record, written 2026-11-03 before any single point with these files.** No S2 cell has been
evaluated with them or with any other calculator, and none of them is on the node yet.

Tags as in `S2_PLAN.md`: **[R]** read from the files themselves or from a repository file; **[M]**
modelling choice; **[I]** interpretation.

## 1. Provenance

- **Approval.** The download needed the user's approval (`S2_BUILDERS_DESIGN.md` §11). On 2026-11-03
  the PI delegated the choice of the S2 research direction to the analyst (an AI assistant) and
  approved everything else, including this download (`S2_DECISION.md`, "Who decided").
- **Source.** The pslibrary 1.0.0 `upf_files` directory of the Quantum ESPRESSO pseudopotential
  library, the source of the S1 set (its address is in `ehpc/EHPC_REBUILD_GUIDE.md` §A5).
  Downloaded 2026-11-03.
- **Storage.** The five files and a `SHA256SUMS` list are kept off-repository in the private record
  folder. They are not committed: the S1 UPFs are not in the repository either, and the sha256 below
  identifies each file exactly.
- **Not yet on the node.** They are copied to the node's pseudopotential directory (the `pseudo_dir`
  of `scripts/30`) at the start of campaign 1. The sha256 of every copy is checked on the node against
  the table below before any single point; on a mismatch the campaign stops [M].

## 2. Files and header fields [R]

All five are UPF 2.0.1 files generated with the "atomic" code of A. Dal Corso (author field `ADC`):
ultrasoft (`pseudo_type="USPP"`, `is_ultrasoft="true"`, `is_paw="false"`), scalar-relativistic
(`relativistic="scalar"`, `has_so="false"`), `functional="PBE"`, with nonlinear core correction
(`core_correction="true"`). The fields below were read from each `<PP_HEADER>` and from the
"Suggested minimum cutoff" lines of the file's own info block, and the sha256 was recomputed from the
files on 2026-11-03; it equals the value recorded at download.

| file | element | sha256 | bytes | atomic code, date | z_valence | suggested ecutwfc / ecutrho (Ry) | header wfc_cutoff / rho_cutoff (Ry) | l_local; projectors |
|---|---|---|---|---|---|---|---|---|
| `Cl.pbe-n-rrkjus_psl.1.0.0.UPF` | Cl | `6178e5e4ea26a81a2e8556f65f13c3ba282b75cc3df620746ac20d4a195b0513` | 1 530 948 | v.6.3, 4 Sep 2018 | 7 | 45 / 223 | 45.33 / 223.21 | −1; 6 |
| `S.pbe-n-rrkjus_psl.1.0.0.UPF` | S | `90fb585e830674f2de7b4cbace28d5dd0c05ca1a919d1f92a59b54d6b95cbfc4` | 1 526 090 | v.6.3, 4 Sep 2018 | 6 | 39 / 181 | 39.13 / 180.97 | −1; 6 |
| `S.pbe-nl-rrkjus_psl.1.0.0.UPF` | S | `4717a5314fa0fa53f6ee7542a50e7dfd44824a2f19f727c0f76f2205cae79deb` | 909 146 | v.6.3, 4 Sep 2018 | 6 | 39 / 157 | 39.13 / 156.54 | 2; 4 |
| `Ca.pbe-spn-rrkjus_psl.1.0.0.UPF` | Ca | `60745cd19cb7c96ea734fe68ea89a54603d83eaaca19cb8b37deb3fc41fe9b43` | 1 716 998 | v.6.2.2, 3 May 2018 | 10 | 45 / 274 | 45.05 / 273.93 | −1; 6 |
| `Rb.pbe-spn-rrkjus_psl.1.0.0.UPF` | Rb | `642852a379c2f212a7cd4205bd705cf2195b26f263ee2f14fe9a10dab824fa28` | 1 873 680 | v.6.2.2, 4 May 2018 | 9 | 35 / 259 | 34.59 / 258.72 | −1; 6 |

- **S exists as an `-n-` file.** `S2_BUILDERS_DESIGN.md` §11 expected that S might exist only as
  `-nl-`. Both variants exist and both were downloaded. The `-n-` file follows the repository's
  `-n-`/`spn` pattern and is the one any later S work would use [M]; the `-nl-` file is recorded only.
- **Valences.** z_valence equals the registry value of `S2_BUILDERS_DESIGN.md` §2 for every element
  (Cl 7, S 6, Ca 10, Rb 9), so the valence-electron bookkeeping of the registry holds.
- **Cutoffs.** Every suggested cutoff lies below the S1 fingerprint of 50 / 400 Ry (`scripts/30`;
  the S1 set suggests at most 46 / 326 Ry). The condition of `S2_BUILDERS_DESIGN.md` §11 under
  which standing rule 1 would decide ("If a suggested cutoff exceeds 50/400 Ry") is therefore not met.

## 3. Use in S2

- **Cl and Ca** enter the S2 QE writer beside the S1 set (`S2_PLAN.md` §6). The fingerprint of
  `scripts/30` is otherwise unchanged, and `scripts/30` itself is not edited.
- **S and Rb** are not used in S2: SCN and Rb are deferred (`S2_PLAN.md` §2). Their files are
  recorded here for a later amendment.
- **Planned checks before any decisive use (gate G1, `S2_PLAN.md` §7; campaign 1; not yet run):**
  - **Cutoff.** For one unrelaxed host-leg cell per element on the S2-relaxed m30 host (Cl at I138,
    Ca at Pb136): |Δ[F(doped) − F(host)]| between 50/400 Ry and 60/480 Ry must be ≤ 5 meV.
    60/480 Ry is max(60/480 Ry, the suggested cutoffs), since every suggested cutoff is lower.
  - **Valence.** z_valence of the node copy equals the registry value (checked through the sha256).
  - **Spin.** One doped V_I⁺ cell per element at nspin 2, seeded with about 1 μB on the dopant
    (`starting_magnetization` = 1/z_valence: Cl 1/7, Ca 1/10) and 0.1 on every other species:
    |ΔF| ≤ 3 meV and total magnetisation below 0.1 μB per cell.
  - **Fail.** An element that fails leaves the decisive family of S2. No setting is changed to rescue
    it; a later amendment may schedule it at a new fingerprint.
- **Isolated-atom moments** (only if an isolated-atom energy is ever needed, as in `scripts/31`):
  Cl 1, S 2, Ca 0, Rb 1 (Hund's rules; `S2_BUILDERS_DESIGN.md` §11). S2 needs none.
