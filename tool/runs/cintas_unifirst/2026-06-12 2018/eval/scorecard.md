# Eval report — cintas_unifirst / 2026-06-12 2018

_Independent verification of the **120** claims the memo surfaced (99 facts, 21 inferences), judged against the cached source snapshot by `opus-4-8`._

## Summary

| Tier | Metric | What it asks | Score | What failed |
|---|---|---|---|---|
| **Primary** | **Precision** | Does the citation resolve, is the quote present, and does it actually support the statement? | 95.0% (94/99) | antitrust_4, target_fundamentals_3, operational_integration_7, commercial_market_20, antitrust_13 |
| | &nbsp;&nbsp;↳ Fabrication rate | Citation dead or absent. | 0.0% (0/99) | — |
| | &nbsp;&nbsp;↳ Misattribution rate | Resolves and quoted correctly, but doesn't support the statement. | 5.1% (5/99) | antitrust_4, target_fundamentals_3, operational_integration_7, commercial_market_20, antitrust_13 |
| | **Inference validity** (entailment) | Are the supports verified, and does the conclusion follow? | 90.5% (19/21) | ex_wearers, deal_rationale_synergies_6 |
| **Secondary** | Separation discipline | No opinion dressed up as fact. | 100.0% (21/21) | — |
| | Coverage | Checklist areas with a verified claim. | 83.3% (10/12) | Macro & geopolitical, ESG / environmental |
| | Utilization | Did the memo use what it found? | 35.2% (76/216) | 27 verified research inference(s) unused |
| | Fact / insight recall (gold set only) | Did we surface the material facts and reach the key judgments? | n/a | requires a gold set; none provided for this run |

Independent verification flagged 5 misattribution(s), 2 weak inference(s) among the surfaced claims — each needs fixing or dropping before sign-off (see the ledger below).

## Ledger — per-claim verdicts

_Every surfaced claim, re-judged INDEPENDENTLY against its own cached source snapshot (reproducible). Failures are listed first._

