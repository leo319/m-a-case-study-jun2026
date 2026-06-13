# Method cards — the first-principles spine for stages 2–4

Deal-agnostic M&A reasoning cards. They are the reusable knowledge of **what
fundamental business questions matter, and why** — applied to *this* deal at the
Plan stage and again at the Expert/Red-Team stages.

## Why these exist

The pipeline's failure mode is **checklist-driven research**: a fixed coverage
checklist asks the same questions of every deal, so the facts gathered are generic
and the inferences built on them are generic. These cards fix that *upstream*: at the
**Plan** stage the agent reasons from first principles about the specific deal and asks
"what does the checklist miss here?", producing deal-specific `key_questions` that drive
the rest of the run.

## First principles first — frameworks are servants, not masters

The principle: **reasoning is first-principles, not framework-driven.** The mechanical
application of a standard framework is a red flag, not an answer. So every card is
structured this way:

1. **First-principles trace** — build the picture from scratch by following the money:
   who is the customer and why do they pay, who is in the supply chain and where does power
   sit, how does one unit of value flow to cash, where does the profit pool form.
2. **Framework prompts** — *then* reach for Porter / VRIO / Damodaran etc. **only to
   pressure-test the trace** — adapt or discard the prompts that don't fit this business,
   and say which. A framework you can't justify applying, you drop.

The named frameworks are a checklist to confirm you didn't miss something — never the path
to the insight.

## The card schema (every card has these blocks)

- **The why it answers** — the core question, one sentence.
- **Grounded in** — the framework(s) + source the prompts draw on.
- **First-principles trace** — the from-scratch questions; do these first.
- **Framework prompts** — the adaptable checklist to test the trace.
- **Facts to gather (→ research)** — the sourceable facts this analysis needs. These become
  research mandate, so they ride the fail-closed rails (every fact → a verified claim).
- **Inferences to form (→ expert)** — the judgments to build *from* those facts, each
  grounded on verified claims (the "Our view" blocks in the memo).
- **Weak-answer tells** — what a shallow / framework-jammed / empire-building answer looks like.

The two middle output blocks are the point: **`facts to gather` feeds `claims.jsonl`;
`inferences to form` feeds the memo's "Our view" judgments.** That bridge is what turns a
question into grounded analysis.

## The cards

| # | Card | Bucket | Grounded in |
|---|---|---|---|
| 00 | First principles — trace the business | (meta, always) | First-principles — hypothesis-free, custom logic |
| 01 | Industry structure & economics | Industry | Porter Five Forces · Value Chain · industry life cycle |
| 02 | Company position & competitive advantage | Companies | VRIO / Resource-Based View |
| 03 | Deal mechanism & synergies | Deal / combination | Value-chain overlap · Damodaran synergy |
| 04 | Macro & exogenous forces | Macro | PESTEL-style scan |
| 05 | Why this deal, why now | Synthesis / "what's off" | Strategic vs financial buyer · consolidation endgame |

## How the cards wire into the pipeline

- **Plan stage (source-plan)** loads cards 00–05 to generate deal-specific `key_questions`
  beyond the static checklist. The questions persist in `source_plan.json` and render in
  `source_plan.md` for the analyst gate.
- **Research** hands each area its `key_questions` as additional mandate (alongside the
  checklist subtopics), so the right facts get gathered.
- **Expert** loads the cards, builds the "why" from the first-principles trace, and answers
  the `key_questions` — especially card 05 ("why this deal").
- **Red-Team** hunts `key_questions` and "whys" the memo left unanswered, tries to close each
  from the verified fact base, and relegates anything unclosable to a **Limitations** section.

Cards are **deal-agnostic** — they ask the agent to *derive* the economics of whatever
industry the deal is in (uniform rental, freight rail, streaming, …), never to hardcode one.
