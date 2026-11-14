# Implementation specification: S2b evaluation E (blocks 1, 2, 3 and 5; block 4 as an interface)

**Repository and line numbers.**
- The repository is the analyst's checkout of this repository, at HEAD `4d27d2d`.
- `S2/` means `results/objective2/s2/`. Code paths without `S2/` are repository-relative.
- [46:n]-[50:n] are lines of `scripts/46`-`50` at `8bff03e`. They are byte-identical at HEAD: `git diff --stat 8bff03e HEAD -- scripts/46_s2_cells.py ... scripts/50_s2_campaign.py` prints nothing.
- [S2B:n] is a line of `S2/S2B_PLAN.md` at `0e846cc`, which is unchanged at HEAD. P:n is a line of `S2/S2_PLAN.md`.
- Other short names:
  - [fig:n] is `S2/figures/fig_s2_c2_a2.py`;
  - [cd:n] is `S2/c2_diagnostic/check5_diag.py`;
  - [pd:n] is `S2/c2_diagnostic/part_d_read.py`;
  - [g2:n] is `S2/c2_diagnostic/g2_square.py`.
- [wt49:n], [wt50:n] and [wtg:n] (`S2/s2b/guard.py`) are lines of the uncommitted integration tree as read on 2026-11-12. That code is still moving, so every field name taken from it must be re-verified when E is coded.

**Blinding.**
- I listed file names under `S2/c1/raw`, `S2/c1/records`, `S2/c2/raw`, `S2/c2/gates` and `S2/c2/gates_applied`. I opened, grepped and hashed none of them.
- I read the key names of three public C1 files: `c1/regions/m30_A188.json`, `m30_B76.json` and `m30_B136.json`, with their `centres`. I also read the `smoke.json` mapping and the key names of `c1/pairs/m30_Cs188p0.json`.
- No energy was read or computed. No repository file was edited.
- **One check was run.** I parsed a synthetic 3-configuration pw.x output with `scripts/47` from `8bff03e` (`read="full"`), using the project's Python 3.12 environment with `python -B -I` and a temporary file.
  - It loaded none of `CALC_ENGINES` [cd:32]. `ase.calculators.singlepoint` was already loaded by the imports.
  - READS rose by ase +1 and by F, forces and positions +3 each.
  - This settles the [UNVERIFIED] item of map 3, §6.

## 0. Design

- **What E is.** E is one program, `S2/s2b/e_eval.py`, with helper modules beside it. It runs once per evaluation attempt in two phases. Phase 1 computes everything in memory. Phase 2 writes one output file, plus the figure source data, with `O_EXCL`.
- **How E reads data.**
  - It reads every C2, fr, c3b and c4b A2 record, validity record, gate file, `campaign.json` and `state_end.json` only through **EGuarded**, by full dotted leaf paths from closed per-mode lists (§4).
  - It reads C1 records and single points only through **C1Access**, which enforces the Pb136 deferral (§4.4).
  - Every file it opens is logged by **OpenAudit** (§4.5) and hashed against the verified archive (§8, INT-SHA).
- **Code it reuses.** It reuses the `scripts/48` and `scripts/49` functions that S2B:564-569 names, imported read-only from a `git archive` of `8bff03e` (§2). It also reuses the `scripts/47` parsers (`parse_relax`, `parse_sp`, `sp_status`, `end_rule`, `upf_md5_extra`) and the `scripts/46` loader `load_record` from the same extraction.
- **What it never runs.** No entry point of `scripts/48` (evaluate, assemble, cmd_evaluate, main) is run, and no `scripts/49` gate is evaluated.
- **New code** is limited to what S2B:570-578 lists:
  - the table builder, which includes the archive layout, the readers and the census;
  - validity;
  - the labels;
  - the block logic;
  - the C1-C5 composition, which lives in block 4.
- **The blocks.**
  - Blocks 1, 2, 3 and 5 are specified in full here. Block 4 is an interface (§13) that the code must provide, as a stub, at the FR commit.
  - The block-5 trigger is a value that block 4 supplies. With the stub it is always "C4b not run".
- **The c3 lock.**
  - E constructs no path for a campaign outside (`c1`, `c2`, `fr`, `c3b`, `c4b`).
  - It refuses any root that holds an entry named like `c3` (§3).
  - It never imports `scripts/48` `assemble`, which would read c3 [48:992, 1023].

## 1. Files, interpreter and command line

| file | content |
|---|---|
| `S2/s2b/e_eval.py` | CLI; run discipline (§6); imports at `8bff03e` (§2); commits check (§7); header, labels, precision and formatter (§9); blocks 1, 2, 3 and 5 (§§10-12, 14); cross-checks (§15); fallback (§16); output writer |
| `S2/s2b/e_guard.py` | `EGuarded` and its allow-lists (§4.1-4.3); `C1Access` (§4.4); `OpenAudit` (§4.5) |
| `S2/s2b/e_read.py` | `ELayout` (§3); `ReadsAudit` and `read_relaxation` (§5.1-5.2); `sp_full` and `sp_forces` (§5.3); the C1 census and the table builder (§5.4); tar members (§5.5) |
| `S2/s2b/e_block4.py` | the block-4 interface (§13). At the FR commit it is a stub with `BLOCK4_IMPLEMENTED = False`; it is filled in before C3b |
| `S2/s2b/e_selftest.py` | the synthetic archive builder and every case of §18 |
| `S2/figures/fig_s2b_e_fk.py` | the figure (§17) |

- **Where the code is committed.** It is outside `scripts/` (S2B:532). Blocks 1-3 and 5, the block-4 stub, the self-test and the figure are committed with passing self-tests and a review. That commit must be in the tree of the fr campaign commit, i.e. before the node checkout is updated (S2B §9 step 3). Otherwise §7 asks for an amendment.
- **Interpreter.**
  - Use the project's Python 3.12.14 interpreter with `-B -I`.
  - E asserts `sys.version_info >= (3, 12)` and `hasattr(tarfile, "data_filter")`.
  - It prints the Python, numpy, scipy and ase versions.
  - `/usr/bin/python3` 3.9.6 lacks both `data_filter` and ase (map 1 §B4).
- **Command line.**
  ```
  e_eval.py --self-test
  e_eval.py --run [--root S2] [--private-root DIR] [--stop-note NOTE]
                  [--rerun-cause CASE --amendment NOTE] [--item7-amendment NOTE]
  e_eval.py --hinge --hinge-cause {prereg,backstop} [--prereg NOTE] [--root S2] [--private-root DIR]
  ```
  - `--root` defaults to `results/objective2/s2`, which holds the public c1, c2 and fr archives.
  - `--private-root` holds only `c3b/` and `c4b/`. It is needed only on routes past FR, and only with block 4.
  - Every NOTE is a repository-relative path.

## 2. Imports at `8bff03e` (S2B:564-569)

**Procedure.** `import_8bff03e(repo) -> (m48, g49, q47, c46, tmp)`:
1. Run `git -C <repo> archive -o <tmp>/x.tar 8bff03e scripts results/objective2/dopant_shell/wp2c/wp2cde_dft.json results/objective2/dopant_shell/wp1_production/shell_m30.json results/objective2/dopant_shell/wp1_production/shell_m05.json results/objective2/dopant_shell/wp1_production/v2prod_structures.tar.gz`. `<tmp>` comes from `tempfile.mkdtemp(prefix="e_8bff03e_")`.
2. Extract with `tarfile.extractall(<tmp>, filter="data")`, then `chmod -R a-w <tmp>`.
3. Load `m48 = spec_from_file_location("e_a48_8bff03e", <tmp>/scripts/48_s2_analysis.py)`. Then:
   - `g49 = m48.g49`;
   - `q47 = g49.dep("q47")`;
   - `c46 = g49.dep("c46")`.
4. **Assertions.** Each failure is INT-IMPORT.
   - Every extracted file's bytes have the sha256 of `git cat-file blob 8bff03e:<path>`. The pinned blob ids are 48 `4cbd82f5…`, 49 `e074d8a2…`, 46 `92fbaab6…`, 47 `84c8e8ee…` and 50 `8c04d65f…` (map 1 §A).
   - `os.path.dirname(g49.__file__)`, and the same for `q47` and `c46`, equals `<tmp>/scripts`.
   - `m48.ROOT == <tmp>`.
   - `g49.dep("q47") is q47`. This gives exactly one READS counter; no other 47 instance is created (§5.2).
   - No E module calls `fig.modules()` or `check5_diag.load_c46/load_fig`.
5. Delete `<tmp>` at exit, after the final audit.

**Used from the extraction (closed list).**
- From 48: `leg_F`, `quartet_a1`, `host_values`, `pooled_delta`, `tier_a1`, `tier_cal`, `classify`, `heterogeneity`, `cal_heterogeneity`, `c2_noise`, `dopant_specific`, `required_hosts`, `path_work`, `_mace_eb`, `_mace_pilot`, `_determinism` and `_wp2c_values`.
- From 49: `separability`, `t_ppf`, `sign_required`, `boltzmann_meV` and `g1_pass`.
- The tier functions of 48 and the 49 functions other than `t_ppf` and `boltzmann_meV` are called only by block 4.
- From 47 (OP-26): `parse_relax`, `parse_sp`, `sp_status`, `end_rule`, `upf_md5_extra`, `_header`, `_segment` and `_read_forces`. The last three are used only by the force-only SP reader, as in [fig:164-187].
- From 46 (S2B:579): `load_record` and `write_cell`. `write_cell` is used only in the self-test.

**Restated, not imported (OP-26).** E restates as literals the label grammar, `FAR4_TABLE`, `CAL_SITES`, `POSE_SITES`, `K3_QUARTETS`, `STEP0_PAIRS`, `END_ACCEPTED`, k_BT = 25.7, Q_STAR = 0.99375, Q_RANK = 0.9975 and Q_SITE = 0.975.
- It asserts at load that each literal equals the 8bff03e object (INT-IMPORT). The objects are `g49.lab_host`/`lab_v`/`lab_dop` on every label E builds, `c46.FAR4_TABLE`, `c46.CAL_SITES`, `c46.POSE_SITES`, `g49.K3_QUARTETS`, `g49.STEP0_PAIRS` and `g49.RULES[...]`.
- Its own code calls none of those helpers.

**Data paths of 48.**
- `_wp2c_values()` reads `<tmp>/results/objective2/dopant_shell/wp2c/wp2cde_dft.json`. E asserts that the file exists before the call, because absence returns None silently [48:1250-1252].
- `_determinism(hosts, cdir, wp1_dir=<tmp>/results/objective2/dopant_shell/wp1_production)` is called with an explicit `wp1_dir`, and E asserts that the three wp1 files exist. Its silent `except (OSError, KeyError, IndexError, tarfile.TarError)` [48:1221] is guarded: if `max_dr_A` or `E_WP1_eV` comes back None for a pilot, E reports cross-check XC-DETERMINISM failed.

## 3. Roots, layout and the c3 lock

**`ELayout(root, private_root=None)`.**
- **Campaigns.** `CAMPAIGNS = ("c1", "c2", "fr", "c3b", "c4b")`. The public ones (c1, c2, fr) sit under `root` and the private ones (c3b, c4b) under `private_root`. `cdir(c)` raises `EError` for any other name; in particular, no `c3` path can be built.
- **Methods.** The paths mirror the archive layout of 46 [46:1564-1646] and the archiver [50:4240-4337]:
  - `record(c, wid)` → `<c>/records/<wid>.json` (c1, c3b);
  - `raw(c, name)` → `<c>/raw/<name>`;
  - `a2_record(c, lab)` → `<c>/raw/<lab>.a2.json`;
  - `a2_parts(c, lab)` → the sorted `<c>/raw/<lab>.p<n>.out.gz` matching `^<lab>\.p([1-9]\d*)\.out\.gz$`. The numbers must be exactly 1..N; otherwise INT-PARTS;
  - `structures(c)` → `<c>/structures.tar.gz`;
  - `region(member, L, j)`, `pair(member, T, j, n)` and `distinct(member, T, j, leg)` (c1 only);
  - `gate(c, name)` → `<c>/gates/<name>.json`;
  - `applied(c, gid, suffix)` for `suffix ∈ (".json", ".gate.json")`, where `gid` has `[^A-Za-z0-9_.-]` replaced by `_`. No `.inputs.json` path can be built;
  - `campaign(c)`, `state_end(c)`, `smoke()` (`c1/smoke.json`), `upf_check()` (`c1/upf_check.json`) and `throughput()` (`c1/throughput.json`).
- **Why not 46's Layout.** 46's `Layout` is not used. At `8bff03e` it refuses fr, c3b and c4b [46:1574-1577].

**The c3 lock** (S2B:569; 11a part b, point 2).
- `assert_no_c3(dir)`, for `root` and for `private_root` if given, refuses (exit 2) when either holds:
  - an entry of `os.listdir(dir)` matches `re.fullmatch(r"c3([._-].*)?", name, re.I)`. So `c3`, `C3`, `c3.tar.gz` and `c3_notrun` are refused, and `c3b` is not;
  - `os.path.lexists(join(dir, "c3"))` holds. This also covers a dangling symlink.
