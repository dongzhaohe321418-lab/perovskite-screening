#!/usr/bin/env python
"""Block 4 of E, the one evaluation of S2b: the tier block (results/objective2/s2/S2B_PLAN.md section 7, "Blocks",
item 4; E_IMPLEMENTATION_SPEC section 13). At the FR commit this file is the interface only: a stub with
BLOCK4_IMPLEMENTED = False whose every function raises NotImplementedError. It is specified and filled in before C3b
(S2B:532-533), with its self-tests T1-T5, and E's route() refuses every past-FR route while it is a stub (spec 6.1).

Fixed now, for the block-4 specification (spec section 13; S2B:356, 576, 649-650; P:771):
  dopants ("Sr", "Cl", "Cs", "GA"), decisive ("Cl", "Cs", "GA"), no Ca in any pool or ranking; C5 with FR
  (m_d >= 1, df_delta >= 3, |delta_bar_d| <= 50 meV, decision.FR.outcome == "pass"); a_far from delta_far(FA188) of
  block 2 only, never from Pb76; delta_Sr,m30 only from block 5's hinge quartet; the df_delta count by one committed
  function (OP-23); the ranking over the 6 pairs with Q_RANK = 0.9975; the labels L_A1TIER (with its bracketed clause
  iff block 2.5 is not 'none'), L_DOPANT* and L_SENS verbatim from S2B; the tier and c4b guard modes of e_guard.TABLE;
  INT-SHA of the private archives against <private_root>/<c>/MANIFEST.sha256.

Interface (called by e_eval.py only on routes past FR):
  tier_route(ctx)                    -> {"id": "C3B-STOP" | "C3B-NOTIER" | "C4B-NOTRUN" | "C4B-STOP" | "C4B-ENDED",
                                         "c3b": {...}, "c4b": {...}, "commits": {...}, "verify": {...}}
  c4b_df_delta_validity(ctx)         -> {"df_delta": int, "m_d": {...}, "units": [...], "function": str, "blob": str}
  build_tier_table(ctx, c1, fr)      -> an s2-evaltable-1-shaped production table (c3b hosts; c4b a2)
  evaluate_tier(table, fr, *, hinge=None) -> the A1 tier; the calibrated tier only with hinge (delta_Sr,m30)
  rows(result, labels)               -> the Rows of block 4
  manifest(ctx, c)                   -> {root-relative path: sha256} of a private archive (INT-SHA, RF-11)

Blinding. The stub reads nothing and computes nothing.

    (imported by e_eval.py; self-tests: e_selftest.py group T)
"""

BLOCK4_IMPLEMENTED = False
NOT_IMPLEMENTED = "block 4 is specified before C3b (S2B §7)"
DOPANTS = ("Sr", "Cl", "Cs", "GA")                   # spec 13: no Ca in any pool or ranking
DECISIVE = ("Cl", "Cs", "GA")
ROUTES = ("C3B-STOP", "C3B-NOTIER", "C4B-NOTRUN", "C4B-STOP", "C4B-ENDED")


def tier_route(ctx):
    raise NotImplementedError(NOT_IMPLEMENTED)


def c4b_df_delta_validity(ctx):
    raise NotImplementedError(NOT_IMPLEMENTED)


def build_tier_table(ctx, c1, fr):
    raise NotImplementedError(NOT_IMPLEMENTED)


def evaluate_tier(table, fr, *, hinge=None):
    raise NotImplementedError(NOT_IMPLEMENTED)


def rows(result, labels):
    raise NotImplementedError(NOT_IMPLEMENTED)


def manifest(ctx, c):
    raise NotImplementedError(NOT_IMPLEMENTED)
