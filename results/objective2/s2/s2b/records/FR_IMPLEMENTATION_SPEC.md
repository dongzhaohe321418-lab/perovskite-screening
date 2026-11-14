# Implementation specification: S2b campaign `fr`

**Repository and line numbers.** The repository is the analyst's checkout of this repository, at HEAD `4d27d2d`. Running `git diff --stat 8bff03e HEAD -- scripts/ ehpc/` touches only `scripts/27` and `ehpc/EHPC_REBUILD_GUIDE.md`. So every [46:n]-[50:n] and `ehpc` line cited here is also the plan's line.

**Blinding.** I opened no blinded path, computed no energy and modified nothing.

## 0. Design
- **The campaign.** `fr` is a new campaign with the phases check → a2 → gate. It runs four A2 jobs in `FR_ORDER`, one copy at a time, strictly in sequence.
- **Order and early stop.** One pure function, `g49.fr_progress`, decides both. The runner calls it on every tick. Gate FR calls it once, at the end, on the same record fields. The runner asserts that the two results agree.
- **Gates.**
  - Step-0 is its own gate, `fr_step0`, with its own state key `fr_step0`.
  - Gate FR is a single gate at the end, in phase `gate`.
- **Check 5.** The invariant reading is an opt-in in scripts/46 (`check5_reading="invariant"`). The default output stays byte-identical.
- **Commit.** A new HEAD is admitted once, through `fr/CAMPAIGN_COMMIT`. `state["commit"]` stays `8bff03e`.
- **Scope of every change.** Each new branch keys on `self.c == "fr"`, on a gate in {fr_step0, FR}, or on an FR label. The C1-C4 paths change only by tuple membership, plus one refusal that writes nothing (§4.4).

## 1. Identifiers and state keys

**Constants in scripts/49 (the source of truth):**
- `FR_QUARTET = {host: s2r_m30_hostA188, V: s2r_m30_VA188, D: s2r_m30_Cs188o0_novac, DV: s2r_m30_Cs188o0_vac}`.
- `FR_ORDER = (host, V, D, DV)`.
- `FR_STEP0_PAIRS = {"s2_m30_VA188": "s2r_m30_VA188", "s2_m30_Cs188o0_vac": "s2r_m30_Cs188o0_vac"}`.
- `RULES["FR2_MAX_MEV"] = 50.0`, pinned by a new `S2B_PINS`. `PLAN_PINS` is unchanged.
- `FR_ENERGY_FIELDS = ("Eb_A1_meV", "Eb_A2_meV", "delta_far_meV", "dF_meV")`.

**Constants in scripts/50:**
- `FR_ORDER` as a literal; the self-test asserts it equals `g49.FR_ORDER`, as C2_ORDER is checked.
- `S2B_CAMPAIGNS = ("fr",)`.
- `S2B_STATE_KEYS = ("campaign_commit", "fr_step0", "fr_stop", "FR")`.

**New keys in the node-global `state.json`, written only in fr:**

| key | writer | content |
|---|---|---|
| `campaign_commit` | the commit route | `{"fr": <40-hex>}` |
| `fr_step0` | 49 gate fr_step0; the runner (repeat, NO_ERROR) | attempts, outcome (pass, fail_pending_fix, fail_final, repeat_pending), repeat, fix_note, cell (A2 label), attempt1, no_error_found, note |
| `fr_stop` | the runner's scan | at, kind, time |
| `FR` | 49 gate FR | outcome (pass/fail), FR1, FR2 (bool or None), part (None, "FR-1", "FR-2"), cell, kind, invariant_only |

- `kind` takes one of: end_rule, check, check_not_evaluated, missing, not_started_cap, killed_by_gate, not_run_gate. None of these keys holds a value or a check list.
- `commit_history` only gains entries, each with `via` and `campaign`.
- Every other key is protected (§4.5).

