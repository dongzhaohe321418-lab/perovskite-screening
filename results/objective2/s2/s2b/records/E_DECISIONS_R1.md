# Analyst decisions on the E implementation specification and its review (2026-11-12)

Source: `e_spec_output.json` (workflow wi6vnuxms): three code maps, the spec `E_IMPLEMENTATION_SPEC.md` (31 open
points, OP-n) and three reviews (1 critical, 6 distinct major, about 25 minor). Every item is decided below. Where a
decision changes or adds to S2B §7, it is carried by **amendment 2026-11-12a** (`S2B_AMENDMENT_2026-11-12a_DRAFT.md`),
appended to `S2B_PLAN.md` and committed before E's code and before FR is launched. Every item of that amendment affects
only values that are still unread (no fr cell has run; the C2 part-c values are blind), so S2B line 9 is met.

Binding for the implementer: the spec as amended by this file. Where this file and the spec differ, this file governs.
Where this file and S2B (with the amendment) differ, S2B governs and the implementer reports the conflict.

## Open points of the spec

| OP | decision | amendment item |
|---|---|---|
| 1 | Pb136 residual forces move to block 5. No `c1/raw` output of a Pb136 cell is opened outside block 5, by any reader. The force-only reader (§5.3 `sp_forces`) and XC-FORCES are dropped altogether; `PB136_FORCES_IN_BLOCK3` does not exist. | A1 |
| 2 | Adopted: E opens no G1 or spin output in any mode. | — |
| 3 | `layout.ranks` added to every A2-record kind. | A2 |
| 4 | `validity_final.valid` and `.failed` added for relaxations 1-8 in far mode, i.e. also to `a2_hinge_counts` (this resolves the block 3.6 major of all three reviews); the six FR validity leaves added to `a2_fr`. | A2 |
| 5 | `decision.K3` (leaf), not `decision`. | A2 |
| 6 | Explicit leaves only (`FR_DECISION_KEYS`, `FR_STEP0_KEYS`), re-verified against the worktree after the fix round (F3 removed `invariant_only` from `decision.FR`). | A2 |
| 7 | One explicit exception to R3: `("fr", "fr_gate", "result.FR2.Eb_A2_meV")`. | A2 |
| 8 | `result.invariant_only` added to `fr_gate`. | A2 |
| 9 | See RF-5 below. | A3 |
| 10 | Header alternative "fail (step-0 final; gate not evaluated)" added. | A4 |
| 11 | k counts valid far quartets (FR-1 for FA188): an FR-2 failure gives "1 of 2". | A4 |
| 12 | FR per-relaxation items are checked against the records only (INT-NCFG, INT-KLAST). | A5 |
| 13 | FR ΔF_tail at k_last − 36, labelled with L_TAIL; "not formed (k_last < 36)" below. | A5 |
| 14 | k_last is the record's `k_last`; see RF-4 for k_last None. | A5 |
| 15 | Path work by shell with minimum-image distances: lattice images of the site passed as centres to the unchanged `path_work`; XC-MIC asserted; only that version printed. | A6 |
| 16 | Start-set A1 E_b beside MACE in block 3: L_NOA1 ("no A1 DFT value"). | A7 |
| 17 | INT-SHA reference classes, see RF-11. | A9 |
| 18 | Verify records: `S2/c2_verify/verify_c2.txt` and `S2/fr_verify/verify_fr.txt` (named in the fr operations note §4). | A9 |
| 19 | `--stop-note` (committed, clean, dated note under `S2/` stating that the STOP is final). | A8 |
| 20 | S2B_LAST is the last S2b campaign commit; every consecutive diff is printed. | A8 |
| 21 | See RF-6. | A8 |
| 22 | `E_hinge_output_attempt2.txt`; no third. | A8 |
| 23 | Deferred to the block-4 specification (before C3b). Recommendation kept: one pure module outside `scripts/` imported by the c4b runner and by block 4. | — |
| 24 | E writes the figure source data itself in phase 2; the figure script reads only those CSVs. On routes with private c3b/c4b data, E's outputs are committed privately until the S2b result note. | A10 |
| 25 | `campaign.json` and `state_end.json` read through EGuarded. | A2 |
| 26 | Imports: from 47 `parse_relax`, `parse_sp`, `sp_status`, `end_rule`, `upf_md5_extra`; from 46 `load_record` (`write_cell` in self-tests only). `_header`, `_segment`, `_read_forces` are not used (OP-1). 49 constants restated as literals and asserted equal to the 8bff03e objects. | A7 |
| 27 | Deferred to the block-4 specification. | — |
| 28 | The q = +1 comparator uses the same F sources as its q = 0 row. | A7 |
| 29 | L_FR1 gets an end-rule variant ("FR quartet invalid (end rule <outcome>, <cell>); reported only; not valid") and a not-run variant ("FR quartet incomplete (<cell> <kind>); reported only; not valid"). | A4 |
| 30 | Print the difference of E_b^A1(Pb76) to the literal −5.0 meV and to gate N's unrounded value. | A7 |
| 31 | `n_el` is not passed to `parse_relax`. | — |