**Verdict meanings** — **PASS** (grounded & entailed) · 🔴 **FABRICATION** (citation dead/missing or quote absent) · **MISATTRIBUTION** (quote present but statement not supported by it) · **WEAK-INFERENCE** (conclusion doesn't follow its supports) · **DISCIPLINE** (opinion-as-fact / broken fact-inference separation).

| claim_id | type | verdict | cited source | offending span | reason |
|---|---|---|---|---|---|
| antitrust_13 | fact | MISATTRIBUTION | s_antitrust_precedent_aramark | ~$1.0bn acquisition of uniform/linen rental peer | FTC notice confirms only Aramark/AmeriPride txn 20180159 granted Dec 22 2017 (early termination = no second request); source never establishes ~$1.0bn deal size nor that AmeriPride is a uniform/linen rental peer — those descriptors are unsupported by the cited source |
| antitrust_4 | fact | MISATTRIBUTION | s_defm14a_regulatory | the deadline at which the FTC issued its Second Request | quote establishes the refiling HSR expiry of June 11 2026 11:59 p.m. but does NOT establish that the FTC issued its Second Request at/on that deadline; appended clause is not supported by the cited span |
| commercial_market_20 | fact | MISATTRIBUTION | s_defm14a_opinion | the second precedent transaction | Aramark/AmeriPride (Oct 2017) is the THIRD transaction listed after Cintas/G&K (Aug 2016) and Elis/Lavebras (Dec 2016); the quote confirms the deal exists but does not establish it is 'second' |
| operational_integration_7 | fact | MISATTRIBUTION | s_unf_10k | about one-fifth the size of Cintas's ~22,900-vehicle fleet | cited source (UniFirst 10-K) only establishes UniFirst's 4,813-vehicle fleet; the Cintas ~22,900-vehicle figure and the one-fifth comparison appear nowhere in this source |
| target_fundamentals_3 | fact | MISATTRIBUTION | s_unf_10k | its facilities include a 325,000 square foot Owensboro, Kentucky distribution center plus almost all of its industrial laundry processing plants | quote establishes only the 62% garments-manufactured figure; the 325,000 sq ft Owensboro DC and laundry-plant facility assertions are not established by the cited quote |
| deal_rationale_synergies_6 | inference | WEAK-INFERENCE | deal_rationale_synergies_1,deal_rationale_synergies_5 | post-dates Cintas's publicly-disclosed Jan 2025 $275 approach, so the unaffected baseline may already embed takeover speculation | premium math (102.5%) follows, but the Jan 2025 $275 approach and the takeover-speculation conclusion are a new fact not grounded in either support (support_5 ties $153.05 only to the Nov 11 2025 director-nomination disclosure) |
| ex_wearers | inference | WEAK-INFERENCE | custmix_1,custmix_2,custmix_3 | The strikingly low ~4 uniform-wearers-per-customer ratio | the ~4 wearers-per-customer ratio appears in no support; new figure smuggled into the premise and the route-density-not-account-size conclusion overreaches what supports license |
| antitrust_10 | fact | PASS | s_antitrust_precedent | — | quote present; 45-50% share and 'only Vestis as viable national alternative' both in cited span |
| antitrust_11 | fact | PASS | s_antitrust_precedent | — | quote present; HHI 800-1000 in quote, 3-to-2/Big Three/35%+14% in adjacent cited context |
| antitrust_12 | fact | PASS | s_antitrust_precedent_gk | — | quote present; Jones Day source confirms closed Mar 21 2017 no divestitures, eight-month FTC/Canadian probe, two of four largest, $2.2bn |
| antitrust_8 | fact | PASS | s_ion_ftc_competitors | — | quote present; statement (source's view that finding divestiture buyers may be challenging) entailed by the quoted span |
| antitrust_9 | fact | PASS | s_ion_ftc_competitors | — | quote present; S&P downgrade to B Dec 2025 plus 'unlikely buyer'/'not really capable of growth' in cited span |
| commercial_market_11 | fact | PASS | s_aramark_vestis_8k | — | quote present; press release context confirms completed spin-off, holds uniform/workplace supplies business, now independent public company, and VSTS regular-way trading Oct 2 2023 |
| commercial_market_13 | fact | PASS | s_vestis_10k | — | verbatim quote present; statement faithfully attributes the 'second largest provider' assertion to Vestis with same basis |
| commercial_market_14 | fact | PASS | s_vestis_10k | — | verbatim quote present; all figures (~$2.7bn revenue, $64.4M op income/2.4%, $40.2M net loss/(1.5)%) entailed |
| commercial_market_16 | fact | PASS | s_vestis_10k | — | verbatim quote present; statement entailed by the risk-factor span on rental revenue declines |
| commercial_market_2 | fact | PASS | s_cintas_fy25_er | — | quote present; total revenue 10,340,181 (+7.7%) and Uniform rental 7,976,073 vs 7,465,199 confirmed in income statement; ~77% share holds |
| commercial_market_22 | fact | PASS | s_cintas_gk_pr | — | full source confirms $97.50, ~$2.2bn EV incl net debt, ~19% premium to Aug 15 2016 close, $130-140M synergies realized in fourth full year |
| commercial_market_23 | fact | PASS | s_cintas_gk_pr | — | full source confirms $130-140M annual synergies 'projected to be realized in their entirety in the fourth full year after closing' |
| commercial_market_24 | fact | PASS | s_cintas_pr_2025_proposal | — | source: $275/sh proposal, ~$5.3bn total value, 46% premium to 90-day avg as of Jan 6 2025, delivered to Board Nov 8 2024 — all entailed |
| commercial_market_25 | fact | PASS | s_cintas_pr_2025_proposal | — | source states $255/sh IOI Feb 7 2022 at 43% premium, and rejections Nov 27 2024 and again Dec 9 2024 without/refusing further engagement — statement entailed |
| commercial_market_26 | fact | PASS | s_merger_pr_2026 | — | source: $155 cash + 0.7720 shares = $310 combined at $200.77 Mar 9 2026 close, ~$5.5bn EV, 8.0x run-rate TTM EBITDA incl ~$375mm synergies — entailed |
| commercial_market_4 | fact | PASS | s_cintas_fy25_er | — | operating income $2.36B/$2.07B/14.1% in quote; $10.34B revenue and 22.8% margin confirmed in source context window |
| commercial_market_5 | fact | PASS | s_cintas_10k | — | quote present verbatim; statement paraphrases the Item 1 overview self-description accurately |
| commercial_market_6 | fact | PASS | s_cintas_10k | — | quote present verbatim; 48,300 employee-partners and 900 union-represented entailed |
| commercial_market_7 | fact | PASS | s_cintas_10k | — | quote present; full Competition paragraph in context window supports local/fragmented plus national, regional, local, retailer and online competitor enumeration |
| commercial_market_8 | fact | PASS | s_cintas_10k | — | quote present verbatim; no customer over one percent of total revenue entailed; low concentration is fair restatement |
| commercial_market_9 | fact | PASS | s_unf_10k | — | quote present; industry described highly competitive and principal competitors Cintas, Alsco, Vestis confirmed in context |
| costnat_1 | fact | PASS | s_unf_10k | — | quote present for the rental cycle; source separately states cost of revenues comprises amortization of rental merchandise, labor, production, service and delivery costs, supporting the cost-composition framing |
| costnat_2 | fact | PASS | s_unf_10k | — | quote present; energy/labor inflation disclosure entailed by Risk Factors span |
| custmix_1 | fact | PASS | s_cintas_10k_cust | — | quote present; over one million businesses of all types from small to major corporations entailed by Customers span |
| custmix_2 | fact | PASS | s_cintas_10k_cust | — | quote present; ~95% route-servicing revenue statement entailed by the revenue recognition span |
| custmix_3 | fact | PASS | s_unf_10k_cust | — | quote present verbatim; 'all sizes / no customer >10% of revenue' in context entails the broad, non-concentrated base |
| deal_rationale_synergies_1 | fact | PASS | s_cintas_pr_deal | — | quote present; $310/share, ~$5.5B EV and 'two family-founded companies' all entailed by the quoted span and its immediate context |
| deal_rationale_synergies_11 | fact | PASS | s_defm14a_opinion | — | quote present; 8.0x-10.0x EV/2026E Adj. EBITDA and $147.00-$182.00 range entailed by quoted span and surrounding context |
| deal_rationale_synergies_12 | fact | PASS | s_defm14a_opinion | — | quote present; 11.7x-14.2x FV/LTM EBITDA and $215.50-$260.00 implied range entailed by quoted span and context |
| deal_rationale_synergies_13 | fact | PASS | s_defm14a_opinion | — | quote present; 7.50%-8.50% discount, PV as of Feb 28 2026, $193.00-$266.50 all entailed by quoted span |
| deal_rationale_synergies_14 | fact | PASS | s_defm14a_opinion | — | quote present; 9.0% discount = CAPM estimate of cost of equity and $160.00-$218.00 illustrative PVs entailed by quoted span and context |
| deal_rationale_synergies_15 | fact | PASS | s_defm14a_opinion | — | cached source confirms GS applied 11.7x-14.2x EV/LTM adj EBITDA as of Feb 26 2026 to derive $216.00-$260.00; statement entailed |
| deal_rationale_synergies_18 | fact | PASS | s_defm14a_opinion | — | quote present; 21%-59% illustrative premia on $153.05 (Nov 11 2025) deriving $185.00-$243.00 entailed by quoted span |
| deal_rationale_synergies_2 | fact | PASS | s_unf_424b3 | — | quote present for $155 + 0.7720; 'exchange ratio is fixed and will not be adjusted... stock price' verified verbatim elsewhere in the same 424B3 source |
| deal_rationale_synergies_3 | fact | PASS | s_unf_424b3 | — | 424B3 Q&A: ~14,261,683 Cintas shares as stock consideration, ~3.4% fully diluted as of Apr 16 2026 — entailed |
| deal_rationale_synergies_4 | fact | PASS | s_cintas_pr_deal | — | quote present; $155 cash + 0.7720 x $200.77 = $310.00 entailed by quoted span |
| deal_rationale_synergies_5 | fact | PASS | s_defm14a_opinion | — | quote present; $153.05 unaffected price (Nov 11 2025, day prior to nomination disclosure) vs $310.00 consideration entailed verbatim |
| deal_rationale_synergies_7 | fact | PASS | s_cintas_pr_deal | — | quote present verbatim; statement is a faithful restatement of the $375M synergy bullet |
| deal_rationale_synergies_9 | fact | PASS | s_cintas_pr_deal | — | quote present in PR transaction-benefits; EPS accretion by end of second full year stated verbatim |
| ex_antitrust | inference | PASS | antitrust_4,antitrust_10,antitrust_11,antitrust_12,antitrust_13,antitrust_9,antitrust_18 | — | supports verified; Second Request + ~45-50% share + favorable base rate + impaired Vestis support the localized-divestiture-with-real-tail conclusion |
| ex_close | inference | PASS | whycintas_17,management_governance_6,merger_agreement_20,merger_agreement_4,antitrust_17,antitrust_18,antitrust_4 | — | all supports verified; balanced more-likely-than-not-conditioned-on-remedy synthesis follows from the pro/con supports |
| ex_fundamentals | inference | PASS | target_fundamentals_4,target_fundamentals_6,short_activist_4,operational_integration_9,antitrust_4 | — | supports verified; flat revenue, ~1/3 margin, activist gap thesis, multi-year route contracts under a multi-quarter Second Request support the deterioration-during-pendency conclusion |
| ex_governance_vote | inference | PASS | management_governance_3,management_governance_6,management_governance_24 | — | all supports verified; low vote-risk-on-related-party-footing conclusion follows from >2/3 control + support agreement + activist entrenchment dynamic |
| ex_integration | inference | PASS | supplychain_16,operational_integration_12,operational_integration_14,operational_integration_21,operational_integration_9 | — | all five supports verified; above-normal integration/execution risk conclusion follows from different supply models, IT weakness, mid-flight ERP, multi-year contracts and retention risk |
| ex_lever | inference | PASS | synmech_1,synmech_5,synmech_6,synmech_10,synmech_18,operational_integration_1 | — | supports verified (63.4% CoR, 23.2% SG&A, route fleet, overlapping route networks); $375M-from-these-lines plausibility conclusion follows |
| ex_margin_gap | inference | PASS | target_fundamentals_6,commercial_market_4,management_governance_10,management_governance_15 | — | supports verified; 7.6% vs 22.8% gap, activist 12.8%->6.4% case, ISS endorsement all grounded |
| ex_overpay | inference | PASS | deal_rationale_synergies_19,deal_rationale_synergies_21,financing_18 | — | supports verified; price-above-standalone + synergy-dependent value + back-end-loaded accretion support the overpayment-risk conclusion |
| ex_premium | inference | PASS | deal_rationale_synergies_19,deal_rationale_synergies_20,deal_rationale_synergies_5 | — | supports verified; price above all method highs and 102.5%/36 = 2.85x median both follow from supports |
| ex_profit_engine | inference | PASS | synmech_6,synmech_1,synmech_18,custmix_2,operational_integration_8,operational_integration_3 | — | supports verified; route-based fleet + dominant local-delivery/processing/merchandise cost lines + 83.8%/95% route-servicing revenue license the route-density per-stop economics conclusion |
| ex_supplychain | inference | PASS | supplychain_1,supplychain_3,supplychain_10,supplychain_11,supplychain_17,operational_integration_12 | — | all supports verified; opposite-supply-model / captive manufacturing / inherited tariff + IT-stack conclusion follows from the supports |
| ex_synergy_test | inference | PASS | deal_rationale_synergies_19,deal_rationale_synergies_21,deal_rationale_synergies_22,synmech_11,synmech_17,synmech_13,synmech_15 | — | supports verified; price>standalone, 8.0x incl synergies, ex-synergy higher, G&K base rate all follow |
| ex_whynow | inference | PASS | whycintas_17,whycintas_18,whycintas_15,commercial_market_30,management_governance_23 | — | supports verified; scarcity/persistence read follows from ~4yr/5-approach pursuit, $255->$275->$310, three-player field, weakened Vestis |
| financing_13 | fact | PASS | s_cintas_s4 | — | quote present in S-4; ~$2.8B additional / ~$5.44B consolidated / greater than current all entailed |
| financing_14 | fact | PASS | s_cintas_s4 | — | quote present; 5% assumed rate on $2.8B Permanent Debt Financing entailed (the $2.8B is established in adjacent context) |
| financing_15 | fact | PASS | s_cintas_s4 | — | S-4 states Cintas/UniFirst shareholders hold ~96.6% / 3.4% of Cintas common stock immediately following the mergers — exact match |
| financing_2 | fact | PASS | s_cintas_pr_deal | — | press release: net leverage ratio at close expected to be 1.5x debt to EBITDA — exact match |
| financing_3 | fact | PASS | s_cintas_pr_deal | — | quote present in deal press release; EPS accretion by end of second full year entailed |
| financing_5 | fact | PASS | s_cintas_pr_deal | — | press release states fully committed bridge financing from Morgan Stanley Senior Funding, KeyBank N.A. and Wells Fargo Bank N.A. — exact match |
| litigation_11 | fact | PASS | s_ctas_8k_vote | the vote cleared without any disclosed merger-objection litigation or mooting supplemental disclosure | load-bearing fact (June 12 approval) entailed; the negative clause is a reasonable status characterization of the cited deal 8-K, which discloses no such litigation |
| litigation_3 | fact | PASS | s_unf_10k | — | quote present for Q1 FY2025 partial favorable ruling; the authority's subsequent appeal ('federal tax authority appealed the determination of the Federal Tax Court') confirmed in same Note in source |
| litigation_5 | fact | PASS | s_cintas_10k | — | quote present verbatim; 10-K Legal Proceedings/Note 15 context entails the additional non-ordinary-course litigation statement |
| litigation_8 | fact | PASS | s_defm14a | — | quote present; 'no pending lawsuits challenging the mergers as of date hereof' entailed (demand letters noted in context are not lawsuits) |
| management_governance_10 | fact | PASS | s_engine_prec14a | — | quote present verbatim; 12.8%->6.4% ~50% drop vs Cintas margin expansion entailed exactly |
| management_governance_6 | fact | PASS | s_defm14a | — | verbatim quote present; two-thirds voting power and expected approval subject to V&S agreement entailed by context |
| management_governance_9 | fact | PASS | s_engine_prec14a | — | verbatim quote present; Engine's deeply-disappointing-TSR-across-every-period assertion entailed by quoted span |
| merger_agreement_10 | fact | PASS | s_unf_defm14a | — | quote present; Company-side MAE bring-down since Aug 30, 2025 matches Sec 3 rep |
| merger_agreement_11 | fact | PASS | s_unf_defm14a | — | quote present; Parent-side MAE bring-down since May 31, 2025 matches Sec 4.7 rep |
| merger_agreement_12 | fact | PASS | s_unf_defm14a | — | quote present; no-shop restriction on solicit/seek/facilitate/discuss entailed |
| merger_agreement_14 | fact | PASS | s_unf_defm14a | — | quote present; specific-performance non-opposition covenant entailed by Sec 8.10 |
| merger_agreement_17 | fact | PASS | s_unf_defm14a | — | verbatim quote present; $350M reverse termination fee + obligation to litigate antitrust challenges entailed exactly |
| merger_agreement_18 | fact | PASS | s_unf_defm14a | — | quote present; $350M reverse fee cap and two four-month extensions on 10-month date entailed |
| merger_agreement_2 | fact | PASS | s_unf_8k_20260311 | — | quote present; $213.3M target fee and $350M reverse fee both stated verbatim |
| merger_agreement_4 | fact | PASS | s_unf_defm14a | — | DEFM14A: Cintas' obligation to complete the mergers is not conditioned upon obtaining financing — exact match |
| merger_agreement_6 | fact | PASS | s_unf_defm14a | — | DEFM14A Regulatory Matters: mergers conditioned on expiration/termination of any HSR waiting period — exact match |
| merger_agreement_7 | fact | PASS | s_unf_defm14a | — | quote present; statement entailed by the Other Approvals span (foreign antitrust + permits conditions) |
| merger_agreement_8 | fact | PASS | s_unf_defm14a | — | quote present; verbatim restatement that shareholder approval is required for completion |
| merger_agreement_9 | fact | PASS | s_unf_defm14a | — | quote present; NASDAQ listing condition entailed by quoted span |
| operational_integration_1 | fact | PASS | s_cintas_10k | — | quote present verbatim; 12,100 routes, 478 facilities, 12 distribution centers at May 31 2025 entailed |
| operational_integration_10 | fact | PASS | s_unf_10k | — | quote present; Mexico plants and 325,000 sq ft Owensboro KY DC also confirmed verbatim in same source; statement entailed |
| operational_integration_11 | fact | PASS | s_cintas_10k | — | quote present verbatim; 'sources from many outside suppliers + five manufacturing facilities' entails the more-outsourced characterization |
| operational_integration_12 | fact | PASS | s_unf_10k | — | quote present; ITGC material weakness on manage change/manage access stated; 'unremediated' supported by 'if not remediated' and prior-year carryover in context |
| operational_integration_14 | fact | PASS | s_unf_10k | — | quote present for ERP initiated FY2022 through 2027; $45.3 million capitalized in fiscal 2025 confirmed in same Key Initiatives section of source |
| operational_integration_21 | fact | PASS | s_unf_424b3 | — | quote present verbatim in merger-risk-factors; key-person/retention risk entailed |
| operational_integration_8 | fact | PASS | s_unf_10k | — | quote present; 83.8% route-servicing revenue figure verbatim from Revenue Recognition note |
| operational_integration_9 | fact | PASS | s_unf_10k | — | quote present; three-to-five-year written service contracts entailed; attrition-as-non-renewal framing is a fair gloss |
| rt_divestiture_synergy | inference | PASS | antitrust_18,antitrust_10 | — | supports verified; localized-overlap divestiture theory + 45-50% local shares support that a remedy cuts into the overlapping route density driving the synergy |
| rt_family_flip | inference | PASS | management_governance_18,whycintas_18,management_governance_23,management_governance_24 | — | supports verified; conclusion (sale under activist pressure at higher price, not loss of control) follows from defeated slate + $310 vs $275 |
| rt_financing_risk | inference | PASS | merger_agreement_21,financing_19,merger_agreement_14 | — | supports verified; no-financing-condition + specific-performance + unsecured $2.8B permanent debt yield the low-but-nonzero conclusion |
| rt_synergy_magnitude | inference | PASS | deal_rationale_synergies_21,synmech_17,synmech_14,synmech_15,financing_3 | — | supports verified; 2.0x op income, 24% cost of rev, yr2 accretion vs yr4 run-rate all follow |
| short_activist_10 | fact | PASS | s_engine_dfan_proxyadvisors | — | full source confirms ISS/Glass Lewis/Egan-Jones all recommend FOR Ajdler and M. Croatti on BLUE card at Dec 15 2025 annual meeting |
| short_activist_11 | inference | PASS | short_activist_1,short_activist_2,short_activist_3,short_activist_4,short_activist_5,short_activist_7 | — | supports verified; activist-not-short thesis (mismanagement under family control, sale as path) reinforces acquirer narrative, follows |
| short_activist_4 | fact | PASS | s_engine_prec14a | — | quote present; statement restates Engine's assertion under 'A Sale Represents the Best Path Forward', conclusion supported by surrounding context |
| supplychain_3 | fact | PASS | s_unf_10k_fy2025 | — | quote present verbatim; statement is a faithful restatement of the manufacturing/sourcing span |
| supplychain_6 | fact | PASS | s_unf_10k_fy2025 | — | quote present verbatim in Item 1A risk factors; statement entailed by the quoted span |
| synmech_1 | fact | PASS | s_unf_10k_fy2025 | — | quote present; $1,542.4M / 63.4% of revenues verbatim from MD&A cost-of-revenues table |
| synmech_11 | fact | PASS | s_ctas_pr_20260311 | — | quote present verbatim; ~$5.5B EV / 8.0x EBITDA incl. ~$375M synergies entailed; 'interested-party-asserted / embedded in multiple' faithful gloss |
| synmech_4 | fact | PASS | s_unf_10k_fy2025 | — | quote present; source explicitly states amortization expense is included in cost of revenues on the Consolidated Statements of Income |
| synmech_5 | fact | PASS | s_unf_10k_fy2025 | — | quote present; $565.1M / 23.2% of revenues verbatim from MD&A SG&A table |
| synmech_9 | fact | PASS | s_ctas_10k_fy2025 | — | quote present; SG&A composition statement entailed verbatim by significant-accounting-policies span |
| target_fundamentals_1 | fact | PASS | s_unf_10k | — | quote present for 'over 300,000 customer locations in the U.S., Canada and Europe'; 'leading provider' is a generic Item 1 self-descriptor consistent with the 10-K |
| target_fundamentals_10 | fact | PASS | s_unf_10k | — | 91.2% Uniform & Facility Service Solutions share verbatim in quote |
| target_fundamentals_11 | fact | PASS | s_unf_10k | — | First Aid segment $114,586/$106,271/8,315/7.8% match quote; 4.7% share confirmed in source context window |
| target_fundamentals_12 | fact | PASS | s_unf_10k | — | quote present; 4.7% of revenues for First Aid & Safety Solutions in fiscal 2025 entailed by disaggregated-revenue table |
| target_fundamentals_13 | fact | PASS | s_unf_10k | — | quote present; Other 99,204 vs 97,130, +2,074 (2.1%) matches MD&A revenues-by-segment table |
| target_fundamentals_14 | fact | PASS | s_unf_10k | — | U.S. $2,245.9M, Europe/Canada $186.5M, and 3-year totals all match quoted geographic revenue table |
| target_fundamentals_2 | fact | PASS | s_unf_10k | — | quote present; 16,000 persons (team partners) and <1% U.S. unionized both entailed by quoted span |
| target_fundamentals_4 | fact | PASS | s_unf_10k | — | revenue figures and 0.2% match quote; 53rd-week note confirmed in source context window |
| target_fundamentals_5 | fact | PASS | s_unf_10k | — | operating income $184,498/$183,578/$920/0.5% match quote exactly |
| target_fundamentals_6 | inference | PASS | target_fundamentals_4,target_fundamentals_5 | — | 184.5/2432.4 = 7.58% ~7.6% follows from verified supports (source itself states 7.6% margin); Cintas ~22% conservative and verified elsewhere |
| target_fundamentals_9 | fact | PASS | s_unf_10k | — | segment revenue $2,218,562/$2,224,030/$(5,468)/0.2% match quote; 91.2% confirmed in same filing |
| whycintas_11 | fact | PASS | s_defm14a | — | Feb 8 2026 $310 mix-TBD quote verbatim; same source confirms Cintas viewed $275 as 'full and fair' price, so $35-above framing is grounded |
| whycintas_15 | fact | PASS | s_unf_10k_fy2025 | — | quote present verbatim; 'principal competitors include [three named]' entails the three-name scarcity statement |
| whycintas_8 | fact | PASS | s_defm14a | — | quote present verbatim in DEFM14A Background; statement entailed by the quoted span |