## 2. scripts/46
1. **`Layout._c`** [46:1574-1577]: admit `"fr"`. On the node the path is `work/s2/fr`; in the archive it is `fr/`.
2. **`check_partner`** [46:1400-1443]: add the keyword `exchange_n=False`.
   - When it is True, each FA row also gets `rot_exchanged_deg = a38.kabsch_deg(_rel_skeleton(parent.positions, sk, cell), _rel_skeleton(child.positions, [cc[0], cc[2], cc[1]], cell))`. This is D5's `Qc[[0,2,1]]` [D5:135-136]; `kabsch_deg` centres the points [38:69-75].
   - The as-written `ok` [46:1441-1442] is computed unchanged.
   - With `exchange_n`, the result gains:
     - `passed_as_written = ok`;
     - `passed` under D5's rule: inorganic dr < 0.25 Å, and for FA, carbon dr < 0.25 Å and min(rot, rot_exchanged) < 20°;
     - `reading: "invariant (D5, check5_diag.py 966aa75)"`;
     - `fa_needs_exchange`, the carbons that pass only through the minimum.
   - With the default, the function is byte-identical and adds no key. D5's R46 assertion [D5:340-345] and the C2 records depend on this.
3. **`validity_a2`** [46:1476-1493]: add `check5_reading="as_written"`.
   - Any value other than `as_written` or `invariant` raises S2Error.
   - Check 5 runs with `exchange_n=(reading == "invariant")`, and `failed` and `valid` follow its `passed`.
   - For `invariant` only, the output adds `check5_reading`, `valid_as_written`, `failed_as_written` (taking check 5 from `passed_as_written`) and `invariant_only` (valid but not valid as written).
4. **`job_validate_a2`** [46:2025-2071]: take `reading = job.get("check5_reading", "as_written")` and pass it through. The `rule` string gains a clause only for `invariant`.
5. **Untouched:** `build_region`, `build_pair`, `write_cell`, `a2_order` and `campaign_of`. `campaign_of` raises for FR labels, but only the self-tests call it.

## 3. scripts/49
1. **Constants.** Add the §1 constants after [49:376].
2. **`label_campaign`** [49:389-399]: make the first line of the `s2r` branch `if label in FR_ORDER: return "fr"`.
   - `is_blinded` [49:402-405] stays unchanged, so FR labels are not blinded to gate code, as C2's are not.
   - This is required: the invariant at [49:2109-2112] fails if any allow-list holds an energy mode on a blinded label.
   - Blinding from the analyst comes from the guard in §6.
3. **Step-0, generalised.** The C2 output stays identical.
   - Add `STEP0_GATES = {"step0": ("step0", STEP0_PAIRS), "fr_step0": ("fr_step0", FR_STEP0_PAIRS)}`.
   - `step0_eval(..., pairs=STEP0_PAIRS)`, using `pairs` at [49:567]; `gather_step0(reader, cells=None, *, pairs=STEP0_PAIRS)`.
   - `allow_list("fr_step0")`: full on the FR_STEP0_PAIRS keys, k0 on its values, and `smoke:c1`.
   - `derive_inputs` [49:1301-1316] and `evaluate_gate` [49:1412-1421] look up the key and the pairs in the table.
   - The fr_step0 decision is `{"fr_step0": {**prev, attempts, outcome, repeat, fix_note, "cell": FR_STEP0_PAIRS[sp]}}`. Exactly one SP must be given; otherwise GateRefused.
   - The `step0` branch emits today's dict unchanged.
   - FR has one repeat in total: after a repeat, every later fr_step0 is attempt 2, by the I-F3 carry-over.
4. **`fr_progress(rows, *, final=False)`**: a pure function with no I/O.
   - Each row holds `{label, status (A2 record status or None), end_rule (outcome or None), check (a2v job state or None), valid (validity_final.valid or None)}`. Rows not in FR_ORDER raise GateRefused.
   - In order, for each cell:
     - status None or `pending`: when `final`, GateRefused; otherwise return `next = label`;
     - any status other than `complete`: the kind is that status;
     - an end rule outside END_ACCEPTED: kind `end_rule`;
     - `valid` None while not final and the check is None or pending: return `next = None`, so the runner waits;
     - `valid` None otherwise: kind `check_not_evaluated`;
     - `valid` False: kind `check`.
   - It returns `{first_failure: None | {cell, kind, end_rule}, next, cells_not_run, passed}`.
