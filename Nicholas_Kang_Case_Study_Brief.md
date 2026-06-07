# Merger Arbitrage Analyst — Case Study

**The deal (worked example):** Cintas (NASDAQ: CTAS) is acquiring UniFirst (NYSE: UNF), announced March 11, 2026.

- Cintas 424B3: https://www.sec.gov/Archives/edgar/data/0000723254/000114036126020376/ny20069194x3_424b3.htm

---

## Your task

Build **tooling — skills, agents, or prompt systems — that analyses a merger along two distinct dimensions:**

1. **Strategic & financial rationale** of the deal
2. **Tail risks** that could derail the deal

Use Cintas/UniFirst as the worked example, but the tooling must work on **any deal**, not just this one. Whether you build one system that does both or two separate tools is your call. 

You are highly encouraged to use any AI tools or harnesses as you see fit to assist you in this project.

You will deliver three things.

### 1. The tooling

Information source: Public filings of the companies (sec filing, investor presentations), news channels, analyst reports, trade magazines etc.

**1a. Strategic & financial rationale.**

- **Strategic logic** — what type of deal this is (e.g. horizontal consolidation, capability acquisition, geographic expansion) and the specific strategic drivers. "Creates a leading platform" is not an answer; what concretely changes for the buyer? Are there structural reasons which are forcing a merger, or threats from emerging competitors? Be skeptical about the strategic rationale proclaimed by the parties, most deals are simply empire building.
- **Financial rationale** — is the deal likely accretive or dilutive; how the consideration is structured and financed; whether the stated synergies are large or small relative to the premium paid.
- **Synergy credibility** — the stated synergies are management's number. Is that number plausible, and on what basis?
- **Deal risks** — what could undermine the thesis from the deal's own terms and economics (integration, execution, financing, synergy shortfall). The few that matter, not a generic list.

**1b. Tail risks.** Surface the risks that could derail the deal. Research **both the target and the acquirer** (acquirer-side problems can sink a deal too) across, at minimum: litigation and regulatory actions, short-seller or activist reports, macro or geopolitical risks, consumer/product complaints, management and shareholder controversies, and anything that creates antitrust, financing, or reputational exposure to *this* deal. Typically, the kind of tail risks that derail the deal is one which dramatically reduces the strategic or financial rationale for the deal - for example an unexpected deterioration of the target's business fundamentals. For each risk, state why it matters to the merger — not just that it exists.

Hard requirements on both outputs:

- **Inspectable reasoning.** A reader must be able to tell, for every claim, whether it is a *fact drawn from a source* or the *tool's own judgment/inference*. Make that separation explicit, however you choose to represent it.
- **Sourced facts.** Every factual claim traces to where it came from — filing section and figure for rationale; a real, verifiable URL/document for tail risk. Unsourced numbers and unverifiable risks are defects. (Fabricated or dead citations are the single worst failure here — guard against them.)
- **Source quality.** Especially for tail risk: a court filing is not a random blog post. Distinguish them.
- **Generalization.** Running it on a different deal should require feeding it that deal's inputs — not rewriting the tool. Avoid hard-coding anything specific to Cintas/UniFirst into the logic.

Note that the guidance given above is merely a starting point and is not exhaustive. You are encouraged to use your business acumen and engineering capability to expand the tool's capability.

### 2. The evaluation

Design a way to **test and evaluate the tooling**, covering **both** dimensions, plus the results of running it.

- **Does it work?** On what basis do you claim the output is correct, not just fluent and plausible? Note that the two dimensions are verifiable in different ways — a rationale judgment has no clean answer key, whereas a tail-risk claim can be checked against whether the underlying source actually exists and says what's claimed. Your evaluation should reflect that difference.
- **Does it generalize?** Show it running on deals beyond Cintas/UniFirst (see test deals below). Does quality hold up, or degrade?
- **Where does it fail?** Find and document the failure modes — don't hide them. What kinds of deals, filings, or claims break it? For tail risk specifically: how often does it fabricate or misattribute, and how do you measure that?

How you evaluate these — particularly the judgment dimension, which has no simple answer key — is up to you. The design of your evaluation is itself a large part of what we're assessing. We should be able to re-run it and get the same verdict.

**Test deals** (use as you see fit)

- Paramount's acquisition of Warner Bros. Discovery
- Union Pacific's acquisition of Norfolk Southern
- Skyworks' acquisition of Qorvo

### 3. The write-up

- How the tool works and the key design decisions you made.
- Your evaluation methodology and what it actually showed — including the weaknesses you found.
- What you would build next with more time.
- **Your own view:** do you agree with what your tooling concluded about Cintas/UniFirst — on both the rationale and the tail risks? Where would you overrule it, and why?

---

## What matters

- **Analytical thinking** — separating fact from inference, sizing what matters, and naming what could break the thesis.
- **Business acumen and financial competency** — how well you understand business and finance will determine how well you expand the capabilities of the tool, guide it to focus on the correct questions, and provide the correct analysis.
- **Engineering skills and AI leverage** — turning a fuzzy judgment task into a tool that generalizes, and *proving* it works rather than asserting it. Your design of guardrails for accurate, consistent outputs, as well as scaffolding or pipeline that can tackle complex tasks. Deterministic scripts that act as hooks, or JSON schemas that enforce consistency of outputs, are examples of engineering decisions.

## Submitting

A single folder or repo: the tool, the evaluation and its outputs, and the write-up, with brief instructions to run it.