- It runs before any read, and again at exit as INT-ROOT.
- OpenAudit also refuses any opened path with a segment matching that pattern.
- Self-test D3 covers this.

## 4. The E guard

### 4.1 `EGuarded(fig.Guarded)` (S2B:540-545)

- **Base.** `fig` is `S2/figures/fig_s2_c2_a2.py` at HEAD, loaded unchanged with `spec_from_file_location`. Only `fig.Guarded`, `fig.Blinded` and `fig.WITHHELD` are used.
- **Construction.** `__slots__ = ("_mode", "_kind")`. E constructs objects only through `eg_load(L, c, relpath, *, mode, kind)`, which:
  - refuses unless `(mode, kind)` is in `TABLE` and `relpath` is one of that kind's explicit files (no globs);
  - refuses any `*.inputs.json` path;
  - reads the bytes once through OpenAudit and calls `json.loads`;
  - returns `EGuarded(d, relpath, mode=mode, kind=kind)`.
- **`get(path)`.** It takes a full dotted path only.
  - It refuses (`Blinded`) unless `path in TABLE[mode][kind]["get"]`.
  - It walks `self._d` directly, without `Guarded.get`, which would refuse the `Eb_A2_meV` segment.
  - If a segment is missing it returns the sentinel `ABSENT`, which is unprintable (its `__repr__` refuses).
  - A dict, or a list holding a dict, is refused as a parent.
  - It returns only `None`, `bool`, `int`, `float`, `str`, or a deep-copied list of `str`, `int` or `bool`.
- **`is_none(path)`.** It is allowed only for the paths in `TABLE[mode][kind]["is_none"]`, and returns `x is None` as a bool. An `ABSENT` leaf there is INT-STRUCT.
- **Refused** (each through `_refuse`):
  - `has`, `open` and `_wrap`;
  - every dunder that `fig.Guarded` refuses (`__iter__`, `__repr__`, `__str__`, `__eq__`, `__len__`, `__contains__`, `keys`, `items`, `values`);
  - additionally `__reduce_ex__`, `__reduce__`, `__copy__` and `__deepcopy__`, so that `copy.copy`, `copy.deepcopy` and pickle are refused.
  - `__hash__ = None`, and `__bool__` returns True.
- **A discipline rule.** No E source file other than `e_guard.py` contains `._d`. The self-test asserts this by scanning the source.

### 4.2 Allow-lists

Bold entries are additions proposed in §19. They are coded as `PROPOSED`, and each is removed, with its stated fallback, unless the dated amendment named there is committed before E's code.

**FAR mode** (every run, including the hinge run; S2B:546-552):

| kind | files (relative to the root) | `get` | `is_none` |
|---|---|---|---|
| `k3` | `c2/gates/K3.json`, `c2/gates_applied/gate_K3.gate.json` | `decision.K3`, `result.checks_failed`, `result.Eb_A2_meV.far` | `result.value_meV` |
| `k3_marker` | `c2/gates_applied/gate_K3.json` | **`decision.K3`** (the plan says `decision`; OP-5), `gate_file_sha256` | — |
| `a2_far` | `c2/raw/s2r_m30_{hostB76,VB76,Sr76o0_novac,Sr76o0_vac}.a2.json` | `n_config`, `converged_at_k`, `k_last`, `final_geometry.k`, `final_geometry.sha256`, `restarts`, `reruns_from_zero`, `status`, `end_rule.outcome`, **`layout.ranks`** (OP-3), **`validity_final.valid`, `validity_final.failed`** (OP-4) | — |
| `a2_hinge_counts` | `c2/raw/s2r_m30_{VB136,hostB136,Sr136o0_novac,Sr136o0_vac}.a2.json` | `n_config`, `end_rule.outcome` | — |
| `campaign_c2` | **`c2/campaign.json`** (OP-25) | `commit`, `status` | — |

**FR mode** (every run; S2B:555-557):

| kind | files | `get` |
|---|---|---|
| `a2_fr` | `fr/raw/<lab>.a2.json`, for `lab` in FR_ORDER (§9) | the `a2_far` leaves, **`layout.ranks`**, **`validity_final.{valid, failed, check5_reading, valid_as_written, failed_as_written, invariant_only}`** (OP-4) |
| `fr_gate` | `fr/gates/FR.json`, `fr/gates_applied/gate_FR.gate.json` | `decision.FR.{outcome, FR1, FR2, part, cell, kind}` (OP-6; `FR_DECISION_KEYS` [wt50:704]); `result.checks_failed`, `result.end_rule_failed`, `result.cells_not_run`; `result.FR2.Eb_A1_meV`, `result.FR2.Eb_A2_meV` (OP-7), `result.FR2.delta_far_meV`; **`result.invariant_only`** (OP-8) |
| `fr_marker` | `fr/gates_applied/gate_FR.json` | `decision.FR.{outcome, FR1, FR2, part, cell, kind}`, `gate_file_sha256` |
| `fr_step0_gate` | `fr/gates/fr_step0.json`, `fr/gates_applied/gate_fr_step0_2.gate.json`, `fr/gates_applied/gate_fr_step0_4.gate.json` | `decision.fr_step0.{attempts, outcome, repeat, fix_note, cell, no_error_found, note}`, `decision.fr_step0.attempt1.{attempts, outcome, cell}` (`FR_STEP0_KEYS` [wt50:705]); **`result.cells.s2_m30_VA188.{dF_meV, passed}`, `result.cells.s2_m30_Cs188o0_vac.{dF_meV, passed}`** (OP-9) |
| `fr_step0_marker` | `fr/gates_applied/gate_fr_step0_2.json`, `fr/gates_applied/gate_fr_step0_4.json` | the `decision.fr_step0` leaves above, `gate_file_sha256` |
| `campaign_fr` | **`fr/campaign.json`** (OP-25) | `status`, `commit`, `start_commit`, `fr_outcome`, `stop_reason` |
| `state_fr` | **`fr/state_end.json`** (OP-25; present only at CAMPAIGN_DONE) | `commit`, `campaigns.fr`, `campaign_commit.fr`, `fr_step0.{attempts, outcome, cell}`, `FR.{outcome, FR1, FR2, part, cell, kind}`, `fr_stop.{at, kind}` |

**HINGE mode** (block 5 and the hinge run only; S2B:560). It adds:

| kind | files | `get` |
|---|---|---|
| `k3` | as in far mode | adds `result.Eb_A2_meV.hinge` |
| `a2_hinge` | the four `c2/raw/s2r_m30_{VB136,…}.a2.json` | the `a2_far` leaves, with the bold additions; this replaces `a2_hinge_counts` |
| `step0_c2` | **`c2/gates/step0.json`, `c2/gates_applied/gate_step0_1.gate.json`, `gate_step0_4.gate.json`** (OP-9) | `decision.step0.outcome`, `result.cells.s2_m30_VB136.{dF_meV, passed}`, `result.cells.s2_m30_Sr136o0_vac.{dF_meV, passed}` |

**TIER and C4B modes** (block 4). They are an interface only (§13): the c3b and c4b kinds, with the same record leaves plus validity leaves, and the c4b gate leaves. Their field names are fixed with the c3b and c4b code.

**Files E never opens:**
- every `*.inputs.json`, including `c2/gates_applied/gate_K3.inputs.json` (S2B:545);
- `*.validity_final.json`;
- the C2 `K2`, `projection` and `step0` gate files, outside hinge mode;
- anything under `step0_attempt1/` or `discarded/`;
- `HARD_CAP.json`, `ledger.json`, `graph.json`, `completeness.json`, `runner_reads.json` and `logs/`.

### 4.3 Static rules

These are asserted at import (INT-GUARD) and in self-test A5.

- **R1.** No path has a segment in `{"state_in", "inputs_in", "c1_in", "inputs_opened", "opened", "inputs_digest"}`.
- **R2.** No path has the segment `dF_200_180_meV`.
- **R3.** No path's last segment is in `fig.WITHHELD`, except the single pair `("fr", "fr_gate", "result.FR2.Eb_A2_meV")` (OP-7). `value_meV` appears only in an `is_none` list.
- **R4.** Mode-specific paths:
  - `result.Eb_A2_meV.far` appears only in far mode;
  - `result.Eb_A2_meV.hinge` only in hinge mode;
  - `result.FR2.*` and the fr step-0 `dF_meV` only in fr mode;
  - the C2 step-0 `dF_meV` only in hinge mode.
- **R5.** `Eb_A2_meV` is a non-final segment only in the `k3` kind.
- **R6.** Every file list is explicit and holds no `*.inputs.json`.

### 4.4 The C1 side: `C1Access` (S2B:561-563, 579)

**Constants.** E asserts each against its classifier at load (INT-C1-CENSUS) and against the audit log at exit (INT-PB136-REC, INT-PB136-RAW):
- `PB136_WIDS = ("s2_m30_VB136", "s2_m30_Sr136p0_novac", "s2_m30_Sr136p0_vac", "s2_m30_Ca136p0_novac", "s2_m30_Ca136p0_vac")`.
- `PB136_SP = ("s2_m30_VB136", "s2_m30_Sr136o0_vac", "s2_m30_VB136_q0", "s2_m30_Sr136o0_vac_q0", "s2_m30_Ca136o0_vac_q0")`.
- `NEVER_SP`: the five G1 labels and the two spin labels. These are `s2g1_m30_host_e60`, `s2g1_m30_Cl138o0_novac_e50`/`_e60`, `s2g1_m30_Ca136o0_novac_e50`/`_e60`, `s2spin_m30_Cl175o0_vac` and `s2spin_m30_Ca76o0_vac`.
  - E opens none of them in any mode (OP-2). They are not A1 cells of §6 settings, and their values are G1 gate values, already public.
- **The single-point sets:**
  - `NOISE_SP` (106): per pilot, the host, the 12 far4 V⁺ cells and the 40 far4 dopant legs.
  - `POSE_SP` (4): `s2_m30_Cs128o0_novac`/`_vac` and `s2_m30_Cl138o0_novac`/`_vac`.
  - `Q0_SP` (7): `s2_m30_VB76_q0`, `s2_m30_Sr76o0_vac_q0`, `s2_m30_VX138_q0`, `s2_m30_Cl138o0_vac_q0`, `s2_m30_VA128_q0`, `s2_m30_Cs128o0_vac_q0` and `s2_m30_GA128o0_vac_q0`.
- **Census.** `NOISE_SP ∪ POSE_SP ∪ Q0_SP ∪ PB136_SP ∪ NEVER_SP` must equal the 129 label stems of `c1/raw/*.out.gz`, which are listed by name only. These names were checked on 2026-11-12.

**`C1Access(L, c46, q47, audit, reads, *, hinge)`** has these methods:
- **`record(wid, *, blind, block)`.**
  - It returns `c46.load_record(L.record("c1", wid), blind=blind)`.
  - `blind=False` is refused unless `block in (3, 4, 5)`.
  - For a wid in `PB136_WIDS` it is refused unless `hinge and block == 5`.
  - `blind=True` is always allowed. Block 3 uses it for the validity of the Pb136 cells in the invalid-cell table.
- **`sp_full(label, *, block)`.** It runs `q47.sp_status(L.raw("c1", ""), label)`. If the status is complete, it then runs `q47.parse_sp(<raw>/<label>.out.gz, read="full", free=<free of the label's base record>)`.
  - The base record of a `_q0` label is the record of the label without `_q0`. This departs from [48:1076], where q = 0 rows get no free set.
  - Allowed labels: in blocks 1-3, `NOISE_SP ∪ POSE_SP ∪ Q0_SP`; in block 5 in hinge mode, also `PB136_SP`.
  - Results are cached per label, so READS rises once per label.
- **`sp_forces(label, *, block)`.** The force-only reader (§5.3). It is allowed for `PB136_SP` in block 3 only if OP-1 is adopted (`PB136_FORCES_IN_BLOCK3 = True`). In every other case it is used only for the cross-check XC-FORCES on the non-Pb136 labels.
- **`assert_closed()`.** At load it checks the constants against the classifier and the census. At exit it checks that the audit log holds no Pb136 record loaded `blind=False` and no Pb136 `c1/raw` path, except under the flags above.

**The classifier `classify_wid(wid)`.** It follows map 2 §2b: `WORK_RE` [46:626-627], with first-definition precedence as in `graph_c1` [50:1076-1116].
- **Pb136** holds when the member is m30 and either the cell is V with L = B and j = 136, or the token is Sr or Ca with j = 136.
- **Otherwise:**
  - `host`;
  - `V`;
  - `pose_start` (D or DV with n ≥ 1);
  - `noise` (D or DV, n = 0, j in `FAR4[h][L]`);
  - `startset` (D or DV, n = 0, j = `CAL[h][L]`).
- **Expected counts** (INT-C1-CENSUS): host 2, V 29, noise 80, startset 16, pose_start 28 (block 3: 155), and Pb136 5. The total is 160 = `len(os.listdir(c1/records))`.

### 4.5 `OpenAudit`

