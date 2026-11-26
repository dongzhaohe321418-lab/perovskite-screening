# S3a: evaluation record of the hinge read

**Status: EVALUATION RECORD (S3a).** This file opens the evaluation of the pre-registration
`results/objective2/s2/S3A_HINGE_PLAN.md`. It is added in a commit after the one that fixed that note. When this
record was written no hinge value had been read by the project.

## 1. The rules that bind the read

- Note: `results/objective2/s2/S3A_HINGE_PLAN.md`
- Last commit that changed it: `b6bacd4eb90afd01529174b6dcb439f63d7d9d08` (2026-11-26T17:00:36Z)
- git blob id: `31e922cdc6304d319949f4e83536ab08b14c6e1e`
- sha256: `d230f70a40bf0e7a06ca613a1e5949b0eafd6f68f18fead013eea91dbe9577c4`

## 2. The command (section 8 step 4 of the note)

```
python -B -I results/objective2/s2/s2b/e_eval.py --hinge --hinge-cause prereg --prereg results/objective2/s2/S3A_HINGE_PLAN.md --prereg-eval results/objective2/s2/S3A_HINGE_EVAL.md --private-root <private root>
```

Standard output is captured to a file outside the working tree. The parser of the readings,
`results/objective2/s2/s3a/s3a_read.py`, is added in the commit of this record with the output of its self-test on
invented texts (`s3a/s3a_read_selftest.txt`).

## 3. Pre-flight conditions (section 8 step 3 of the note)

Their results are appended below, in a later commit that changes only this file, before the run.

1. A full clone with the objects of `8bff03e`; HEAD at the commit that adds this record or at a later commit that
   changes only this record; `git status --porcelain --untracked-files=all` empty.
2. `s2b/E_output.txt` in the working tree is the committed public copy (sha256 `30804fef…afb5`), with one adding
   commit; the unedited file is kept outside the working tree.
3. No hinge output file and no hinge figure source data exist.
4. `scripts/46` to `50` and E's eight tools are unchanged since `e5883d5`; `C3B_NOTE.md` and the verify records are
   committed and clean; the parser lives outside `s2b/`.
5. `c1/`, `c2/` and `fr/` show no difference from `98bb606`.
6. The private root holds the c3b archive whose manifest hash is the line of `C3B_NOTE.md`; no c3 or c4b entry in
   either root.
7. `--prereg` and `--prereg-eval` are repository-relative paths; this record contains the note's path character
   for character (section 1).
8. The interpreter of E's attempt 1: Python 3.12.16, numpy 2.5.4, scipy 1.18.1, ase 3.29.0.