5. **Gate FR.**
   - **`allow_list("FR")`:** the files `a2:<lab>` for each FR label and `smoke:c1`; the records `a1_start_of(lab)`; k0 and final reads on FR_ORDER.
   - **`gather_fr`** follows the K3 pattern [49:1242-1254]: from each record, status, `end_rule.outcome`, the `validity_final` leaves, and `a1_valid` (reported only).
   - **`fr_eval`:**
     - GateRefused if any `validity_final` lacks `check5_reading == "invariant"`.
     - Calls `fr_progress(final=True)`, with check = done if `validity_final` exists.
     - Its result holds: `cells`, `first_failure`, `end_rule_failed`, `checks_failed` (K3-style strings), `cells_not_run`, `invariant_only` (labels), `a1_invalid_reported` and `FR1`.
   - **Before evaluating at all,** GateRefused if `fr_step0.outcome` is fail_pending_fix or fail_final.
   - **FR-2, only if FR1 passes:**
     - It requires `fr_step0 == {outcome: pass, cell: s2r_m30_Cs188o0_vac}`, else GateRefused.
     - It reads k0 and final through `_relax_value` [49:1145] and writes `result.FR2 = {Eb_A1_meV (from the k = 0 F, eb_meV [49:272]), Eb_A2_meV, delta_far_meV, bound_meV, passed}`.
     - `fr2_decide(d) = d is not None and abs(d) <= 50.0`. A missing value is GateRefused.
     - No energy is opened when FR-1 fails.
   - **Decision:** `{"FR": {...}}` as in §1.
6. **Names, CLI and notes.**
   - `GATE_NAMES` [49:1063] gains `fr_step0` and `FR`; their case-folds stay unique.
   - Both names join the mapping tuple at [49:1390].
   - The CLI campaign choices at [49:1500, 1506] gain `fr`.
   - NOTES gain entries for X3, X4, X6 and S2B §2.
   - `verify` [49:1472-1488] needs no change.

## 4. scripts/50, in implementation order
1. **Constants.**
   - `CAMPAIGNS` [673] gains `"fr"`. This also covers `load_walls`, `cmd_status` and the CLI [7290-7295].
   - `PHASES["fr"] = ("check", "a2", "gate")` [678-682].
   - The §1 constants go after [694].
   - NOTES [702] gain N-FR1 to N-FR8, citing S2B §§1, 2 and 9 step 3, and X3-X6 and X13.
2. **Graph.**
   - `graph_fr` holds:
     - `check:upf` and `check:nodescripts`;
     - `_a2_jobs(G, list(FR_ORDER))` [1263-1273], unchanged; through `a2_parent` [1017-1026] the partners come out as V→host, D→host and DV→V;
     - `gate:fr_step0@2` in phase a2, depending on `k0:s2r_m30_VA188`, with `at` set to that label;
     - `gate:fr_step0@4`, depending on `k0:s2r_m30_Cs188o0_vac`;
     - `gate:FR` in phase gate, depending on the four a2v jobs.
   - Register it in `GRAPHS` [1396].
   - In `expected_counts` [1405], `fr` returns `{"a2": 4, "a2_validate": 4, "gate": 3}`. This branch must sit before the C3 fall-through at [1436], because `assert_counts` runs on the node [2511-2513].
   - No a2→a2 dependency is added. The order is enforced by the scan (item 10).
3. **Backend.**
   - `NodeBackend` gains:
     - `git_is_ancestor(a, b)`, using `merge-base --is-ancestor`; any exit other than 0 or 1 is a Stop;
     - `git_tracked(path)`, using `ls-files --error-unmatch`;
     - `git_unchanged(a, b, paths)`, using `diff --quiet`.
   - `MockBackend` takes the same answers from its config.
   - `MockBackend.graph` [4653] returns `graph_ref_fr(state)` for `fr`: four `ref=True` rows labelled with FR_ORDER (as in `graph_ref` [4657]), plus the three gates.
4. **Refusal of c1-c4.** As the first statement of `run()` [4085], before `makedirs`, the lock or any log line:
   - if `self.c` is c1-c4, `campaigns.c2 == "done"`, and HEAD differs from `state.commit` (or git fails), print to stderr and return 2.
   - Today this case is a Stop that writes `CAMPAIGN_STOPPED` and rewrites `campaign.json` [2245-2248], which would hit the private not_run c3.
   - STEP0_FIX and NODE_FIX cannot apply after C2 is done, so this changes no live route.