## Review findings

- **RF-1 (critical; deferred hinge precondition).** Adopt the reviewer's fix in full. `--hinge-cause prereg` needs
  `--prereg NOTE` and `--prereg-eval REC`:
  - NOTE is tracked and clean; it was added (`git log --diff-filter=A`) in a commit strictly after the commit that
    added the last E attempt file; that commit's committer date is before 2027-06-30; NOTE is not on the deny-list
    (`S2/S2B_PLAN.md`, `S2/S2_PLAN.md`, any `S2/*_OPERATIONS.md`, `S2/*_RESULT.md`, `S2/*_DIAGNOSTIC.md`, anything under
    `S2/s2b/`, any E output); its first 40 lines contain a "Status: PLAN" line; it contains `E_hinge_output.txt`.
  - REC is tracked and clean, added in a commit after NOTE's commit, and names NOTE's path (the record that the later
    pre-registration's evaluation is under way).
  - `--hinge-cause backstop` uses the real UTC date in run mode (clock injection only under `--self-test`) and is
    refused when any tracked file meets the NOTE conditions above (a later pre-registration has replaced the backstop).
  - D8 gains negative cases: S2B_PLAN.md, E_output.txt, a note whose text date is before 2027-06-30 but whose commit is
    after it, a NOTE without REC, a REC older than NOTE, a backstop with an injected clock in run mode.
  - The hinge run is also allowed after a FALLBACK attempt whose output holds "BLOCK 5. Hinge block: not opened"
    (the fallback prints that line whenever `.hinge` is not printed).
- **RF-2 (major; c3 lock).** Refuse an entry of a root when its name, case-insensitively, is one of `c3`, `c3.tar`,
  `c3.tar.gz`, `c3.tgz`, `c3_notrun`, or when it is a directory or a symlink (dangling included) whose name matches
  `c3([._-].*)?`. Regular files such as `C3_OPERATIONS.md` are allowed. OpenAudit's segment rule applies to directory
  segments of the path relative to the root. D3 gains `C3_OPERATIONS.md` (allowed) and `c3/`, `C3/`, `c3_x/`, a dangling
  `c3` symlink and `c3.tar.gz` (refused).
- **RF-3 (major; commit timing).** Hard refusal with no amendment route: every E file of §1 (`e_block4.py` as the stub)
  and `figures/fig_s2b_e_fk.py` must exist (`git cat-file -e`) at `fr/campaign.json` `start_commit` and at every
  `commit_history` entry; on past-FR routes, `e_block4.py` with `BLOCK4_IMPLEMENTED = True` must exist at the c3b
  start commit. The `--amendment` route stays only for changes between S2B_LAST and HEAD. D4 cases for both.
- **RF-4 (major; relaxations with few configurations).** A complete record with `k_last` None or `n_config` 0 is
  read without the final-geometry checks and returns `{parsed: True, n_config: 0}`; every quantity needing F prints
  "not formed (no configuration; end rule <outcome>)". `path_work` None prints "path work: not formed (< 2
  configurations)". k_last < 36 prints "ΔF_tail: not formed (k_last < 36)". An ABSENT `validity_final` on a complete
  cell is "check not evaluated", as `fr_eval` does. C1 cases: SCF failure at k = 0 for D (FR-1 fails, kind end_rule),
  and k_last = 20.