- **What it hooks.** At start it wraps `builtins.open` (which also covers `io.open` and `gzip.open`, since `GzipFile` calls `builtins.open`) and `tarfile.bltn_open`. That covers `json.load(open(…))`, `scripts/32 read_text` and `tarfile.open`.
- **What it logs.** For each open of a path under a root or under `<tmp>`, it records `realpath`, the mode and the current block.
- **What it refuses**, raising before the real open:
  - any write mode under a root;
  - `*.inputs.json`;
  - a segment matching the c3 pattern;
  - `step0_attempt1/` and `discarded/`;
  - `c2/raw/s2r_m30_{VB136,hostB136,Sr136o0_novac,Sr136o0_vac}.*` outside hinge mode, except `.a2.json` read through `a2_hinge_counts`;
  - `c1/raw/<PB136_SP or NEVER_SP>.*` outside hinge mode, except the OP-1 force-only flag;
  - in `--self-test` mode, every real path under `S2/c1/records`, `S2/c1/raw`, `S2/c1/gates`, `S2/c1/gates_applied`, `S2/c1/structures.tar.gz`, `S2/c2`, `S2/fr`, `S2/c3b`, `S2/c4b` and the given private root.
- **At exit.** E re-reads every logged file with the original `open` and compares its sha256 with the one taken at first open (INT-SHA-STABLE), and then with the verified-archive reference (INT-SHA, §8).

## 5. Readers

### 5.1 `read_relaxation(ctx, c, lab, *, mode, kind) -> dict` (S2B:535-539)

1. **Read the record leaves.** Through `eg_load(L, c, f"raw/{lab}.a2.json", mode=mode, kind=kind)`, read `status`, `n_config`, `converged_at_k`, `k_last`, `final_geometry.k`, `final_geometry.sha256`, `restarts`, `reruns_from_zero`, `end_rule.outcome`, `layout.ranks` and the validity leaves.
2. **Only complete relaxations are parsed.** If `status != "complete"`, return `{"label", "status", "parsed": False}`; no part is opened (N-F40, [48:1113-1115]).
3. **Parse.** Take `parts = L.a2_parts(c, lab)` (INT-PARTS) and call:
   ```python
   rel = ctx.reads.parse_relax(lab, parts, read="full", k_cap=200, mapping=ctx.mapping,
                               ranks=<layout.ranks>, md5_extra=ctx.md5_extra, label=lab)
   ```
   - `mapping` is `json.load(c1/smoke.json)["mapping"]`.
   - `md5_extra` is `q47.upf_md5_extra(json.load(c1/upf_check.json))`.
   - `n_el` is not passed, because no A2 meta is archived (map 2 §1). This is OP-31.
4. **Integrity** (§8):
   - INT-PARSE: `rel["usable"] is True` and `rel["ks"] == list(range(rel["n_config"]))`.
   - INT-NCFG: `rel["n_config"] == record n_config`.
   - INT-KLAST, by outcome (OP-14):
     - accepted_converged: `rel.k_last == rel.converged_at_k == record.converged_at_k == record.k_last`;
     - accepted_plateau and unconverged_cap: `rel.k_last == 200 == record.k_last` and `rel.cap_reached`;
     - unconverged_early: `rel.k_last == record.k_last`.
   - INT-FINALK: `final_geometry.k == rel.k_last`.
   - INT-FINALSHA: the sha256 of the member bytes `a2/<lab>/<lab>.final.extxyz` of `L.structures(c)` equals `final_geometry.sha256`.
   - INT-FINALPOS: the member, read with `ase.io.read(StringIO, format="extxyz")` with `calc = None` and constraints cleared (as [pd:68-73]), has the same symbols as `rel["symbols"]`, and `max |positions_A[k_last] − positions| ≤ 1e-6 Å`. There is no minimum image, as in [pd:166-170].
   - INT-CELL: the member's cell equals the cell of the A1 start member `c1/structures.tar.gz:cells/<a1>/start.extxyz` to 1e-9 Å. Here `<a1>` is the label's A1 start work id (`s2_m30_host` for host_R, `s2_<h>_V<L><j>` for V⁺, `s2_<h>_<T><j>p0_<leg>` for D and D+V⁺), as [49:379-386].
5. **Cross-checks** (§15):
   - XC-ENDRULE: `q47.end_rule(rel)["outcome"] == end_rule.outcome`.
   - XC-PARTS: `len(parts) == restarts + 1`.
   - XC-C2R: for C2 only, the `C2_RESULT` constants (§10).
6. **Derived values.**
   - `F = rel["F_eV"]` (eV, by k).
   - `F0 = F[0]`, `Ffin = F[k_last]`, and `relax_meV = (Ffin − F0) × 1000`.
   - `curve_meV[k] = (F[k] − Ffin) × 1000` for every k.
   - `restart_k = [p["k_first"] for p in rel["parts"][1:] if p["n_config"]]`.
   - `tail = {kt: (F[kt] − Ffin) × 1000}` for the window ks of the label.
   - `pw = m48.path_work(rel, image_centres(centres, cell))`, where:
     - `centres = [region["centres"]["v"], region["centres"]["site"]]` of `c1/regions/<pilot>_<L><site>.json`;
     - the pilot, L and site come from E's restated `a2_cell` grammar;
     - `cell` is the final member's cell;
     - `image_centres` returns `c + n·A` for n ∈ {−2,…,2}³ (OP-15).
   - XC-MIC: for every atom, the image-centre distance from `positions_A[0]` equals `min_c |cd.mic(x − c, cell)|` to 1e-9 Å.
7. **Memory.** E keeps only `F`, `positions_A[0]`, `positions_A[k_last]`, `symbols`, `pw`, `restart_k` and the part counts, and drops `rel` before the next relaxation. E parses one relaxation at a time.

### 5.2 `ReadsAudit` (S2B:612-614)

- **Around each `parse_relax` call.** It snapshots `before = Counter(q47.READS)`, calls, and takes the delta.
  - The delta must equal `{ase: n_kept_parts, F: n, forces: n, positions: n}`, where `n_kept_parts = sum(1 for p in rel["parts"] if p["n_config"] > 0)` and `n = rel["n_config"]`. This holds because `restart_repeats_last` is False; E asserts that.
  - Every other key must have a delta of 0 (INT-READS).
- **Around each `parse_sp` full call.** The delta must be `{F: 1, TS: 1, forces: 1, fermi: 1, mag_total: 1, mag_abs: 1}`.
- **Around the force-only reader.** The delta must be `{forces: 1}`.
- **Between calls**, READS is unchanged. Before each call E compares it with the previous `after`.
- **A per-label log** records which labels had F read. At exit E checks two things:
  - the A2 labels are a subset of the A2 labels of the blocks run (far 5-8; the complete FR cells; c4b in block 4; 1-4 only if block 5 was opened);
  - the SP labels are a subset of the SP set of the blocks run.
- The audit uses the real key names (`mag_total`, `mag_abs`), not the `"mag"` key of [pd:322] and [g2:244].

### 5.3 Single points

- **`sp_full`.** See §4.4. The output keeps `F_eV`, `forces` (`{all: {rms_eVA, max_eVA, n}, free: {rms_eVA, max_eVA, n, indices, norms_eVA}}` [47:1228-1235]), `scf_converged` and `status`.
- **`sp_forces(label)`**, the force-only reader (OP-1).
  - It reads `txt = q47.a32.read_text(path)`, then `hdr = q47._header(txt)`, then `cfg, _ = q47._segment(txt, hdr["nat"])`.
  - It requires `len(cfg) == 1`. It then computes `f = q47._read_forces(txt, *cfg[0]["forces"]) × q47.RY_EV / q47.BOHR_A` and the norms and summaries as [47:1228-1235]. The '!' value is never captured, because `RX["bang"]` captures nothing [47:829].
  - XC-FORCES: on every non-Pb136 SP, the reader's result equals `parse_sp`'s `forces` to 1e-12 eV/Å. Both use RY_EV = 13.605693122994 and BOHR_A = 0.529177210903 (`scripts/32` uses the same [32:24-25]).

### 5.4 C1 table builder

- **Records.**
  - For every wid in the census, E loads `blind=True`, which gives the validity, labels, free set, member, kind, site, token, leg and start.
  - For the 155 block-3 records, and in hinge mode for the five Pb136 records, it also loads `blind=False` with `block=3` (or 5) and collects every `E_mace_eV` leaf at any depth as `(json_path, value)`. E walks the record itself and does not take the leaves by label: the 28 pose-start records have `labels: []` (map 2 §2a).
- **Pilot host tables `H[p]`.** These have the s2-evaltable-1 host shape [48:1015-1016], so that the 48 functions apply:
  - `host_valid` from the host record;
  - `cell_valid`, `failed_checks` and `E_mace` keyed by the records' `labels`;
  - `F` and `forces` from `sp_full`;
  - `pair_rejected` from `c1/pairs/*p<n>.json` with `status == "rejected"`;
  - `pose = {"Cs": {"mode": "default", "start_failed": {}}, "Cl": {...}}`. This avoids the multi-pose trap of [48:177-183] (map 1 §D.1);
  - `pose_pilot` (m30) from the `map` keys of the eight `c1/pairs/m30_{Cs128,Cs188,Cl138,Cl175}_{novac,vac}.distinct.json`, sorted by o-index [48:1060-1062].
- **Outside hinge mode.**
  - `H["m30"]` holds no label of a Pb136 cell in `F`, `E_mace`, `cell_valid` or `failed_checks`.
  - `a2_sites = {"m30": {"A": 128, "X": 138}, "m05": {"B": 124, "A": 28, "X": 49}}`. The m30 `B` key is omitted, so `_mace_pilot` skips B136 [48:778-780].
  - `a2 = {}` unless block 4 supplies C4b cells.
- **In hinge mode.** `a2_sites["m30"]["B"] = 136`, the Pb136 labels are added, and `a2["m30"]` holds the four hinge cells with `F0_eV`, `Ffin_eV` and the validity leaves.
- **C1 gate files** (public; plain JSON): `c1/gates/N.json`, `c1/gates/pose.json`, `c1/gates/G1.json`, `c1/gates/throughput.json` and `c1/throughput.json`. Only the leaves named in §12 are used.

### 5.5 Tar members

`member_bytes(tar_path, name)` uses `tarfile.open(...).extractfile(getmember(name)).read()`. It never calls `extractall`. Every member read is logged as `(tar realpath, member name)`.

## 6. When E may run, and the run discipline

### 6.1 Routes (S2B:515-518, 149-156)

`route(ctx) -> {"id", "fr_part", "blocks", "reason"}` reads only `campaign_fr`, `state_fr`, `fr_gate`, `fr_step0_gate` and, past FR, block 4's `tier_route`.

| id | condition | blocks |
|---|---|---|
| `FR-FAIL` | `fr/campaign.json` `status == "done"`, `fr_outcome ∈ {"fail (FR-1)", "fail (FR-2)", "fail (step-0 final; gate not evaluated)"}` [wt50:2452-2476] | 1, 2, 3; 4 not printed; 5 not opened |
| `FR-STOP` | `status == "stopped"`, no `fr/state_end.json`, and `--stop-note` names a committed, clean, dated note under `S2/` that states the fr STOP is final (OP-19) | 1, 2, 3 |
| `C3B-STOP`, `C3B-NOTIER`, `C4B-NOTRUN`, `C4B-STOP`, `C4B-ENDED` | `fr_outcome == "pass"`, then `e_block4.tier_route(ctx)` (§13) | per §13; refused while `BLOCK4_IMPLEMENTED` is False |

- **Refusals** (exit 2, nothing written):
  - `fr/campaign.json` is absent ("fr has not run: none of S2B §7 'When E may run' holds");
  - the status is `running`;
  - the status is `stopped` without a valid `--stop-note`;
  - FR passed while block 4 is a stub.
- **INT-ROUTE** checks the consistency of the outcome with the decisions:
  - `fail (FR-1)` needs `decision.FR.{outcome: "fail", part: "FR-1", FR1: False}` in both FR files and the state;
  - `fail (FR-2)` needs `{outcome: "fail", part: "FR-2", FR1: True, FR2: False}`;
  - `fail (step-0 final…)` needs `fr/gates/FR.json` absent and `state_fr` `fr_step0.outcome == "fail_final"`;
  - `pass` needs `{outcome: "pass", FR1: True, FR2: True, part: None}`.
- **Verified archive** (S2B:522; OP-18).
  - For c2, E requires the committed `S2/c2_verify/verify_c2.txt`.
  - For fr, it requires `VERIFY_RECORD["fr"] = "results/objective2/s2/fr_verify/verify_fr.txt"`, with the path to be fixed by the fr operations note.
  - Each must exist, be tracked and clean. E prints its sha256 and its last line. E does not judge accepted differences; the campaign note does.

### 6.2 Run discipline (S2B:520-529)