5. **State protection.**
   - At `load_state` [2304], for S2b campaigns, record a digest of every key outside `S2B_STATE_KEYS`, `campaigns` and `commit_history`, plus `campaigns` without the S2b ids, plus the existing `commit_history` entries.
   - `save_state` [2025] raises S2Error, and writes nothing, if that digest has changed.
   - `run_gate` stops on any fr decision key other than `fr_step0` or `FR`, before `state.update` [2743].
6. **Commit route.** In `check_commit` [2356], after the clean test: `if self.c in S2B_CAMPAIGNS: return self.check_commit_s2b(head)`. The C1-C4 body stays byte-identical.
   - **First start.** `fr/CAMPAIGN_COMMIT` holds `<40-hex> <YYYY-MM-DD> <note path>`. It is accepted only if all of these hold:
     - exactly three tokens;
     - token 1 equals HEAD;
     - the date matches `^\d{4}-\d{2}-\d{2}$`;
     - the note path is relative, lies under `results/objective2/s2/`, contains no `..`, is tracked at HEAD, and its text contains the date;
     - `git_is_ancestor(state.commit, HEAD)`;
     - `git_unchanged` for `qe_queue.sh`, `chain.sh` and `s2_run_qe.sh`;
     - C2 is done;
     - `c46.hygiene_violations(line)` finds nothing.
   - **On acceptance**, one `save_state` records `campaign_commit.fr = HEAD` and appends `{from, to, note, time, via: "fr/CAMPAIGN_COMMIT", campaign: "fr"}` to `commit_history`. Only then is the file renamed `.used.<t>`, following R6-C1-3. Any refusal is a Stop that names every reason and writes nothing.
   - **Later starts.** HEAD must equal `campaign_commit.fr`. The only other route is `fr/STEP0_FIX`:
     - It is checked the same way, with the recorded fr commit as the ancestor, and only while `fr_step0` is fail_pending_fix.
     - On acceptance it updates `campaign_commit.fr`, appends to `commit_history` and renames the file.
     - It then calls `discard_checks("fr")` [2409-2416] and `fr_step0_repeat`.
   - **`fr_step0_repeat`** is new; `step0_repeat` [2418-2436] is never called for fr.
     - The failed cell is `fr_step0.cell`.
     - It moves `fr/a2/<cell>`, `gates/fr_step0.json`, and that check's `gates_applied/gate_fr_step0_{2|4}{.json,.gate.json,.inputs.json}` into `discarded/step0_attempt1_<t>/{a2,gates,gates_applied}`. The archive glob at [4285-4287] picks these up.
     - It sets `fr_step0` to repeat_pending, with the note and `attempt1`.
     - It pops no key, and the other cells stay as they are.
7. **`set_campaign`** [2035]: the commit recorded is `campaign_commit[c]` for S2b campaigns. For c1-c4 the expression is unchanged.
8. **`preconditions`** [2438], fr branch. Each missing item is a Stop.
   - c1 and c2 are done, c3 is not_run, and c4 is absent.
   - `fr/STEP0_NO_ERROR` turns `fr_step0` into fail_final, as in [2460-2468].
   - The smoke mapping and A2 layout are checked as in [2471-2476]. Layout `2x32` is a Stop.
   - fr refuses if `g49` is the stub [516].
   - The branch reads no K2, K3, step0, gateN, cuts or n.
9. **Stop state.**
   - `a2_stopped` [3623-3628], for fr only: `fr_step0.outcome` is fail_pending_fix or fail_final, or `fr_stop` is set. Otherwise the state's K3 = fail_replan would mark every FR cell not_run_gate at the first tick.
   - Add `"fr"` to the tuples at [3631] and [4185].
