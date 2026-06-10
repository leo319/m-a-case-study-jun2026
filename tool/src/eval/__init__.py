"""Live independent verification eval (eval #2).

A STANDALONE quality harness — NOT part of merger-run. It takes a finished run,
re-derives the set of claims the memo actually surfaced (cited via [[id]] tokens),
and has an independent verifier judge EACH surfaced claim against its OWN cached
source snapshot — fact precision, fabrication, misattribution, inference validity,
and fact/inference separation discipline.

See eval_run.py for the plan -> verify -> aggregate -> dashboard flow.
"""
