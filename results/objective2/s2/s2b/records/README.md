# S2b design records (committed with the S2b campaign commit, before fr starts)

These records define the ruling codes that the S2b code and `../../FR_OPERATIONS.md` cite (amendment 2026-11-12a of
`S2B_PLAN.md`, item 15; integration ruling IX-24). They were written between 2026-11-12 and 2026-11-13. No fr cell had
run, and no value that any of them governs had been read: every C2 part-c value, every C1 MACE value and every fr
value was unread (`S2B_PLAN.md` §0, §7).

| file | what it is | codes it defines |
|---|---|---|
| `E_IMPLEMENTATION_SPEC.md` | the implementation specification of E (blocks 1-3 and 5; block 4 as an interface) | OP- |
| `E_DECISIONS_R1.md` | the analyst's decisions on the first review of E | RF- |
| `E_DECISIONS_R2.md` | the analyst's decisions on the second review of E | ER2- |
| `FIG_DECISIONS_R3.md` | the analyst's decisions on the review of the FR figure | FG- |
| `FR_IMPLEMENTATION_SPEC.md` | the implementation specification of the fr runner, gates and node changes | - |
| `FR_IMPL_DECISIONS_R1.md` | the analyst's decisions on the first review of the fr code | its own F and T items |
| `FR_IMPL_DECISIONS_R3.md`, `_R4.md`, `_R5.md` | the analyst's decisions on the later reviews of the fr code | R3-, R4-, R5- |
| `INTEGRATION_DECISIONS.md` | the analyst's rulings on the integration of the four S2b tools | IX- |

**Other codes.**
- **D-C2-.** These are the provisions of `../../C2_OPERATIONS.md` (OPS2), as `../../FR_OPERATIONS.md` §2 keeps,
  adapts or supersedes them for fr.
- **N-FR and N-F.** These are the runner notes in `scripts/50_s2_campaign.py` (`NOTES`).
- **X.** These are the codes of `S2B_PLAN.md`.
- **Older R3- and R5- codes in `scripts/50`.** Citations written "round-3 R3-<m>" or "round-5 R5-<m>" predate S2b.
  They come from the reviews of the C1 runner and appear in its N-F notes and in self-test cases z1 to z28. The S2b
  codes R3- to R5- of the table are cited as "FR_IMPL_DECISIONS_R<n> R<n>-<m>", or bare in the fr code and its cases.
- **Ids in the self-tests and docstrings.** Ids of review findings, mutants and code maps (such as M3, G07, R-1, F01,
  ST01 or "map 2") label test cases. They are defined in the review reports, which stay in the analyst's private
  record folder. Each test states what it checks.
- **Workflow-run ids** (such as w739j3tt0) name the private review runs whose reports a record decides on. They are
  kept for traceability and name no path.
- **W and W4** are the records' names for the uncommitted integration tree and the figure's work tree.

**References that changed after writing.**
- `E_DECISIONS_R1.md` names the amendment's draft file. That draft is the amendment now appended to `S2B_PLAN.md`.
- IX-13 says the fixed strings go into "amendment item 14". They are in item 15 (IX-24).
- Line numbers cited inside the records (such as `[50:n]`, `W 50:n` or `S2B:n`) refer to the files as they stood when
  each record was written. The code at the campaign commit is the reference.

**How these copies differ from the analyst's originals.** The changes are limited to rewording the lines that named
a local path, an agent's work directory or tree, or a reviewer's harness directory, to meet the public-repository
rules. Nothing else was changed:
- `E_IMPLEMENTATION_SPEC.md`:
  - line 4, the repository's local path;
  - line 13, the integration tree's directory name;
  - line 19, the interpreter and temporary file of the one check run;
  - line 60, the interpreter rule.
- `FR_IMPLEMENTATION_SPEC.md`: line 3, the repository's local path.
- `E_DECISIONS_R1.md`: lines 147 and 150, E's work tree and the agents' work directories.
- `FR_IMPL_DECISIONS_R1.md`: lines 86-87, a shared work area.
- `FR_IMPL_DECISIONS_R3.md` line 65 and `FR_IMPL_DECISIONS_R4.md` lines 11 and 31: the reviewers' harness directories.
- `FR_IMPL_DECISIONS_R5.md`: lines 3, 9 and 38, the reviewer's harness directory and files.
- `INTEGRATION_DECISIONS.md`: lines 97 and 181, a harness directory and a private snapshot.