10. **Scan and launch.**
    - At the top of `schedule()` [2621], after `spot_check`, for fr when A2 is not stopped:
      - run `g49.fr_progress` on the records and on `st["a2v:<lab>"]`;
      - write `fr_stop` once, then save and log `FR early stop at <cell> (<kind>)`;
      - keep `self.fr_next`.
    - The scan runs in `schedule()`, not in `a2_phase`, because after the last cell fails the active phase is already `gate`.
    - In `a2_phase` [4000-4049]:
      - for fr, the not_run_gate reason reads "FR early stop at <cell> (<kind>; S2B §2)" or "FR step-0 <outcome>";
      - fr launches only `j["label"] == self.fr_next`, with one copy.
11. **Gates.**
    - **`gate_inputs`** [2708]: for fr_step0, the SP comes from the inverted pairs; attempt 2 if the state shows a repeat or repeat_pending; the note is taken from the state.
    - **`run_gate`** [2726]:
      - On fr_step0 fail_pending_fix, call `a2_stop_all` and raise a Stop that names `fr/STEP0_FIX` and `fr/STEP0_NO_ERROR`.
      - After gate FR, stop unless (FR1 is true and `fr_stop` is absent) or (`fr_stop.at`, `fr_stop.kind`) equals (`FR.cell`, `FR.kind`).
    - **`status()`** [2579-2585]: `gate:FR` is skipped at fail_final, which gives the plan's "gate not evaluated".
12. **`run_a2v`** [3963-3992], for fr:
    - the job carries `"check5_reading": "invariant"`;
    - after the existing `validity_final` literal, add `check5_reading`, `valid_as_written`, `failed_as_written` and `invariant_only`; a Stop if the reading is not invariant;
    - the log line says "checks evaluated (check 5 invariant)" and gives no pass/fail and no check list.
13. **`cmd_status`** [4342-4343]: also print `campaign_commit`, `fr_step0`, `fr_stop` and `FR`.

## 5. ehpc/node
- **`s2_campaign.sh`** lines 4 and 13: accept `fr` only (`case "$C" in fr) ;;`), with a new usage text. The runner's refusal (§4.4) is the second layer.
- **`s2_relaunch.sh`:**
  - set `CAMPS="c1 c2 c3 c4 fr"`;
  - replace [37] with a loop over `$W/$c/CAMPAIGN_STOPPED`;
  - make [45] read `for c in $CAMPS`;
  - keep the exactly-one rule [51].
  - Under `set -e`, a failing `[ ] &&` as the last command of a loop does not abort the script. I tested this.
- **Unchanged, byte for byte:** `s2_run_qe.sh`, `qe_queue.sh`, `chain.sh`, `install_mace.sh` and `s2_status.sh` (check:nodescripts at [1773-1810]).

## 6. The extended guard: new file `results/objective2/s2/s2b/guard.py`
- **Base.** It loads `figures/fig_s2_c2_a2.py` unchanged. `WITHHELD_S2B = WITHHELD ∪ FR_ENERGY_FIELDS ∪ {F_sp_eV, F_k0_eV, F_final_eV}`.
- **`GuardedS2b(Guarded)`** for fr A2 and validity records. `get`, `open` and `_wrap` use `WITHHELD_S2B`, and children stay `GuardedS2b`.
- **`GateLeaves`** for fr gate files, `gates_applied` copies and markers.
  - It reads full dotted paths from a closed list: `decision.*`, `result.checks_failed`, `result.end_rule_failed`, `result.cells_not_run`, and `gate`, `campaign`, `attempt`, `schema`, `id`, `rc`, `applied` and `gate_file_sha256`.
  - Every other path raises, including parents, `state_in`, `inputs_in`, `c1_in` and `opened`. Iterating, printing and comparing are refused.
  - A step-0 STOP mode (D-C2-10) also admits `result.cells.<SP>.dF_meV` and `.passed` of the failing SP.
- **`--self-test` canary** on a synthetic fr archive:
  - every energy leaf, `end_rule.dF_200_180_meV` included, raises;
  - the allowed leaves can be read;
  - parents, `repr`, `==`, iteration and `open()` on a subtree that holds a withheld field all raise.

