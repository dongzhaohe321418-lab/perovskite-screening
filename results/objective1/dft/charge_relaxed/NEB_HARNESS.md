# q=0 NEB restart/archive/state-ID harness — gate condition 5

**Built and validated against a real neb.x band, not a synthetic fixture.**

`scripts/26_neb_harness.py` implements the three things condition 5 names, each mapped to a
requirement the PI set:

| function | requirement | validation |
|---|---|---|
| `archive_iteration()` | snapshot the band after every NEB iteration, nothing overwritten | 2 snapshots written to `iter_000/`, `iter_001/`; a third write to an existing index **raises** |
| `verify_restartable()` | prove the latest snapshot is a usable `neb.x` restart | re-parses the archived `.path`, re-hashes it against `INDEX.json`, checks image/atom-count consistency |
| `identify_state()` | match the defect state **without** band index | per-atom weight cosine against the stored q=0 reference; band index is never read |

## Selftest — against the preserved q=+1 explore band

The selftest does **not** use a file I wrote. It extracts `q1_explore_state.tar.gz` — the band
`neb.x` itself produced during the q=+1 explore run — and round-trips it:

    selftest_pass    : true
    n_images         : 5
    rows_per_image   : 159
    snapshots_written: 2
    verify           : {restartable: true, snapshot: 1, n_images: 5, rows_per_image: 159}

5 images × 159 atoms is the correct shape for this cell, parsed back out of the archive with a
matching sha256. Regression test [31] runs this selftest and asserts every one of those values,
so a harness regression fails the suite rather than surfacing during a live NEB.

## Design decisions worth recording

**Parse before archiving.** `archive_iteration()` parses the `.path` file *first* and only
copies it if parsing succeeds. An unreadable snapshot is never written, so the archive cannot
accumulate files that look like restarts but aren't.

**Append-only, enforced not just documented.** Writing to an existing `iter_NNN/` raises
`FileExistsError`. Combined with the hash ledger in `INDEX.json`, a silently-mutated snapshot is
detectable — `verify_restartable()` re-hashes and fails on mismatch.

**No band index anywhere in state identification.** Per the standing rule, the defect state is
matched by the cosine of the per-atom weight vector against the stored reference. Adding empty
bands renumbers bands; it does not change where the state lives in space.

## Condition 5 status: components complete, end-to-end pending

| component | state |
|---|---|
| NEB input generation | done (`scripts/11_generate_neb_input.py`, used for the q=+1 band) |
| restart from an archived band | done, round-tripped on the real q=+1 `.path` |
| append-only iteration archive | done, 2 snapshots, hash-indexed |
| state identification without band index | done |
| **exercised end-to-end on a live q=0 job** | **NOT YET — requires the q=0 NEB to start** |

The last row is the honest remaining gap and it is circular by nature: the harness cannot be
proven on a live q=0 job until a q=0 job runs, and the gate exists to stop that job starting
unprotected. The resolution is to treat the **first** q=0 NEB as the harness's live trial — run
it with archiving enabled from iteration 1, verify the archive after the first few iterations,
and stop immediately if the round-trip fails. That is a smaller commitment than a full CI-NEB
and it closes the circularity honestly rather than by declaring the component done.

**This document does not open the gate.** It records that four of five condition-5 components
are validated and proposes how to close the fifth.