- **RF-5 (major; step-0 files and killed cells; OP-9).** One leaf set per file, by a fixed map:
  `s2_m30_VA188` from `fr/gates_applied/gate_fr_step0_2.gate.json` (decision from its marker);
  `s2_m30_Cs188o0_vac` from `gate_fr_step0_4.gate.json`, and from `fr/gates/fr_step0.json` only when @4 ran.
  C2 (hinge mode only): `s2_m30_VB136` from `c2/gates_applied/gate_step0_1.gate.json`, `s2_m30_Sr136o0_vac` from
  `gate_step0_4.gate.json` and `c2/gates/step0.json`. The implementer verifies these C2 gate ids from the C2 code and
  the public file names only. For each evaluation that ran, block 2 prints the gate-recorded `dF_meV` and `passed`,
  labelled "recorded by gate code"; when the A2 cell is complete it also prints E's recompute and XC-FRSTEP0 against
  that evaluation's own `passed` and decision; when the cell is `killed_by_gate` it prints "cell killed by the step-0
  gate; output set aside, not archived". C1h is rewritten to the real state (VA188 `killed_by_gate`, no raw part).
  Synthetic gate files hold one cell each, as the gate code writes them.
- **RF-6 (major; item-7 fallback condition; OP-21).** Attempts:
  - attempt 1 fails before output (exit 3): fixed and rerun once as attempt 2 (`--rerun-cause`);
  - attempt 1 completes (exit 0/1) and a code error is found after output: one rerun as attempt 2. If that attempt 2
    fails before output, it writes its failure report only (exit 3, no fallback); attempt 1's output stands as E's
    output, and the result note lists the error, its cause and the diff. No attempt 3 on this route;
  - the item-7 fallback is written only when attempt 1 and attempt 2 both failed before output. Its one further run
    (item-7 amendment) writes `E_output_attempt3.txt`. A fourth is always refused.
  D7 negative case: attempt 1 exit 0, attempt 2 exit 3 → no FALLBACK text, attempt 3 refused.
- **RF-7.** R4 restated: `.far` in far and hinge modes, `.hinge` only in hinge mode, `result.FR2.*` and fr step-0
  `dF_meV` only in fr mode, C2 step-0 `dF_meV` only in hinge mode.
- **RF-8 (two-phase write).** Phase 0 asserts that the attempt file and both CSV paths are absent. Phase 2 writes each
  CSV to a temporary file in the same directory and links it into place (`os.link`, which fails if the target exists),
  CSVs first, the attempt file last with `O_EXCL`. If a CSV link fails, the partial files are removed and the attempt
  file is written as a failure report (exit 3).
- **RF-9 (self-tests and real files).** No self-test names a real archive path. A9 runs on a synthetic tree that
  mirrors the S2 layout, with a sentinel that raises if the original open is reached. Old-code and new-code `--rerun-cause`
  cases run in a subprocess (`python -B -I`) with OpenAudit in self-test mode.
- **RF-10 (OpenAudit coverage).** Use `sys.addaudithook` on the `open` event (covers `builtins.open`, `io.open`,
  `os.open`, `open_code`, pathlib) to log and refuse; keep the tar-member log. A9 case through pathlib and `os.open`.
- **RF-11 (INT-SHA references; OP-17).** Every logged path falls into exactly one class: c1, c2, fr archive files →
  the archive-commit blobs (fr: the commit that added `fr/campaign.json`); c3b, c4b → committed manifests (block 4);
  `<tmp>` files → the 8bff03e blobs; tracked notes and verify records → the HEAD blob, with the clean-tree check; E's
  own outputs → exempt. A logged path in no class is INT-SHA failed.