## 7. Input identity and the dry run (§9 step 3, D4): new file `results/objective2/s2/s2b/fr_inputs.py`
- **Rebuild.** From the C1 source, it rebuilds the region `m30_A188` and the pair `m30_Cs188p0`. The source is either archive members of `c1/structures.tar.gz` read in memory, with records loaded blind, or the node's `c1/` tree. It compares them with `c1/regions` and `c1/pairs` as canonical JSON, without `written`.
- **Inputs.** It writes the four part-1 inputs exactly as `a2_launch` [4051-4082] does.
- **Comparison.** It runs in a worktree of `8bff03e` and at the S2b commit. The `.in` files must be identical; the `.meta.json` may differ only in `campaign` and time.
- **On the node** it is D4, written outside `/data/work/s2`.

## 8. Self-tests

**scripts/46.** Extend `t_jobs` [46:2672-2768], which already builds Cs at the ref233 A site 128:
- the default output equals the `as_written` output and adds no key;
- on the Cs128 D and D+V⁺ legs (A-site map):
  - nitrogens exchanged with their hydrogens: fails [5] as written, passes invariantly, flagged `invariant_only`;
  - 20.1°: fails both readings;
  - 19.9°: passes both;
  - carbon moved 0.26 Å, with the exchange: fails both;
  - inorganic atom moved 0.30 Å: fails both;
- on the same cases, `check5_diag.d5_check` gives `passed_exchanged` equal to the invariant reading, and `passed` equal to the as-written reading;
- an unknown reading raises S2Error.

**scripts/49.** A new `t_fr`; the existing cases stay unchanged.
- **Labels:** each FR label maps to `fr`, is not blinded, is outside A2_ORDER, matches LABEL_RE and has the right `a1_start_of`. `S2B_PINS` holds.
- **`fr_progress`:** each failure kind at each of the four positions, `cells_not_run`, the waiting cases, and a wrong order.
- **fr_step0:**
  - 0.5000 meV passes and 0.5001 meV fails;
  - SPs from the other set are refused in both directions;
  - only the `fr_step0` key is written, and a planted `state["step0"]` is unchanged;
  - after a repeat, the next evaluation is attempt 2.
- **Gate FR, on `_TestLayout`:**
  - passes at δ = 49 meV;
  - fails FR-2 at δ = 51 meV;
  - fails FR-1 for each cell and each kind;
  - flags `invariant_only`;
  - refuses a missing reading, a failed step-0, and FR-1 without the step-0 pass at D+V⁺;
  - opens no relaxation file when FR-1 fails;
  - `fr2_decide` passes at ±50.000 and fails at ±50.001.
- **Energy-name canary:** evaluate FR twice with planted F perturbed non-uniformly. Every result leaf that changes, outside `opened`, `inputs_digest`, `written` and `commit`, is named in FR_ENERGY_FIELDS.
- **`verify --campaign fr`** reproduces every file with 0 differing, then reports 1 after an output is changed.

**scripts/50, unit cases on temporary roots, as cases (m) and (n) do [4987-5073]:**
- graph counts, `FR_ORDER == g49.FR_ORDER`, the a2v partners, and the case-fold test (z1) extended with the fr ids;
- the route: accepted; refused for each condition with `state.json` byte-identical; accepted again at the same HEAD; refused at any other HEAD; STEP0_FIX accepted only at fail_pending_fix;
- a c1-c4 start at the S2b HEAD returns 2 and no file under c1-c4 changes;
- with K3 = fail_replan and K2 = fail in the state, `a2_stopped` is False for fr and True for c2;
- an early stop at each of the four cells:
  - `fr_stop` is written once;
  - the later cells become not_run_gate with the FR reason;
  - no cell starts while the previous check is pending;
  - a failure at the last cell is caught in the gate phase;
- step-0:
  - a failure at V⁺ raises a Stop whose text names the routes;
  - STEP0_FIX moves only `a2/s2r_m30_VA188` and the marker trio;
  - STEP0_NO_ERROR leads to fail_final, and `gate:FR` is skipped;
- k = 0 read from the files after a relaunch;
- key isolation;
- gate FR disagreeing with `fr_stop` gives a Stop;
- the fr fields and log line of `run_a2v`;
- the relaunch script:
  - "WOULD RELAUNCH fr" for a running fr;
  - `fr/CAMPAIGN_STOPPED` is listed and the relaunch refused;
  - cases (z19) and (z23) switch from `c1` to `fr`.

