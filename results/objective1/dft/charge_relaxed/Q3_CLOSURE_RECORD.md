# Q3 demotion closure record (audit F-019 reconciliation)

**The condition stated by the demotion — "until an audit cycle closes the Q3 findings" — is
met, and was met before the F-019 contradiction arose.** This file is the closure artifact the
canonical index points at; the underlying verdicts live in the audit-loop controller state, not
in this repository.

| Q3 finding | raised | independently verified closed | where recorded |
|---|---|---|---|
| F-006 (raw records not committed / not reproducible) | CYCLE-000001, -000002, -000004 | **CYCLE-000005** | `verified_closed_findings` in CYCLE-000005's audit_result.json |
| F-012 (alignment-value convention error) | CYCLE-000005 | **CYCLE-000006** | same field, CYCLE-000006 |
| F-013 (index self-contradiction on raw provenance) | CYCLE-000005 | **CYCLE-000006** | same field, CYCLE-000006 |

Since closure, three further independent cycles re-executed `q3_raw/derive_q3.py` in isolated
clones and reproduced every quoted value (custody hashes, 160→159 mapping, cosine 0.9757 and
controls, IPRs, +75.8/+52.1 meV alignments): CYCLE-000010, CYCLE-000011, CYCLE-000016.

**Consequence:** Q3's shallow-donor result (bounded form: "no thermally significant polaron";
a weakly bound few-meV state not excluded) is restored as CITABLE and as admissible Q0-gate
evidence for condition 3. The Q0 gate's condition-3 PASS and the canonical index now assert
the same state. Scope limits unchanged: PBE+D3(BJ) level, single distortion mode probed,
conclusions bounded as in `Q0_POLARON_EXCLUDED.md`.