- **RF-12 (absent leaves and files).** `eg_load` on an absent listed file returns `FILE_ABSENT`; each route states
  which files it requires (missing → INT-STRUCT) and which absences it implies (asserted): no fr step-0 files when
  VA188 never reached k = 0; no `fr/gates/FR.json` on step-0 final; no `fr/state_end.json` on FR-STOP. Per leaf, the
  spec states whether ABSENT is allowed and what it maps to. Each case has a self-test.
- **RF-13 (XC-ENDRULE).** When `end_rule.end` ends with "(operator)", compare with the override (outcome
  unconverged_early, k_last equal to the record's). `end_rule.end` is added as a listed leaf (A2).
- **RF-14.** ΔF_tail k_last < 36: as RF-4.
- **RF-15 (item-7 amendment scope).** `git diff --name-only <attempt-2 commit> HEAD` must be a subset of E_FILES plus
  the note, with no change to scripts/46-50, `fig_s2_c2_a2.py` or `check5_diag.py`. D2 negative case.
- **RF-16.** C1Access keeps its own log of (wid, blind, block); INT-PB136-REC uses it.
- **RF-17.** FR_ORDER and FR_STEP0_PAIRS are restated as literals and asserted, at load, equal to the values obtained
  by `ast.literal_eval` of the assignments in HEAD's `scripts/49` (parsed, never executed). The single-READS check
  scans `gc.get_objects()` for module objects whose `__file__` ends with `47_s2_qe.py` and requires exactly one.
- **RF-18 (synthetic archive).** The builder post-processes `q47.synthetic_pw_output` text: per-atom distinct force
  rows and positions; F planted as decimal strings of at most 8 places, from which the independent code starts with
  `Fraction`. Planted F give every role distinct, non-zero, mixed-sign E_b^A1, E_b^A2, δ and relaxation energies, so
  that swapping D and V or flipping a sign changes every checked value. FR-2 cases at δ = +50.000, +50.001 and −50.001
  meV. One synthetic distinct file holds o0 and o1, and the table builder maps kept minima through `work_ids` as
  [48:1037-1052].
- **RF-19.** Helpers are loaded with `importlib.util.spec_from_file_location` from `os.path.dirname(__file__)`; S2/s2b
  is never put on `sys.path`.
- **RF-20.** Catch `q47.S2Error` and `q47.Refused` around 47 calls.
- **RF-21.** Restore `u+w` on the temp tree's directories before `rmtree`, in a `finally`; a failure to delete is
  reported without changing the exit code.
- **RF-22.** XC-FR2-DEC only when `decision.FR.FR2` is not None; else "FR-2 not evaluated (FR-1 failed)". C1f exit 0.
- **RF-23.** XC-PARTS only when `reruns_from_zero == 0`; else "restarts include discarded attempts", plus INT-PARTS.
- **RF-24.** `H[p]["E_mace"][label] = record["relax"]["E_mace_eV"]`; stage leaves are printed in block 3 but enter no
  E_b. Planted stage leaves carry distinct canaries.
- **RF-25.** L_ITEM4 (or L_FRVALID) is attached to every row whose values include an A1 E_b, including the DFT column
  of MACE rows and differences that contain an A1 E_b (a Row attribute `has_a1`). C4 asserts it on the noise-pilot and
  pose-pilot DFT columns.
- **RF-26 (info).** Map-1 note on two 46 instances: harmless; RF-20 covers the exception classes.

## Process

- E is implemented in its own private work tree, which mirrors the fr worktree's files at the time
  of creation; E adds only new files (`S2/s2b/e_*.py`, `S2/figures/fig_s2b_e_fk.py`). After the fr fix round, the E
  files are copied into the fr worktree and every self-test is rerun there.
- Every agent works only in its own uniquely named private work directory.
- The blinding list of the summary is binding for every agent. No agent opens, greps, hashes or decompresses any
  file under `c1/raw`, `c1/records`, `c1/gates*`, `c2/`, or `c1/structures.tar.gz`, or any `*.out.gz`, `*.a2.json`,
  `*.gate.json`, `gates/*.json`. Self-tests use synthetic archives only.