**Mock fr campaign.** It runs after `c_campaign` [4880] in the same sysroot, so the ledger and H_spent carry over.
- **Setup:**
  - plant a C2-done state (K3 = fail_replan) and a synthetic `c2/` tree;
  - write `fr/CAMPAIGN_COMMIT`;
  - run `run --campaign fr --mock` with:
    - a spot notice during host_R, with a restart part;
    - a shift on V⁺ so that check 5 fails;
    - scripted gates `fr_step0` (pass) and `FR` (fail at VA188, kind check).
- **Assert:**
  - the records read complete, complete, not_run_gate, not_run_gate;
  - `fr_stop` is set and `fr_step0@4` is skipped;
  - CAMPAIGN_DONE is written;
  - the protected keys and every file under `c1/` and `c2/` are byte-identical;
  - the boot record lists fr;
  - `archive --campaign fr` succeeds.

**Guard.** The `--self-test` of §6.

**Regression at the S2b commit.**
- Every self-test of 46, 47, 49 and 50 passes, and so does D5's.
- `49 verify --archive results/objective2/s2 --campaign c2` prints exactly `c2_verify/verify_c2.txt`.
- `verify_fields.py` reproduces `verify_fields_c2.txt`.

## 9. Why C1 and C2 stay byte-identical
- **No C2 key is written.**
  - fr decisions are limited to `fr_step0` and `FR`.
  - The digest guard refuses any other change.
  - `step0_repeat` is never called for fr.
- **No file under `c1/`, `c2/` or `c3/` is written.**
  - fr only reads c1 inputs.
  - c1-c4 starts are refused before any write.
- **The default paths are unchanged:**
  - the defaults of the 46 checks;
  - the step0 decision dict;
  - `a2_stopped` and the `validity_final` literal for c1-c4;
  - the C2 log lines;
  - `node_fix` and the C1-C4 body of `check_commit`.
- **The regression set (§8) confirms it.**

## 10. Choices for the fr operations note
1. Host_R's check 4 is decided before V⁺_R starts. This matches §8's "6 if it stops at host_R".
2. FR gets one step-0 repeat in total, following P's "at most once" and §8's "up to 72".
3. The end rule is taken from the A2 records, as for K3.
4. The FR-2 energies are opened only after FR-1 passes.
5. The §8 projection at the FR decision is not run by fr. The c3b code computes it first, with its inputs fixed at FR's end.
6. The expected verify result: fr_step0 differs in its inputs digest only, because the node read a growing output (D-C2-6); FR reproduces.
7. During the campaign the operator reads `fr_stop`, `FR.*` and the D-C2-5 fields. The validity leaves are read after CAMPAIGN_DONE and verify.
8. **D1-D3**, at the launch and at every relaunch:
   - the checkout is clean at `campaign_commit.fr` (at the first launch, the route token);
   - `8bff03e` is an ancestor of HEAD;
   - the node scripts and the pw.x sha256 match C1;
   - the UPF files match `c1/upf_check.json`.
   D4 is the §7 tool.

## 11. Risks
- **The critical one.** Without campaign scoping, `a2_stopped` would silently mark every FR cell not_run_gate, because the state holds K3 = fail_replan. A unit case and the mock run both cover it.
- **The last-cell blind spot.** A failure at the last cell is caught only because the scan runs in `schedule()`.
- **A held unconverged_early STOP** is raised before the scan runs. The same `fr_stop` is then written at the relaunch.
- **A missing FR-2 value is GateRefused (a STOP).** Under the §1 table, that still ends FR as failed.
- **Two ways of finding FA molecules.** 46 uses `a38.molecule` and D5 uses a C-N distance cut. They agree on the reference cells; §6b checks them on the real FR pairs.
- **A relaunch skips the checks** (D-C2-9), so D1-D3 must be repeated by hand.
- **The tail of C2's last boot** is counted from its journal or the I-F8 bound. If FR never boots, a `manual.json` row closes S2's total (§8).
- **`s2_campaign.sh` starts only fr.** Any c1-c4 action needs a checkout at `8bff03e`.
- **Hard cap.** After a hard-cap refusal, the later cells read not_started_cap, not not_run_gate. The FR note must say so.