**Phase 0 (refusals: exit 2; nothing is written):**
1. `git status --porcelain --untracked-files=all` must be empty for the whole repository.
2. Resolve HEAD.
3. Compute the sha256 of the tools: the `E_FILES` of §1, plus `S2/figures/fig_s2_c2_a2.py` and `S2/c2_diagnostic/check5_diag.py`.
4. Run the imports of §2.
5. Choose the attempt file:
   - `S2/s2b/E_output.txt` absent: attempt 1;
   - present with `E_output_attempt2.txt` absent: attempt 2, only under §16;
   - both present: refused, except the item-7 route of §16 (OP-21);
   - in hinge mode: `S2/s2b/E_hinge_output.txt` (§14.3).
6. Run `assert_no_c3` on every root.
7. Determine the route (§6.1).
8. Run the commits check (§7).

**Phase 1 (in memory).** The order is:
1. integrity prechecks: INT-IMPORT, INT-GUARD, INT-C1-CENSUS and INT-CALC-LOAD;
2. the C1 reads (block 3 data, which block 2's step-0 row also uses);
3. block 1;
4. block 2;
5. block 3;
6. block 4, if the route has it;
7. the block-5 trigger, then block 5;
8. the exit audit: INT-SHA, INT-SHA-STABLE, INT-READS (totals), INT-PB136-*, INT-HINGE-CLOSED, INT-CALC-EXIT and INT-ROOT;
9. assembly of the text and the CSV rows.

- **Integrity failures.** Any failed INT check, or any Python exception, ends phase 1 with a failure report. The report holds the check id, the key paths and the file names. For an exception it holds the stage name and the exception type, never the message, as [g2:375-378].
- **Cross-check failures** do not end phase 1 (S2B:739).

**Phase 2.** E writes the attempt file through `os.open(path, O_WRONLY | O_CREAT | O_EXCL)` and an fsync, and prints the same text to stdout. If the run completed (exit 0 or 1), it also writes `S2/figures/source_data/fig_s2b_e_fk<suffix>.csv` and `…_meta.csv` with `O_EXCL`. The suffix is `""`, `_attempt2`, `_attempt3` or `_hinge`.

**Exit codes.** The last line of every written file is `E exit code: <n>`, and the process exits with n.

| n | meaning |
|---|---|
| 0 | complete: every integrity check passed and every cross-check passed |
| 1 | complete; at least one line reads "cross-check failed" |
| 2 | refused in phase 0; nothing was written |
| 3 | failure before output: the failure report only (attempt 1), or the failure report and the item-7 fallback (attempt 2) |

**Operational notes, not code.**
- Each attempt file is committed unedited before the adversarial check (S2B:525-526).
- On routes with private c3b or c4b data, the file and its CSV are committed only to the private record, and the commit is not pushed until the S2b result note (OP-24).

## 7. The commits check (S2B:615-617)

- **The C2 campaign commit.** `C2_COMMIT = "8bff03ede8b9d0f380b6ef373b239e7deb87817f"`. E asserts it equals `campaign_c2` `commit` (INT-COMMITS). C2 has no `commit_history` (`C2_RESULT.md` §1).
- **The S2b campaign commits.** E records:
  - `fr/campaign.json` `start_commit` and `commit`;
  - `state_fr` `campaign_commit.fr`, which must equal `commit` when present;
  - from block 4, the c3b and c4b `commit`.
  - `S2B_LAST` is the commit of the last S2b campaign that ran (OP-20).
- **What E prints:**
  - `git diff --stat <C2_COMMIT> <S2B_LAST> -- scripts/46_s2_cells.py scripts/47_s2_qe.py scripts/48_s2_analysis.py scripts/49_s2_gates.py scripts/50_s2_campaign.py`, with the sha256 of the full diff;
  - the stat between consecutive S2b commits (fr start → fr commit → c3b → c4b), when they differ;
  - the full diff C2 → S2B_LAST in Appendix A of the output.
- **The refusal** (exit 2). E refuses unless both hold:
  - `git diff --quiet <S2B_LAST> HEAD -- <scripts 46-50> <E_FILES> S2/figures/fig_s2_c2_a2.py S2/c2_diagnostic/check5_diag.py`;
  - every E file exists at S2B_LAST (`git cat-file -e`).
- **The amendment.** Either failure is accepted only with `--amendment NOTE`, which must be:
  - committed and clean;
  - outside `scripts/`;
  - added or changed after S2B_LAST (`git diff --name-only --diff-filter=AM`);
  - carrying an ISO date on or after that commit's date.

  These are the rules of [48:1348-1368], re-implemented. E prints the note's path and sha256.
- **Archive commits** (INT-SHA, §8):
  - `ARCHIVE_COMMIT = {"c1": "b711f7e8673a75508cb1c6ac14f18d4f7dedfef8", "c2": "1d19eabfc386fb07e128c751318d9e794a4bd58b"}`;
  - for fr, the unique commit of `git log --diff-filter=A --format=%H -- results/objective2/s2/fr/campaign.json`.

## 8. Integrity checks (closed list; S2B:603-617)

- **How failures are printed.** On failure E prints `INTEGRITY FAILED: <id> <file or tar:member> <key path>`, never a value, and exits 3.
- **How passes are printed.** On success the INTEGRITY section prints each id with `ok` and its count, for example `INT-FINALPOS ok (4 relaxations)`.

| id | check |
|---|---|
| INT-IMPORT | the §2 assertions |
| INT-GUARD | the §4.3 rules on `TABLE` |
| INT-CALC-LOAD, INT-CALC-EXIT | `cd.assert_no_calculator()` (CALC_ENGINES [cd:32-39]) after the imports and at exit; `atoms.calc is None` for every Atoms E builds |
| INT-ROOT | `assert_no_c3` at exit |
| INT-SHA (OP-17) | every logged file's bytes have the sha256 of `git cat-file blob <ARCHIVE_COMMIT[c]>:<path>` (c1, c2, fr), or of the manifest entry for c3b and c4b (§13); and `git diff --quiet <ARCHIVE_COMMIT[c]> HEAD -- results/objective2/s2/<c>` |
| INT-SHA-STABLE | §4.5 |
| INT-K3-SHA | sha256(`c2/gates/K3.json` bytes) == `gate_file_sha256` of `gate_K3.json` |
| INT-K3-DEC | `decision.K3 == "fail_replan"` in both K3 files and in the marker; `result.checks_failed` identical in both, and equal to `["s2r_m30_VB76: final geometry fails check(s) [5]"]`, which the header requires |
| INT-K3-NULL | `is_none("result.value_meV")` in both K3 files. A non-null value is never printed: E stops, and the value is treated as a hinge item (S2B:553-554) |
| INT-FR-SHA | sha256(`fr/gates/FR.json`) == `gate_FR.json` `gate_file_sha256`; and sha256(`fr/gates/fr_step0.json`) == the `gate_file_sha256` of the marker of the last fr_step0 evaluation that ran (@4 if it ran, else @2) |
| INT-FR-DEC | `decision.FR.*` identical in `FR.json`, `gate_FR.gate.json`, the marker and `state_fr`; `decision.fr_step0.*` identical in `fr_step0.json`, its copy and its marker |
| INT-ROUTE | §6.1 |
| INT-COMMITS | §7 |
| INT-C1-CENSUS | §4.4: the classes, the 160 records, the 129 SP labels; the record-file names match `WORK_RE` |
| INT-PARTS, INT-PARSE, INT-NCFG, INT-KLAST, INT-FINALK, INT-FINALSHA, INT-FINALPOS, INT-CELL | §5.1, for every parsed relaxation |
| INT-READS | §5.2 |
| INT-HINGE-CLOSED | outside hinge mode, the audit log holds no `c2/raw/s2r_m30_{VB136,hostB136,Sr136o0_novac,Sr136o0_vac}.p*` and no `c2/structures.tar.gz` member `a2/<hinge label>/…` |
| INT-PB136-REC, INT-PB136-RAW | §4.4 |
| INT-STRUCT | a listed leaf that a code path requires is `ABSENT`, or has the wrong type |
| INT-SP | every SP that E needs has `sp_status(...)["status"] == "complete"`. A missing C1 SP is a structural failure, because C1 is complete (`C1_RESULT.md` §1) |

## 9. Header, labels, precision and output order

**Constants.**
- `FR_ORDER = ("s2r_m30_hostA188", "s2r_m30_VA188", "s2r_m30_Cs188o0_novac", "s2r_m30_Cs188o0_vac")`, asserted at load equal to `wt49 FR_QUARTET` order once FR is committed.
- `FR_STEP0 = {"s2_m30_VA188": "s2r_m30_VA188", "s2_m30_Cs188o0_vac": "s2r_m30_Cs188o0_vac"}`.
- `FAR = ("s2r_m30_hostB76", "s2r_m30_VB76", "s2r_m30_Sr76o0_novac", "s2r_m30_Sr76o0_vac")` (relaxations 5-8).
- `HINGE = ("s2r_m30_VB136", "s2r_m30_hostB136", "s2r_m30_Sr136o0_novac", "s2r_m30_Sr136o0_vac")` (relaxations 1-4) [49:326-330].

**The header** (S2B:619-621), printed at the top of the file, as the second line of every block, and in the figure caption:
```
S2 K3: fail (fail_replan); checks_failed: s2r_m30_VB76, check 5 (C2_RESULT.md). S2b FR: <fr_part>. Valid far references: <k> of 2.
```
- The K3 part is literal; INT-K3-DEC guards it.
- **`fr_part`** is one of:
  - `pass`;
  - `fail (FR-1, <decision.FR.cell>, <reason>)`;
  - `fail (FR-2)`;
  - `fail (step-0 final; gate not evaluated)` (OP-10);
  - `stopped at <cell> (<campaign_fr stop_reason>)`. Here `<cell>` is the first FR_ORDER label whose record status is `pending` or whose record is absent, else `gate FR`.
- **`<reason>` by `decision.FR.kind`:**
  - `check` → `check <n>[, <m>]`, from the `validity_final.failed` of that cell (OP-4). The fallback parses `result.checks_failed`'s `[…]`;
  - `end_rule` → `end rule <end_rule.outcome>`;
  - `missing` → `missing`;
  - `not_started_cap` → `hard-cap refusal`;
  - `killed_by_gate` → `killed by a gate`;
  - `not_run_gate` → `not run (gate)`;
  - `check_not_evaluated` → `no final-geometry check`.
- **`k`** = 1 if `decision.FR.FR1 is True`, else 0 (OP-11).

**Labels** (exact strings):

| id | text | where |
|---|---|---|
| L_ITEM4 | `S2 K3 failed (far quartet invalid); A1 not validated against A2 at the far site` | every row of kind `Eb_A1`, `Eb_q0` or `Eb_q1` while `decision.FR.outcome != "pass"` (S2B:623-629) |
| L_FRVALID | `far-site reference: FR, m30 FA188, valid` | the same rows when FR passed (S2B:631) |
| L_MACE | `zero-shot MACE, not re-admitted` | every `E_mace` and `Eb_mace` row and the determinism rows ([48:69]; S2B:675) |
| L_FAR | `far quartet invalid (check 5, VB76); reported only; not valid` | E_b^A2(Pb76) and δ_far(Pb76) (S2B:649) |
| L_TAIL | `path energy of the whole region over the window; not attributable to the failing objects; bounds no E_b error; reported only` | every ΔF_tail row (S2B:645) |
| L_FR1 | `FR quartet invalid (check <n>, <cell>); reported only; not valid`, or `FR quartet invalid (end rule <outcome>, <cell>); reported only; not valid` (OP-29) | the FA188 values when FR-1 failed and the quartet is complete |
| L_FR2 | `FR-2 failed (\|δ_far(FA188)\| > 50 meV in one quartet; bias and site scatter not separable); reported only` (with a plain `|` in the code) | the FA188 values when FR-2 failed |
| L_NOFORM_C1 | `not formable from C1 single points (no A2 cell)` | the q = 0 rows of S2B:668-670 |
| L_NOA1 | `no A1 DFT value` | MACE rows without a DFT A1 E_b (S2B:667) |
| L_NOTFORMED | `not formed (<reason>)` | an item that cannot be formed (S2B:694, 711-712) |
| L_NOA2 | `no S2 A2 cell` | the WP2c rows without a C4b cell |
| L_C4BNOTRUN | `C4b not run` | block-4 items on FR-fail routes (coverage) |
| L_HINGE_DIFF | `not a K3 decision; K3 failed on validity` | E_b^A2(Pb136) − E_b^A2(Pb76) |
| L_CA_Q0 | `not formable: no F of Ca D(136)` | the Ca136 q = 0 row |
| L_CA_MACE | `no DFT A1 E_b (Ca failed G1)` | the Ca136 MACE row |
| L_FALLBACK | `recorded by gate code; not cross-checked (E failed twice)` | §16 |
| L_NOTREAD | `not read: E failed` | §16 |
| L_XFAIL | `cross-check failed` | §15 |
| L_Q0 | `q = 0 link row (§10), reported only` | [48:915] |
| L_WP2C | `WP2c: whole-cell WP1 MACE geometry, q = 0, one far site (different protocol)` | [48:925] |
| L_A1TIER, L_A1TIER_INV, L_DOPANT{Sr,Cl,GA,Cs}, L_SENS | the strings of S2B:159-168 and 686-687, verbatim | block 4 only |

**Precision** (S2B:633):

| quantity | format |
|---|---|
| F, E_mace_eV, F(SP) and the WP1 E_host | eV, `%.6f` |
| E_b, δ, relaxation energy, ΔF_tail, F(k) − F(final), path work and shells, MACE E_b, q = 0 E_b, determinism dE | meV, `%.2f` |
| "full precision" (the difference to −5.0 meV, S2B:647) | `repr(float)` |
| distances | Å, `%.4f` |
| Σ\|dr\|² | Å², `%.6f` |
| forces | eV/Å, `%.6f` |
| cross-check residuals | `%.3e`, against the stated tolerance |

**Rows.** Every printed item is a `Row(block, id, kind, values, label_ids, text)`. Here `kind` is one of `F`, `relax_energy`, `Eb_A1`, `Eb_A2`, `delta`, `dF_tail`, `path_work`, `curve`, `Eb_mace`, `E_mace`, `Eb_q0`, `Eb_q1`, `forces`, `determinism`, `invalid`, `status`, `xcheck`, `note`.
- The formatter adds the labels by kind as above.
- The self-test inspects the rows and the text (§18).
- No row of blocks 1-3 has a `class` field.

**Output order** (fixed):
1. `S2b E, <attempt n of the one evaluation | hinge run> (S2B_PLAN.md §7); run at <UTC>; HEAD <40-hex>; mode <evaluation|hinge>`.
2. `tools:`, then one line per file, `<path> <sha256>`.
3. `imported at 8bff03e:`, then one line per file, `<path> <blob>`, including the four data files.
4. Interpreter versions; the roots; `no c3 entry in any root: ok`.
5. `route: <id>`, the preconditions that held, and the verify-record lines.
6. COMMITS (§7), and the amendment if any.
7. The header.
8. INTEGRITY.
9. BLOCK 1, BLOCK 2, BLOCK 3, then BLOCK 4 (or `BLOCK 4. Tier block: not printed (<reason>)`), then BLOCK 5 (or `BLOCK 5. Hinge block: not opened (…)`, §14).
10. COVERAGE (P §10, §15; §12.8).
11. CROSS-CHECKS summary.
12. READS summary.
13. APPENDIX A (the diff).
14. `END`.
15. `E exit code: <n>`.

## 10. Block 1: the far block (always; S2B:637-654)

Its title is `BLOCK 1. Far block: C2 relaxations 5-8 (m30, Pb76)`, followed by the header.

**The C2 constants** (`C2_RESULT.md` §2) are `(n_config, converged_at_k, restarts, reruns_from_zero)` per relaxation:

| # | label | n_config | converged_at_k | restarts | reruns_from_zero |
|---|---|---|---|---|---|
| 1 | VB136 | 79 | 78 | 0 | 1 |
| 2 | hostB136 | 83 | 82 | 0 | 0 |
| 3 | Sr136o0_novac | 81 | 80 | 0 | 0 |
| 4 | Sr136o0_vac | 75 | 74 | 0 | 0 |
| 5 | hostB76 | 165 | 164 | 0 | 0 |
| 6 | VB76 | 193 | 192 | 0 | 0 |
| 7 | Sr76o0_novac | 142 | 141 | 2 | 0 |
| 8 | Sr76o0_vac | 136 | 135 | 0 | 0 |

The ΔF_tail windows are `TAIL_K = {hostB76: 128, VB76: 156, Sr76o0_novac: 105, Sr76o0_vac: 99, VB136: 42, hostB136: 46, Sr136o0_novac: 44, Sr136o0_vac: 38}`, and `VB76_EXTRA_K = (158, 172)`. E asserts `TAIL_K[lab] == k_last − 36` (INT-STRUCT) and that every k is in `F`.

**1.1 Per relaxation, for 5-8 in order** (`read_relaxation(..., mode="far", kind="a2_far")`):
- `F(0)`, `F(final)` with its k, and `relaxation energy F(final) − F(0)`.
- `n_config`, `converged_at_k`, `restarts` and `reruns_from_zero`, each with `C2_RESULT.md §2: <constant>, cross-check <ok | cross-check failed>` (XC-C2R). Then the number of parts, against `restarts + 1` (XC-PARTS).
- Path work (OP-15):
  - `total W`;
  - `closure W − (F(final) − F(0))`;
  - `Σ|dr|²`;
  - `by shell (minimum-image distance from the k = 0 position to v or the site; lattice images passed to scripts/48 path_work unchanged)`: `0-4`, `4-6`, `6-8` and `8-1e+09`, each as W (meV) and Σ|dr|² (Å²).
- `F(k) − F(final)`, in lines of ten: `k <k0>-<k9>: v … v`. Restart parts are marked `| restart part n at k = …`.

**1.2 ΔF_tail** (label L_TAIL):
- hostB76: F(128) − F(final);
- VB76: F(156) − F(final), F(158) − F(final) and F(172) − F(final);
- Sr76o0_novac: F(105) − F(final);
- Sr76o0_vac: F(99) − F(final).

**1.3 The quartet** (Sr at Pb76):
- `E_b^A1(Pb76) from k = 0`. Beside it, `C1 (gate N; C1_RESULT.md §6): −5.0 meV`, with `difference E_b^A1 − (−5.0) = <repr> meV`.
  - E also prints the unrounded gate-N value `c1/gates/N.json result.dopants.Sr.hosts.m30.per_site_meV["76"]` and the difference to it at `repr` (OP-30).
  - The row carries L_ITEM4 or L_FRVALID.
- `E_b^A2(Pb76)`, with L_FAR.
- `δ_far(Pb76) = E_b^A2 − E_b^A1`, with L_FAR.
- E_b is formed as `((F_DV − F_D) − (F_V − F_h)) × 1000`, the differences first, as [49:272-277].

**1.4 Cross-checks:**
- XC-K3FAR: E_b^A2(Pb76) against `result.Eb_A2_meV.far` of `K3.json` and of `gate_K3.gate.json`, each `|Δ| ≤ 1e-6 meV`.
- XC-DSUM-FAR: `δ_far(Pb76) == (ΔF_DV − ΔF_D) − (ΔF_V − ΔF_host)`, with ΔF the relaxation energies, to `1e-6 meV`.
- XC-PLATEAU: `plateau differences: none`, which holds iff, for all eight records:
  - `n_config ≤ 200` (`a2_far`, `a2_hinge_counts`);
  - `end_rule.outcome == "accepted_converged"`.

  Otherwise E prints `plateau differences: not none (<labels>)`, with L_XFAIL. The plateau values of a hinge record stay unread.

## 11. Block 2: the FR block (always; S2B:655-660)

Its title is `BLOCK 2. FR block: m30 FA188, Cs (S2B §2)`, followed by the header.

- **Status lines.** For each FR_ORDER label E prints the record status. For a complete cell it also prints `end_rule.outcome` and `validity_final.{valid, failed}` under both readings: `check5_reading`, `valid_as_written` and `failed_as_written` (OP-4; S2B:267).
- **2.1 Per relaxation**, for every complete FR cell (`mode="fr", kind="a2_fr"`): the items of §10.1, without XC-C2R. The FR counts are checked only against the records, by INT-NCFG and INT-KLAST (OP-12).
  - The region is `c1/regions/m30_A188.json`.
  - E also prints ΔF_tail at `k_last − 36`, with L_TAIL (OP-13).
  - If a cell reached k = 200, E prints `plateau difference F(200) − F(180)` from the parse, never from `end_rule.dF_200_180_meV`. Otherwise it prints `plateau difference: none`.
- **2.2 Step-0** (OP-9). For each step-0 pair whose A2 cell is complete:
  - F(SP) (from `sp_full`), F(k = 0) and `F(k = 0) − F(SP)` (meV, `%.2f` and `repr`);
  - XC-FRSTEP0: `|ΔF| ≤ 0.5` must agree with the outcome in `decision.fr_step0`. With OP-9 adopted, `ΔF` must also equal `result.cells.<SP>.dF_meV` to 1e-6 meV.
- **2.3 Quartet values**, when all four cells are complete:
  - `E_b^A1(FA188)` from k = 0, with L_ITEM4 or L_FRVALID;
  - `E_b^A2(FA188)`;
  - `δ_far(FA188)`.
  - **Labels:** FR-1 failed with the quartet complete → L_FR1 on all three; FR-1 passed and FR-2 failed → L_FR2; FR passed → none, beyond L_FRVALID on the A1 value.
  - **If the quartet is incomplete:** `not formed (quartet incomplete: <labels not complete with their status>)`.
- **2.4 Cross-checks:**
  - XC-FR2: when `decision.FR.FR2 is not None`, the three values against `result.FR2.{Eb_A1_meV, Eb_A2_meV, delta_far_meV}` of `FR.json` and `gate_FR.gate.json`, `≤ 1e-6 meV`. When it is None: `gate FR recorded no FR-2 values (FR-1 failed)`.
  - XC-FR2-DEC: `fr2_pass(δ) = abs(δ) <= 50.0` must equal `decision.FR.FR2`.
  - XC-FR1-DEC: E's recomputed FR-1 and first failure must equal `decision.FR.{FR1, cell, kind}`. The recompute is the §2 order over FR_ORDER, using `status`, `end_rule.outcome ∈ END_ACCEPTED` and `validity_final.valid` (OP-4).
  - XC-DSUM-FR: the signed sum of the relaxation energies.
- **2.5 The invariant-only flag** (OP-8): `check 5 passed only under the identical-atom reading: <labels of result.invariant_only>`, or `none`. The tier labels of block 4 use this list.

## 12. Block 3: MACE and the deferred C1 items (always; S2B:661-675)

Its title is `BLOCK 3. MACE and deferred-C1 block (Pb136 cells excluded; see block 5)`, followed by the header.

- **3.1 MACE records.** These are the 155 records in class order (host, V, noise, startset, pose_start), then by wid.
  - Per record: `<wid> <class> valid <bool> failed <list>`.
  - Then one line per MACE leaf: `  <json path> E_mace_eV = <%.6f> eV`, with L_MACE. Host records have four leaves (`relax.E_mace_eV` and `relax.stages[0..2].E_mace_eV`).
  - XC-MACE-COUNT: 161 leaves in all, 4 per host record and 1 per other record. On a mismatch, E prints L_XFAIL with the counts.
  - Finally: `deferred to block 5 (Pb136): s2_m30_VB136, s2_m30_Sr136p0_novac, s2_m30_Sr136p0_vac, s2_m30_Ca136p0_novac, s2_m30_Ca136p0_vac`, by wid only.
- **3.2 Zero-shot MACE E_b**, with L_MACE on every row.
  - **Noise pilot** (40 quartets: per pilot, the far4 sites × `TOKENS_OF[L]`, Ca included). Per row:
    - `Eb_mace = m48._mace_eb(H[p], labels)`;
    - `Eb_A1 = m48.quartet_a1(T, p, d, f)["Eb_meV"]`, with L_ITEM4 or L_FRVALID; the reasons if it is invalid;
    - `Eb_mace − Eb_A1`.
    - XC-GATEN: `Eb_A1` against `c1/gates/N.json result.dopants.<d>.hosts.<p>.per_site_meV["<f>"]`, ≤ 1e-6 meV.
  - **Start set** (`m48._mace_pilot(T)["calibration"]`): m30 Cs128, GA128 and Cl138; m05 Sr124, Ca124, Cs28, GA28 and Cl49. Each row prints `Eb_mace`.
    - The DFT column is L_NOA1 in block 3, because `Eb_A1_dft_meV` is None without C4b. Where C4b ran, block 4 prints the C4b k = 0 value beside the same row (OP-16).
    - E asserts that no key `Sr136` or `Ca136` is present (INT-PB136-REC).
  - **Pose pilot** (`_mace_pilot(T)["pose_pilot"]`): Cs128, Cs188, Cl138 and Cl175, with `Eb_mace_default`, `Eb_mace_aggregate`, `N_D`, `N_DV` and the count term.
    - The DFT column for Cs188 and Cl175 is the noise-pilot `Eb_A1` of the same site (o0; one minimum per leg, `C1_RESULT.md` §3.4).
    - For Cs128 and Cl138 it is L_NOA1, because there is no V⁺ single point.
- **3.3 The q = 0 link rows** (P §10, not at Pb136). For each row E prints:
  - `E_b(q = 0) = eb(F[DV_q0], F_D, F[V_q0], F[host])`;
  - `E_b(q = +1)` from the same sources at q = +1 (OP-28);
  - `E_b(q = +1) − E_b(q = 0)`.
  - Every E_b carries L_Q0 and L_ITEM4 or L_FRVALID.
  - **Sr76:** both formable; the q = +1 value is the noise-pilot E_b.
  - **Cl138:** q = 0 is formed from `s2_m30_Cl138o0_novac`; q = +1 is L_NOFORM_C1 (no `s2_m30_VX138` SP).
  - **Cs128:** q = 0 is formed; q = +1 is L_NOFORM_C1 (no `s2_m30_VA128`).
  - **GA128:** both are L_NOFORM_C1 (no `s2_m30_GA128o0_novac` SP and no `VA128`).
  - E checks each "not formable" case by the absence of the label from the census, which is asserted.
- **3.4 Determinism** (P §5), from `m48._determinism(H, cdir, wp1_dir)` (§2): per pilot, `E_S2_mace_eV`, `E_WP1_eV`, `dE_meV` and `max_dr_A`, with L_MACE. If a value is None, E prints L_XFAIL (XC-DETERMINISM).
- **3.5 DFT residual forces of every A1 cell** (OP-1, OP-2). The q = 0 rows are included, with the free set of their base record; the G1 and spin outputs are not.
  - For each label in `NOISE_SP ∪ POSE_SP ∪ Q0_SP` (`sp_full`), and for `PB136_SP` through `sp_forces` if OP-1 is adopted (else `deferred to block 5`):
    - `all: rms max n`;
    - `free: rms max n`;
    - then `free norms: i:norm …` in lines of ten.
  - XC-FORCES applies to the non-Pb136 labels.
- **3.6 The invalid-cell table**, for C1, C2 and FR.
  - **C1:** every record (blind) with `validity.valid is not True`, as `campaign host wid dopant site leg failed`, plus every rejected pair (`c1/pairs/*.json` `status == "rejected"`: m30 Cs188p3 and Cs188p6), as `pair rejected (<rejection.exception>)`.
  - **C2:** every far and hinge record with `validity_final.valid is False` (OP-4; fallback: the K3 `checks_failed`). The expected row is `c2 m30 s2r_m30_VB76 — B76 — [5]`.
  - **FR:** every FR cell with `status != complete`, an end rule not in END_ACCEPTED, or `validity_final.valid is False`, with the failed checks and the reading.
  - An empty part prints `none`.
- **3.7 C1 pilot items of P §15** (last bullet; public C1 values, recomputed where they can be):
  - **Gate N:** `sigma_far_meV`, `df` and `pass` per dopant, from `c1/gates/N.json`. XC-GATEN-SIGMA recomputes σ_far from the per-site rows of 3.2, as `gate_n_eval` would, but in E's own code.
  - **The pose-pilot spreads:** `c1/gates/pose.json` `result.<tok>.{mode, a_pose_meV, delta_near_meV, delta_far_meV, near.{N_D, N_DV, count_term_meV}, far.{…}}`. XC-POSE recomputes Δ_pose from the four pose SPs and the noise-pilot SPs. The recompute is 0 when one minimum is kept per leg.
  - **The throughput row:** `c1/gates/throughput.json` `result.{rate_config_per_node_h, choice}` [49:874-879].
- **3.8 Coverage** (S2B:711-712). E prints a table that maps every item of P §10 and P §15 (P:788-820) to the block and row id where it is printed, or to its reason:
  - `C4b not run` or `not formed (FR failed: no C3b)` on FR-fail routes;
  - `withdrawn (D3BJ_AMENDMENT.md; sensitivity study after E)` for D3(BJ);
  - `deferred to block 5` for the Pb136 items.

  The self-test asserts that every item appears exactly once.

## 13. Block 4: interface only (to be specified before C3b; S2B:676-695)

`S2/s2b/e_block4.py` at the FR commit:
```python
BLOCK4_IMPLEMENTED = False
def tier_route(ctx) -> dict          # {"id": "C3B-STOP"|"C3B-NOTIER"|"C4B-NOTRUN"|"C4B-STOP"|"C4B-ENDED",
                                     #  "c3b": {...}, "c4b": {...}, "commits": {...}, "verify": {...}}
def c4b_df_delta_validity(ctx) -> dict   # {"df_delta": int, "m_d": {Sr, Cl, Cs, GA}, "units": [...],
                                         #  "function": "<module:function>", "blob": "<git blob>"}
def build_tier_table(ctx, c1, fr) -> dict     # s2-evaltable-1-shaped production table (c3b hosts; c4b a2)
def evaluate_tier(table, fr, *, hinge=None) -> dict   # A1 tier; calibrated tier only with hinge (δ_Sr,m30)
def rows(result, labels) -> list            # Rows of block 4
```
At the FR commit every function raises `NotImplementedError("block 4 is specified before C3b (S2B §7)")`. `route()` refuses past-FR routes while `BLOCK4_IMPLEMENTED` is False.

**Fixed now, for the block-4 specification:**
- **Dopants.** The dopants are `("Sr", "Cl", "Cs", "GA")` and the decisive ones are `("Cl", "Cs", "GA")`. No Ca appears in any pool or ranking: there must be no lookup of `pool["m"]["Ca"]`, as in [48:841].
- **C5 with FR.** `m_d ≥ 1 and df_δ ≥ 3 and |δ̄_d| ≤ 50 and decision.FR.outcome == "pass"` (S2B:356).
- **a_far.** `a_far = g49.separability(δ_far(FA188), s_δ, df_δ)["a_far_meV"]`, with the `c5_far` of the result ignored. δ_far(FA188) comes from block 2, and never from Pb76.
- **δ_Sr,m30** comes only from block 5's hinge quartet, and only when the trigger holds.
- **The df_δ count.** The trigger count is `c4b_df_delta_validity` (§4's "one committed function", OP-23), with Sr's hinge quartet counted valid.
- **Ranking.** The ranking runs over the 6 pairs of the 4 dopants, with `Q_RANK = 0.9975` (the 10-pair Bonferroni, S2B:576).
- **Labels.** The labels are L_A1TIER, the bracketed clause iff 2.5 is not `none`, and L_DOPANT* and L_SENS, all verbatim from S2B.
- **The tier and c4b guard modes** are added to `TABLE` under the §4.3 rules.
- **The private-archive manifest** for INT-SHA is `<private_root>/<c>/MANIFEST.sha256`, whose own sha256 is recorded in the committed c3b and c4b notes.
- **Open for block 4:** OP-27 (the C3b no-tier route) and the TIER/C4B leaf names.

## 14. Block 5 and the deferred hinge run (S2B:696-719)

### 14.1 Trigger

`hinge_trigger(route, b4)`:
- If `route != "C4B-ENDED"`, the result is `{"held": False, "df_delta": None, "reason": "C4b not run" | "C4b final STOP" | "FR failed" | …}`.
- Otherwise `n = b4["df_delta"]`, and `held = n >= 3`.
- **When not held**, E prints:
  ```
  BLOCK 5. Hinge block: not opened. df_δ counted from validity leaves (Sr's C2 hinge quartet counted valid): <n | not formed (<reason>)>; trigger df_δ ≥ 3: not held.
  Deferred, unread: relaxations 1-4 (s2r_m30_VB136, s2r_m30_hostB136, s2r_m30_Sr136o0_novac, s2r_m30_Sr136o0_vac); E_b^A1(Pb136), E_b^A2(Pb136), δ_Sr,m30; F of s2_m30_VB136 and s2_m30_Sr136o0_vac; the Pb136 q = 0 rows; the WP2c comparison at Pb136; E_mace_eV of the five Pb136 records; the zero-shot MACE E_b of Sr and Ca at Pb136. Read by E_hinge_output.txt at the first of: the evaluation of a later pre-registration that names it as data, in rules committed before 2027-06-30; 2027-06-30.
  ```
- **When held**, E prints the count line, then `trigger held: block 5 opened`, and switches `ctx` to hinge mode: `EGuarded` hinge tables, `C1Access(hinge=True)`, and OpenAudit's hinge allowance.

### 14.2 Content (hinge mode)

- **Relaxations 1-4.** These are read with `read_relaxation(..., mode="hinge", kind="a2_hinge")`. Each gets the §10.1 items, with XC-C2R and the region `m30_B136`, plus ΔF_tail at `TAIL_K` = 42, 46, 44 and 38, with L_TAIL.
- **The quartet and gate values:**
  - E_b^A1(Pb136), with L_ITEM4 or L_FRVALID;
  - E_b^A2(Pb136);
  - `δ_Sr,m30 = E_b^A2 − E_b^A1`, which is passed to block 4's `evaluate_tier(..., hinge=…)`.
- **F of the step-0 reference SPs** `s2_m30_VB136` and `s2_m30_Sr136o0_vac`, with `F(k = 0)` and `F(k = 0) − F(SP)`.
  - XC-STEP0-C2: `|ΔF| ≤ 0.5` must agree with `decision.step0.outcome == "pass"`. With OP-9, ΔF must also equal `result.cells.<SP>.dF_meV`.
- **`E_b^A2(Pb136) − E_b^A2(Pb76)`**, with L_HINGE_DIFF. E_b^A2(Pb76) is block 1's value; in the hinge run it is recomputed by block 1's code without printing it again.
- **The q = 0 rows at Pb136.**
  - Sr136: `eb(F[Sr136o0_vac_q0], F_k0[s2r_m30_Sr136o0_novac], F[VB136_q0], F[host])`.
  - Its q = +1 comparator: `eb(F_SP[Sr136o0_vac], F_k0[Sr136o0_novac], F_SP[VB136], F_SP[host])`.
  - Ca136: L_CA_Q0.
- **WP2c at Pb136:** `m48._wp2c_values()["m30_Sr136"]` beside E_b^A1(Pb136) and E_b^A2(Pb136), with L_WP2C.
- **The E_mace_eV of the five Pb136 records**, one per leaf, with L_MACE. XC-MACE-COUNT expects 5.
- **The zero-shot MACE E_b** from `m48._mace_pilot(T_hinge)["calibration"]["m30"]`, keeping only `Sr136` and `Ca136`.
  - Sr136 is printed beside E_b^A1(Pb136). XC-MACEPILOT-A1 checks that `Eb_A1_dft_meV` equals E's E_b^A1(Pb136) to 1e-6 meV.
  - Ca136 is L_CA_MACE.
- **The Pb136 residual forces** appear here if OP-1 is not adopted.
- **Cross-checks:**
  - XC-K3HINGE: E_b^A2(Pb136) against `result.Eb_A2_meV.hinge` of both K3 files, ≤ 1e-6 meV;
  - XC-DSUM-HINGE.

### 14.3 The deferred hinge run

`e_eval.py --hinge`:
- **Preconditions** (exit 2 if one fails):
  - the last evaluation attempt file exists, its exit code line is 0 or 1, and it holds the line `BLOCK 5. Hinge block: not opened`;
  - `E_hinge_output.txt` is absent;
  - the cause is shown in one of two ways:
    - `--hinge-cause prereg --prereg NOTE`, where NOTE is committed and clean, carries an ISO date before 2027-06-30, and contains the string `E_hinge_output.txt`;
    - `--hinge-cause backstop`, with the UTC date (an injectable clock) ≥ 2027-06-30.
- **What it runs.**
  - Phase 0, including the commits check against the S2b commit and an amendment if code changed.
  - Far mode and FR mode for the header and the Pb76 value.
  - Block 5 in hinge mode.
  - The full integrity phase over every file it opens.
- **Output.** It writes `S2/s2b/E_hinge_output.txt`, plus `fig_s2b_e_fk_hinge.csv` and `…_meta.csv`, with the same exit-code line.
- **Runs once.** It is exempt from "runs once" (S2B:715). Reruns follow §16, as `E_hinge_output_attempt2.txt`, and a third is refused (OP-22).

## 15. Cross-checks (closed list)

Each cross-check prints its values and residual. A failure adds L_XFAIL, suppresses no value and sets exit 1 (S2B:739-740).
- **Block 1:** XC-C2R, XC-ENDRULE, XC-PARTS and XC-MIC (each per relaxation); XC-K3FAR, XC-DSUM-FAR and XC-PLATEAU.
- **Block 2:** XC-FR2, XC-FR2-DEC, XC-FR1-DEC, XC-DSUM-FR and XC-FRSTEP0.
- **Block 3:** XC-GATEN, XC-GATEN-SIGMA, XC-POSE, XC-MACE-COUNT, XC-FORCES and XC-DETERMINISM.
- **Block 5:** XC-K3HINGE, XC-DSUM-HINGE, XC-STEP0-C2 and XC-MACEPILOT-A1.
- **Block 4:** to be added with block 4.

**Report only, with no pass or fail:** the closure of the path work, and the E_b^A1(Pb76) differences of §10.3.

## 16. Failure and rerun rules (S2B:727-741)

- **Attempt 1 fails before output** (exit 3). The tool is fixed in a dated commit, with a self-test case that fails on the earlier code. The rerun is `--rerun-cause CASE --amendment NOTE`. E then:
  - checks that CASE is a key of `e_selftest.CASES`;
  - runs CASE on the current code, where it must pass;
  - runs CASE on E's files at the attempt-1 commit, taken from line 1 of `E_output.txt` and loaded from a `git archive` into a temp dir, where it must fail;
  - writes `E_output_attempt2.txt`.
- **A code error found after output** (exit 0 or 1) follows the same route and writes `E_output_attempt2.txt` (P:960-963). The cause and the diff are listed in the S2b result note.
- **Attempt 2 fails before output: the item-7 fallback.** Phase 2 writes the failure report, then:
  ```
  FALLBACK (S2B §7, item 7): E failed twice.
  c2/gates/K3.json result.Eb_A2_meV.far = <%.2f> meV — recorded by gate code; not cross-checked (E failed twice)
  c2/gates_applied/gate_K3.gate.json result.Eb_A2_meV.far = …  (same label)
  fr/gates/FR.json result.FR2.Eb_A1_meV / Eb_A2_meV / delta_far_meV = …  (same label; "none recorded (FR-1 failed)" if decision.FR.FR2 is None)
  c2/gates/K3.json result.Eb_A2_meV.hinge = …  (only if the block-5 trigger held)
  every other part-c value, and the tier: not read: E failed
  ```
  - The fallback is a minimal code path that uses only `eg_load` and `get`, inside its own `try`.
  - If the trigger cannot be evaluated, `.hinge` is not printed.
- **A third attempt** is refused, except as follows (OP-21). It is allowed only when all of these hold:
  - `E_output_attempt2.txt` ends with exit code 3 and holds `FALLBACK`;
  - `--item7-amendment NOTE` is committed and clean, outside `scripts/`, and its commit date lies within 30 days of the attempt-2 commit date;
  - `--rerun-cause` fails on the attempt-2 code.

  That run writes `E_output_attempt3.txt`. A fourth is always refused.
- **"Before any later pre-registration commits its rules"** cannot be checked by code. The note must state it.

## 17. The figure `S2/figures/fig_s2b_e_fk.py` (S2B:721-725)

- **Source data** (written by E in phase 2; OP-24):
  - `S2/figures/source_data/fig_s2b_e_fk<suffix>.csv`, with the columns `block, campaign, order, label, quartet, role, k, part, dF_meV, k_last, restart_start, tail_k`. `dF_meV` is F(k) − F(final) as `repr`; `restart_start` is 0 or 1; `tail_k` is the window k, or empty.
  - `…_meta.csv`, with `key,value` rows `header`, `e_output`, `e_head`, `attempt` and `mode`.
  - The script opens no archive file. Its self-test runs under OpenAudit's self-test refusals.
- **Panels:**
  - a: the C2 far quartet (relaxations 5-8);
  - b: the FR cells that ran;
  - c: C4b, only if present;
  - for `--hinge`, one panel: relaxations 1-4.
- **Axes and marks:**
  - y is `symlog` with `linthresh=0.1` (meV). x runs from −2 to max(k_last) + 2.
  - Restart parts are ticks. Each ΔF_tail window is a light span `[tail_k, k_last]` with a marker at `tail_k`.
  - For VB76 there are dashed verticals at k = 156, 158 and 172, labelled.
  - End glyphs follow the end rule, as D-C2-11.
  - Colour shows the quartet and line style the role, as the C2 figure.
- **Caption.** `caption(meta)` returns a text that begins with `meta.header` verbatim. It is written to `S2/figures/fig_s2b_e_fk<suffix>.caption.txt` and into the PDF metadata `Subject`.
- **Build asserts:**
  - `dF_meV == 0` at k_last;
  - the ks are contiguous from 0 to k_last;
  - every label is a relaxation printed in the named E output;
  - `meta.header` equals that output's header line.
- **QA, as the C1 and C2 figures (nature-figure, Python backend):**
  - the panel-alignment audit;
  - PDF text ≥ 5 pt;
  - the collision audit;
  - the static preflight;
  - source data in `figures/source_data/`.
- **Self-test.** On a synthetic CSV (three relaxations, one with two restart parts and negative values) it checks that:
  - the build succeeds;
  - the caption holds the header;
  - a CSV whose value at k_last is non-zero is refused.

## 18. Self-tests (`e_eval.py --self-test` runs every case)

- **Ground rules.**
  - The self-tests run under OpenAudit in self-test mode. No case opens a real archive file of c1 (records, raw, gates, structures), C2 or S2b (S2B:601).
  - Inputs are synthetic archives built in `tempfile.mkdtemp(prefix="e_selftest_")` by `e_selftest.build(root, scenario)`. They use:
    - the 8bff03e extraction of §2 (git objects, not archive files);
    - `q47.synthetic_pw_output` [47:1426-1521], with `ranks=64` and per-part labels `<lab>.p<n>`;
    - `c46.write_cell`.
  - The git calls go through an injected `GitRunner`. One case (D4b) uses a real `git init` repository in the temp directory.
- **The synthetic archive** has three parts.
  - **c1:**
    - 160 records, with the census names and 4 or 1 `E_mace_eV` leaves holding unique canaries. Pb136: `−13613.613613 − i`;
    - 129 SP `.in.gz`/`.out.gz` pairs (`calculation="scf"`, nat 3, planted F, varied force rows);
    - regions for m30 B76, A188 and B136, with a centre near a cell face;
    - the pairs, eight distinct files `{"o0": "p0"}`, and two rejected pairs;
    - the smoke mapping literal (the C1 keys of map 2 §2d);
    - `upf_check.json` and the gates N, pose, G1 and throughput, consistent with the planted SPs;
    - `structures.tar.gz` with the A1 start and relaxed cells;
    - a synthetic wp1 directory.
  - **c2:**
    - 8 records with every listed leaf and the canaries `end_rule.dF_200_180_meV = 9876.54321`, `value_meV`, and an unlisted sibling at every depth;
    - parts with planted F(k). Relaxation 7 has 3 parts with restarts at k = 1 and 2;
    - `structures.tar.gz` finals;
    - `K3.json`, `gate_K3.gate.json` and `gate_K3.json`, with `gate_file_sha256` set to the bytes of K3, `Eb_A2_meV.hinge = 7654.321`, and `state_in`/`inputs_in` canaries;
    - `gate_K3.inputs.json` with a canary;
    - `campaign.json`.
  - **fr:** per scenario, with records, parts, finals, FR, fr_step0, the markers, `campaign.json` and `state_end.json`.
- **The reference for INT-SHA** is an injected manifest for the synthetic archive commits.

**A. Guard and access**

| id | asserts |
|---|---|
| A1 | For every (mode, kind) in `TABLE`, `get(p)` on a synthetic file succeeds iff p is a listed leaf. The file holds every listed leaf, every `fig.WITHHELD` and `WITHHELD_S2B` name as a canary at several depths and in list elements, and unlisted siblings. The set of paths read equals the list exactly, so the list is closed in both directions |
| A2 | Parents, `has`, `open`, `_wrap`, `repr`, `str`, `==`, `in`, iteration, `len`, `keys`, `items`, `values`, `copy.copy`, `copy.deepcopy` and `pickle.dumps` all raise `Blinded`. `ABSENT` cannot be printed |
| A3 | `eg_load` refuses `*.inputs.json`, a file outside the kind's list, hinge files in far mode and FR kinds in a C2-only call |
| A4 | `is_none` works only for `result.value_meV` of `k3`. A run with `value_meV = 1111.111` exits 3 with `INT-K3-NULL`, and `1111.111` is absent from the output |
| A5 | R1-R6 hold on `TABLE`; each planted violation (a copy of `TABLE`) raises at load |
| A6 | `.far` reads in far mode; `.hinge` raises in far mode and reads in hinge mode; `result.FR2.*` raises outside fr mode |
| A7 | `C1Access.record(..., blind=False)` raises for blocks 1 and 2, and for each Pb136 wid outside hinge block 5. `sp_full` raises for Pb136, G1 and spin labels. `sp_forces(Pb136)` raises unless `PB136_FORCES_IN_BLOCK3` |
| A8 | MACE canary (S0:965): block 3 prints every planted non-Pb136 `E_mace_eV` with L_MACE. `c46.load_record(p)` (blind) returns no `E_mace_eV` at any depth. `g49.Reader(lay, "c1", allow, evaluation=False).record(wid)` passes its no-MACE assertion [49:978-979]. `fig.guarded(c2 record).get("end_rule").get("dF_200_180_meV")` raises |
| A9 | With the hook installed, `open`, `gzip.open` and `tarfile.open` on a real `S2/c2/gates/K3.json` path raise before any OS open. So do the real `S2/c1/raw`, `S2/c1/records` and `S2/fr` paths |
| A10 | With `sys.modules["mace"]` planted, the run exits 3 with `INT-CALC-LOAD`. The plant is removed afterwards |
| A11 | No E source file other than `e_guard.py` contains `._d` |

**B. Readers**

| id | asserts |
|---|---|
| B1 | READS: ase +1 for one part and +3 for the three-part relaxation; F, forces and positions +n. A `_read_F` call planted between two reads gives `INT-READS` (exit 3) |
| B2 | `INT-KLAST` for accepted_converged, accepted_plateau (k_last 200, cap), unconverged_cap and unconverged_early (bfgs_failed): a consistent record passes and each inconsistent leaf fails |
| B3 | A final member moved by 2e-6 Å on one atom gives `INT-FINALPOS`; 0.9e-6 Å passes; a sha mismatch gives `INT-FINALSHA`; a cell mismatch gives `INT-CELL` |
| B4 | `sp_forces` equals `parse_sp`'s forces to 1e-12 eV/Å on every non-Pb136 synthetic SP, with READS F unchanged |
| B5 | An atom 0.5 Å from the far side of a cell face from the centre is in shell `8-1e+09` with plain centres and in `0-4` with image centres. XC-MIC holds. The closure equals an independent trapezoid sum to 1e-9 meV |
| B6 | A missing part number (p1, p3) gives `INT-PARTS`. A part labelled with another relaxation's input name raises in `parse_relax` [47:1025-1027] and is reported as `INT-PARSE` by stage and exception type only |

**C. Blocks and routes** (FR-fail scenarios; for each: blocks 1-3 printed; `BLOCK 4. Tier block: not printed (FR failed)`; `BLOCK 5 … not opened`; the header string exact; L_ITEM4 on every `Eb_A1`, `Eb_q0` and `Eb_q1` row; no `class` field; no hinge or Pb136 canary in the text; no hinge or Pb136 path in the audit log; the READS labels within the allowed sets)

| id | scenario (S2B §§1, 11) | further asserts |
|---|---|---|
| C1a | FR stops at the V⁺-host check 5 (D and DV not_run_gate) | header `fail (FR-1, s2r_m30_VA188, check 5)` and `0 of 2`; FA188 values `not formed (quartet incomplete: …)` |
| C1b | V⁺ unconverged_cap (plateau failed) | `end rule unconverged_cap`; the plateau difference printed from the parse; `dF_200_180_meV` canary absent |
| C1c | host_R accepted_plateau, then D unconverged_early (bfgs_failed) | plateau-accepted host continues; `end rule unconverged_early` |
| C1d | host_R missing | `missing`; no part opened |
| C1e | DV hard-cap refusal (not_started_cap) | `hard-cap refusal` |
| C1f | equal-charge pair fails (DV against V, check 5; the quartet is complete) | L_FR1 `(check 5, s2r_m30_Cs188o0_vac)` on all three FA188 values; XC-FR2 reads `gate FR recorded no FR-2 values` |
| C1g | check 3 fails at D | `check 3` |
| C1h | step-0 final (no FR.json) | header `fail (step-0 final; gate not evaluated)`; the 2.2 row for VA188 |
| C1i | FR-1 passes, FR-2 fails (δ = 50.001 meV) | header `fail (FR-2)` and `1 of 2`; L_FR2; XC-FR2 ok; XC-FR2-DEC ok |
| C1j | final STOP in fr: without `--stop-note` exit 2; with it, header `stopped at s2r_m30_Cs188o0_novac (<reason>)` | — |
| C2 | Independent recomputation (C1f and C1i) | Every printed number of blocks 1-3 equals `e_selftest.independent_*` to 1e-6 meV (1e-6 eV for F, 1e-9 Å): F(0), F(final), relaxation energies, ΔF_tail, E_b^A1 and E_b^A2, δ, path-work totals and shells, MACE E_b including the Boltzmann aggregate of a planted two-minimum pose leg, q = 0 E_b, and determinism. The independent code uses `fractions.Fraction` differences, explicit loops and `math.fsum`. Each printed string equals the formatted independent value |
| C3 | Counts | Block 3 lists 155 records and 161 leaves, and block 5 lists 5 deferred wids: 160 in all, disjoint. A planted 161st record `s2_m30_Sr136p1_novac` gives `INT-C1-CENSUS`. Without block 5, the planted Pb136 `E_mace_eV` and the Pb136 SP F canaries are absent from the text; with block 5 (case C6) they are present |
| C4 | Labels | L_NOFORM_C1 at GA128 (both rows) and at the q = +1 rows of Cs128 and Cl138; L_NOA1 on every start-set row and on the Cs128 and Cl138 pose rows; `not formed` (C1a); L_MACE on every MACE row; L_TAIL; L_FAR; the coverage table holds every P §10 and §15 item exactly once |
| C5 | FR-2 boundary | `fr2_pass(±50.000)` is True and `fr2_pass(±50.001)` is False; a planted `decision.FR.FR2` that disagrees gives L_XFAIL and exit 1 |
| C6 | Hinge opened (a test double of `e_block4`, with `BLOCK4_IMPLEMENTED` patched True, returning `df_delta = 3` and route C4B-ENDED) | block 5 printed; `δ_Sr,m30` equals the planted hinge value and is passed to `evaluate_tier`, not the Pb76 δ; XC-K3HINGE; L_HINGE_DIFF; L_CA_Q0; L_CA_MACE; WP2c row |
| C7 | The same test double, returning `df_delta = 2` | count line `2`, `not held`; no hinge path opened |
| C8 | Cross-check failure (K3 `.far` off by 2e-6 meV) | the `cross-check failed` line with both values; exit 1; output complete |
| C9 | Invariant-only pass (FR pass, `result.invariant_only = [VA188]`, the block-4 test double) | 2.5 lists VA188; the labels the test double prints carry the bracketed clause |
| C10 | Exception inside block 3 | the output holds only the stage name and exception type; exit 3; no CSV |
| C11 | Figure | `fig_s2b_e_fk.caption(meta)` begins with each scenario's header line |

**D. Discipline**

| id | asserts |
|---|---|
| D1 | A dirty tree (fake porcelain) gives exit 2, and no file is written |
| D2 | Attempts: `E_output.txt` present without `--rerun-cause` gives exit 2. A cause that fails on the old code and passes on the new, with an amendment, writes `E_output_attempt2.txt`. A cause that passes on the old code is refused. Both files present gives exit 2, except under the item-7 conditions, which write `_attempt3`. A fourth is always refused |
| D3 | Roots with `c3/`, `C3`, `c3.tar.gz`, `c3_notrun/` or a dangling `c3` symlink give exit 2; `c3b/` is allowed. A `c3/` planted between phase 1 and the exit audit gives `INT-ROOT` |
| D4 | A changed `scripts/49` between S2B_LAST and HEAD without an amendment gives exit 2. With a valid amendment the run goes ahead and records it; an amendment under `scripts/`, undated or not changed after S2B_LAST is refused. `campaign_c2 commit ≠ C2_COMMIT` gives `INT-COMMITS`. D4b runs the same in a real temp git repository |
| D5 | Preconditions: fr `running` is refused; `stopped` without a note is refused; FR pass with `BLOCK4_IMPLEMENTED = False` is refused; an `fr_outcome` inconsistent with `decision.FR` gives `INT-ROUTE` |
| D6 | Every INT check planted in turn exits 3, and the output holds the id, the file and the key path, and none of the planted numeric strings |
| D7 | Fallback: attempt 2 with a planted `INT-FINALPOS` prints the `FALLBACK` block with `.far` and the FR2 leaves and their labels; `.hinge` appears only in the trigger-held variant; `not read: E failed` |
| D8 | Hinge run: refused if block 5 was opened or the E output is missing; `prereg` with a dated note writes `E_hinge_output.txt`; `backstop` before 2027-06-30 (injected clock) is refused; a rerun without an attempt rule is refused; a planted hinge final-geometry mismatch exits 3 |
| D9 | The last line is the exit-code line in every written file. A concurrently created output file makes `O_EXCL` fail, giving exit 2 |

**T. Block 4** (committed with block 4, before C3b; P §17 item 2 and S2B:581-594)

| id | asserts |
|---|---|
| T1 | Independent recomputation of every §14 statistic to 1e-6 meV against a separate implementation: Ȳ, s_Y, t, I^A1, θ̂, a, b, SE, ν, t*, I_d, G_d, the flag, U_d, the required hosts, and the ranking over the 6 pairs |
| T2 | Planted classes: a repelling control; a binder; a null at low noise; a heterogeneous shell (one X site at −100 meV), flagged; one X site at −80 meV, not flagged and not classed "no first-shell interaction beyond k_BT" |
| T3 | Refusals of a validated class: control not repelling; df_δ = 2; \|δ̄_d\| = 50.001; the dopant-specific trip |
| T4 | Binding: a_far fires just above and not just below `t_{df}(0.975)·s_δ`, from FA188, with δ_far(Pb76) planted at 500 meV and never used; δ_Sr,m30 comes from the hinge quartet; "C4b not run" gives the A1 tier only; an invariant-only C3b or C4b pass counts as valid and is flagged |
| T5 | Routes S12-S19: C3b final STOP; C3b with no A1 tier; FR pass, invariant only, C4b not run (cut 2); C4b df_δ < 3; C4b final STOP; df_δ ≥ 3 with C1 failing; df_δ ≥ 3 with C5 failing; everything passes. Each asserts which blocks print, that block 5 opens only when df_δ ≥ 3, the header in every block and in the caption, and the labels |

## 19. Open points (ambiguities or conflicts between the plan and the code; recommended readings)

1. **The Pb136 residual forces (a conflict).**
   - The conflict: block 3 prints the forces of every A1 cell "Pb136 cells included" (S2B:672), but S2B:561-562 says no `c1/raw` output of a Pb136 cell is opened outside block 5. In addition, `parse_sp` full reads F along with the forces [47:1217].
   - Recommended: a dated S2B amendment admits the force-only reader of §5.3 for the five Pb136 SPs in block 3. That reader is D-C2-11's, asserted to read no F, and it applies to SPs only.
   - Fallback (flag False): the Pb136 forces move to block 5.
2. **G1 Ca136 outputs.** `s2g1_m30_Ca136o0_novac_e50`/`_e60` are not named by the deferral. Recommended: E never opens any G1 or spin output in any mode (they are neither A1 cells nor needed), so the question does not arise.
3. **`layout.ranks`** is on no allow-list, but S2B:537 requires "ranks from the record". Recommended: add it to every A2-record kind. Fallback: the literal 64, asserted against the C1 throughput decision.
4. **Validity leaves** are on no record list. They are needed for:
   - the invalid-cell table;
   - the FR header reason `check n`;
   - the "both readings" line (S2B:267);
   - the recomputation of FR-1;
   - the C4b δ validity and df_δ;
   - the A2 units of `dopant_specific`.

   Recommended: add `validity_final.valid` and `.failed` for relaxations 1-8, and the six FR leaves for fr. These are public non-energy leaves, already read in `C2_RESULT.md` §2 and the FR note. Fallback: derive validity from the K3 and FR reason lists, and drop the both-readings line.
5. **The `gate_K3.json` list says `decision`** (a parent). That conflicts with "refuses parents". Recommended: `decision.K3`.
6. **FR mode `decision.*`** is a wildcard. Recommended: the explicit `FR_DECISION_KEYS` and `FR_STEP0_KEYS` leaves of §4.2. `invariant_only` left `decision.FR` at [wt50:704].
7. **`result.FR2.Eb_A2_meV` (a conflict).** Its last segment is in the module-level `WITHHELD`, which S2B:544 puts on no list, while S2B:556 asks for it "under their exact field names". Recommended: the single explicit exception in R3.
8. **`result.invariant_only`** (labels only) is needed for the §1 bracketed clause, but is not on the FR list [wt50:1008-1012]. Recommended: add it.
9. **The step-0 values.**
   - The FR step-0 dF is listed in no block, but the FR ops draft defers it "to E, block 2".
   - The C2 step-0 cross-check of block 5 has no leaves either.
   - Recommended: print the recomputed values (§11.2, §14.2), and add the `result.cells.<SP>.{dF_meV, passed}` leaves for the cross-check.
10. **The header lacks "fail (step-0 final; gate not evaluated)"**, which §1 and `fr_outcome` use. Recommended: add it as a header alternative.
11. **"Valid far references: k of 2" does not say whether k counts FR-1 or FR as a whole.** Recommended: FR-1, the quartet's validity, so FR-2 fail gives "1 of 2".
12. **The FR per-relaxation items have no counterpart to "cross-checked against C2_RESULT.md §2".** Recommended: check against the records only (INT-NCFG and INT-KLAST). The FR note derives from the same records.
13. **ΔF_tail for FR** is not stated. Block 5 counts ΔF_tail among the "per-relaxation items". Recommended: `k_last − 36`, reported only, with L_TAIL.
14. **The k_last assertion "k_last = converged_at_k (or 200 at the cap)"** omits unconverged_early. Recommended: the record's `k_last`.
15. **`path_work` shells are plain Cartesian [48:1188].** The m30 Pb76 site lies at z = 0.037 Å. Recommended: pass lattice images as centres, with 48 unchanged and XC-MIC asserted. Print only that version.
16. **The start-set "DFT A1 E_b" beside MACE in block 3.** `_mace_pilot` takes it only from A2 k = 0 [48:786-789], and C1 single points cannot form any start-set quartet. Recommended: L_NOA1 in block 3, with block 4 printing the C4b k = 0 value when C4b ran.
17. **"The sha256 of each opened file against the verified archive" has no defined reference.** Recommended: the archive-commit blobs for c1, c2 and fr, and a committed-hash manifest for c3b and c4b.
18. **"After the archives … have passed verify" has no defined evidence.** Recommended: committed verify records, with the fr path to be fixed by the fr operations note.
19. **A "final STOP" cannot be told from `status: stopped` alone,** since every STOP writes that status [50:2248]. Recommended: `--stop-note`, a committed and dated note.
20. **"The S2b campaign commit" is singular,** but there are up to three (fr, c3b, c4b). Recommended: compare with the last of them, and print every consecutive diff.
21. **"A third attempt is refused" (S2B:524) conflicts with the item-7 "one more run follows" (S2B:735-736).** Recommended: `E_output_attempt3.txt`, only on the item-7 route of §16.
22. **The file name of a rerun of the hinge run** is not fixed. Recommended: `E_hinge_output_attempt2.txt`, and no third.
23. **The df_δ function and the import list.** "One committed function computes the stop, C5's df_δ and the trigger" (S2B:353-355) lies outside the closed import list. Recommended: a pure module outside `scripts/`, imported by both the c4b runner and E's block 4 and named by amendment, or E's `c4b_df_delta_validity` as that function.
24. **The figure source data and privacy.**
    - The plan does not say who writes the source data. Recommended: E writes it in phase 2, and the figure reads no archive.
    - On routes with private c4b data, the E output and the CSV sit at public repository paths. Recommended: they are committed only to the private record until the S2b result note.
25. **`campaign.json` and `state_end.json` are not named** among the files EGuarded covers. Recommended: read them through EGuarded too, which is stricter than required.
26. **The use of 49, 47 and 46 helpers beyond the closed import list.** E would otherwise use the label builders, `a2_cell`, `far4` and `RULES` of 49, and the `scripts/47` SP parsers and the `scripts/46` `load_record`. Recommended: E restates the 49 constants as literals asserted against 8bff03e, and uses only the 47 and 46 functions named in §2.
27. **The C3b no-tier route (for block 4).** The summary says "When C3b ran, it also reads the production MACE values" (S2B:32-33), but block 4 prints only if an A1 tier is computable. Recommended for block 4: a reduced block 4 on that route, holding the invalid-cell table, the forces and the MACE ledger.
28. **The q = +1 comparator of a q = 0 row** has no defined source. Recommended: the same F sources as the q = 0 row (single points where they exist, else k = 0 F).
29. **The FR-1 label template covers only checks.** Recommended: the end-rule variant of L_FR1.
30. **"Beside C1's −5.0 meV with the difference at full precision".** Recommended: print the difference to the literal and to gate N's unrounded value.
31. **`n_el` for `parse_relax`.** No A2 meta is archived (map 2 §1), so the electron count cannot be passed from a record. Recommended: do not pass `n_el`, as the gates and the C2 figure did. The UPF, version, ranks and label header checks still run.

## 20. [UNVERIFIED] items and risks

- **[UNVERIFIED] The WP1 `v2prod/<p>_host_relaxed.extxyz` members** that `_determinism` reads may carry calculator results; that would attach a `SinglePointCalculator`, which is not in CALC_ENGINES. The file was not opened.
- **[UNVERIFIED] `sha256(c2/gates/K3.json) == gate_file_sha256`** is expected from the code (`dump_public` re-dump [49:1460-1465; 50:4253-4262]; sizes 7267 = 7267, map 2), but it has not been checked by hash. INT-K3-SHA will settle it, and a mismatch stops E.
- **[UNVERIFIED] The exact key sets of `c2/state_end.json` and `fr/state_end.json`.** E reads only the listed leaves, and ABSENT is INT-STRUCT.
- **[UNVERIFIED] The FR field names** (`FR2.*`, `FR_DECISION_KEYS`, the `validity_final` additions, `fr_outcome`, the `gates_applied` ids `gate_fr_step0_{2,4}` and `gate_FR`) come from the moving worktree [wt49:406-411, 684-771; wt50:700-705, 2452-2476]. They must be re-verified at the FR commit, and the self-test pins them against the committed 49 and 50.
- **[UNVERIFIED] The c3b and c4b layouts, gates, df_δ leaf names and manifests** do not exist yet (block 4).
- **[UNVERIFIED] The fr verify-record path** (OP-18).
- **Risk: memory.** One full read of a 193-configuration, 233-atom relaxation holds every part's text until `parse_relax` returns. E therefore parses one relaxation at a time and keeps only the arrays of §5.1 item 7. The output itself is large (curves and per-atom forces); it is plain text of a few MB.
- **Risk: the guard is a discipline tool, not a sandbox.** `g._d` would bypass it, which A11 tests for, while `copy` and `pickle` are refused.
