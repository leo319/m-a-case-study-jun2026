# Context Checkpoint

Date: 2026-06-06

## User Goal

The user is an AI product manager at a hedge fund preparing a case-study response for `Nicholas_Kang_Case_Study_Brief.md`.

They want a critical review of the brief and help thinking through the design of tooling for merger-arbitrage analysis, especially:

- Whether the tool should be a web app with agentic workflows behind it or a repo/instruction-driven agent harness.
- Principles: transparency, guardrails, comprehensiveness, human-in-the-loop control, customization, and trustworthiness through evaluation.
- Regular documentation so another IDE/editor/agent can resume from this file.

## Brief Summary

The case asks for tooling that analyzes any merger along two dimensions:

1. Strategic and financial rationale.
2. Tail risks that could derail the deal.

The worked example is Cintas acquiring UniFirst, announced March 11, 2026. The tool must generalize beyond this transaction.

Deliverables:

- The tooling itself.
- An evaluation methodology and runnable evaluation results, including generalization to other deals.
- A write-up explaining design choices, evaluation, weaknesses, next steps, and the user's own judgment on Cintas/UniFirst.

Hard requirements:

- Every factual claim must be sourced.
- Reasoning must separate source-derived facts from model judgments/inferences.
- Source quality must be distinguished.
- Tail-risk citations must be real and verifiable.
- The system must not be hard-coded to Cintas/UniFirst.

## Initial Design Direction

The strongest response likely combines:

- A repo-based agent/evaluation harness as the core artifact.
- A lightweight analyst-facing UI or review surface only if time permits.
- Structured JSON outputs with claim-level citations, source quality labels, and fact-vs-inference separation.
- Human approval gates before major workflow stages.
- Deterministic citation/source validation and evaluation scripts.

The system should be positioned as a steerable analyst copilot, not an autopilot investment-decision engine.

## Open Work

- Decide exact architecture and artifact scope.
- Define schemas for deal inputs, claims, sources, analyst review states, risk records, and evaluation results.
- Decide whether to build a minimal UI, CLI, or both.
- Design evaluation methodology for judgment-heavy rationale analysis versus more verifiable tail-risk claims.
- Run or simulate the tool on the worked example and test deals.
