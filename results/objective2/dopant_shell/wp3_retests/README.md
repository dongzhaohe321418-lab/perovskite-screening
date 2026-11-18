# WP3 re-tests V1, V1b, V2 and V3: files

The note is `WP3_RETESTS.md`; its section 10 lists the files of this directory.

Published on 2026-11-18 from the analyst's working directory, with these changes and no other:

- Absolute paths in logs, command files, scripts and in the `model` fields of the json files are replaced by the
  placeholders `<repo>` (this repository), `<wp3_retests>` (this directory), `<project>`, `<home>` and `<env>` (the
  Python environment with mace-torch 0.3.16). Line numbers are unchanged. `eval_v1.py`, `traj_v3.py` and the
  `diag_*.py` scripts are therefore records of what ran; `eval_retests.py` is the relocatable evaluator.
- The model files, the checkpoints and the debug logs are not in the repository. The sha256 of each selected model
  is in section 2 of the note.
- `V1_LOG.md` is the analyst's running log of the four re-tests, as written, corrections included.
