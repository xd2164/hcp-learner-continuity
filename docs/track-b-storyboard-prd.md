# PRD: Track B storyboard: a university learner's journey from assessment evidence to AI advising

**Status:** Draft for feasibility review
**Track:** B (career navigation) of HCP Learner Continuity
**Deliverable:** an interactive storyboard that walks one synthetic university learner through five stages, backed by real data structures, so partners can see the flow and judge whether to build it.

---

## 1. Summary

A university learner's evidence today lives in separate places. Assessment results sit in the university's systems, skill estimates sit inside whatever model produced them, credentials sit in a wallet, and goals and preferences sit in the learner's head or in an advisor's notes. Each AI advising tool has to rebuild the picture from scratch.

This PRD covers a storyboard that shows the alternative, one stage at a time:

```
University assessment evidence ─► Inference engine ─► Learner wallet ─► HCP context ─► University advising agent
 (what the learner did)     (what they probably know)  (what they    (what they want,   (3 controlled inputs
                                                        can prove)    and who may see it) → 3 outputs)
```

The core design idea: **the advising agent receives three kinds of evidence, each labelled by how it is known, and the learner controls each one.**

| Input | Source | How it is known (HCP declaration type) | Learner control |
|---|---|---|---|
| **What I can prove** | Verifiable achievements in the learner wallet, issued by the university | `issuer-attested`, cryptographically verifiable | Choose which credentials to present |
| **What I probably know** | The inference engine's P(Known) competency estimates | `model-inferred`, with confidence and expiry | Grant or withhold; restrict to purposes |
| **What I want** | The learner's goals, constraints, preferences | `person-declared` | Edit, revoke, set directives |

The agent produces three outputs. Each one cites which inputs it used:

1. **Next best learning action:** what to study next, and whether the learner is ready to attempt an assessment.
2. **Pathway guidance:** roles or programs that match the learner's goals, with the specific skill gaps to each.
3. **Learner-approved write-back:** an updated plan saved to the learner's HCP context, and optionally a shareable skills summary. Nothing is saved or shared without the learner's confirmation.

---

## 2. Why this is valuable

| For | Value | How the storyboard shows it |
|---|---|---|
| **Learner** | No re-explaining themselves to every tool. Advice grounded in what they have actually done. Control over what each service sees. | Side-by-side "with HCP / without HCP" intake; a revoke button that visibly cuts access. |
| **University** | Advising that scales without a pairwise integration per tool. Assessment evidence keeps working for the learner after they leave a course. Clear provenance for any recommendation. | One protocol call replaces N integrations. Every recommendation traces back to a university assessment. |
| **Employers and career services** | Verified skills instead of self-reported résumés, with honest uncertainty where evidence is inferred. | The pathway output separates "proven" from "likely" skills. |
| **Ecosystem and funders** | Evidence that one interoperable layer can serve many AI learning applications, and that the same infrastructure works for both K-12 tutoring (Track A) and adult career navigation. | The same HCP access model and checker as Track A, with a new issuer and vocabulary. |

**The key safeguard, shown explicitly:** an inference never becomes a credential. The inference engine's P(Known) stays `model-inferred`. Only the university's assessment outcomes become wallet credentials. That keeps "verified" meaning verified, which is what makes the credentials worth anything to an employer.

---

## 3. Goals and non-goals

**Goals**
- G1. Make the five-stage flow understandable to a non-technical audience in under five minutes.
- G2. Back every screen with realistic data structures (Open Badges 3.0 credentials, HCP entries and grants, P(Known) records), so engineers can judge feasibility from the same artifact.
- G3. Show learner control working: grant, purpose restriction, revoke, ask-first directive.
- G4. Show the value counterfactual: the same advising agent with and without HCP context.
- G5. Produce a feasibility verdict per stage (what exists, what to build, what to confirm with partners).

**Non-goals (for this phase)**
- Live integration with the university's, the inference engine's or the wallet's production systems.
- Real learner data. Everything is synthetic.
- A production advising agent. The agent in the storyboard is scripted or rule-based, with an optional LLM mode clearly labelled.
- Choosing who operates the HCP Provider (see open question Q1).

---

## 4. Persona (synthetic)

**Dana**, 34, works full time in IT support and is enrolled in a university bachelor's program in cloud computing. Dana studies about 8 hours a week, mostly on weekends, and wants to move into a cloud security role within 18 months. Dana has passed several competency assessments, is partway through others, and has used two different career tools that each asked for the same résumé and self-assessment.

---

## 5. The journey, stage by stage

Each stage is one storyboard frame. Every frame has three panels:
- **Learner view:** what Dana sees.
- **System view:** what happens and between which parties.
- **Under the hood:** the actual data artifact, collapsible.

### Stage 0: Consent and onboarding

| | |
|---|---|
| **Scene** | Dana connects their university account to a context service and sees, in plain language, what will be shared, with whom, and for what purpose. |
| **System** | An HCP Provider is set up for Dana. The university is granted *write* access for the `education_learner_profile` category under the purpose "keep your academic record in your context". No one has *read* access yet. |
| **Artifact** | Grant record: client = University records service, actions = write, purpose = school-records. |
| **Learner control shown** | Dana can see the grant list and revoke any entry on it. |
| **Acceptance** | Dana can name, in a comprehension check, who can write and who can read. |

### Stage 1: University assessment evidence

| | |
|---|---|
| **Scene** | Dana completes an objective assessment on network security fundamentals and a performance task (a lab write-up). The timeline shows each attempt and its result. |
| **System** | The university records the outcomes: pass or not-yet, the competencies each item covers, and timestamps. These are the raw evidence for both the inference engine (stage 2) and the credential (stage 3). |
| **Artifact** | Assessment-result record: competency IDs (skill descriptors), item-level correctness, attempt number, outcome, evaluator type (scored or rubric). |
| **Value** | This is the most trusted evidence in the chain. Everything later traces back to it. |
| **Feasibility** | **To confirm with the university:** which result fields can be exported, at what granularity (item-level or competency-level), and how competencies are identified (Rich Skill Descriptors or internal IDs). |
| **Acceptance** | Every downstream recommendation in the storyboard links back to at least one stage-1 record. |

### Stage 2: Inference engine

| | |
|---|---|
| **Scene** | Dana sees a competency map. Each competency shows "likely known" as a probability with a plain-language band ("very likely", "developing", "not enough evidence"), and why. |
| **System** | The inference engine consumes stage-1 evidence and returns P(Known) per competency, a knowledge-tracing-style estimate of mastery that updates with each attempt. These are written to HCP as `model-inferred` entries. Each entry carries the probability, a confidence band, the evidence it drew from, the model version, and an expiry date (estimates go stale). |
| **Artifact** | HCP entry: `declarationType: model-inferred`; `confidence: high/medium/low` (mapped from P(Known) and evidence count); `content.value: {competency, pKnown: 0.87, attempts: 12, modelVersion}`; `basis.rationale`; `validUntil`. |
| **Key rule** | P(Known) is never turned into a credential. It informs readiness ("you are likely ready to attempt the assessment"). It is not proof. |
| **Value** | Gives advising a forward-looking view (what Dana is close to mastering) that pass/fail records cannot. |
| **Feasibility** | **To confirm with the inference engine:** the input format it needs, its output schema, whether it reports uncertainty or only point estimates, update latency, and the model-versioning policy. Proposed mapping to the HCP confidence bands: high = P ≥ 0.90 with 5 or more observations; medium = P 0.70–0.90, or fewer observations; low otherwise. Calibrate the thresholds with the inference engine. |
| **Acceptance** | Each estimate shows its probability, its band, the evidence it used and its expiry. Expired estimates disappear from the advising agent's view. |

### Stage 3: Verified achievement in the learner's wallet

| | |
|---|---|
| **Scene** | Dana passes the assessment. A credential arrives in their learner wallet: "Network Security Fundamentals: Competent", issued by the university. Dana can view it, verify it, and choose whether to share it. |
| **System** | The university issues an Open Badges 3.0 / W3C Verifiable Credential to Dana's wallet, with a status-list entry so it can be revoked or suspended later. When Dana presents it into HCP, it becomes an `issuer-attested` entry with the credential as evidence. |
| **Artifact** | `OpenBadgeCredential` with issuer DID, `achievement.id` = competency descriptor, `credentialStatus` (BitstringStatusList), proof. The Track A fixture already uses exactly this structure for K-12 standards. |
| **Value** | A portable, verifiable achievement that outlives the program and is meaningful to employers. |
| **Feasibility** | Mostly proven. Learner wallets that support Open Badges 3.0 / VC issuance and presentation exist today. Track A shows VC-backed HCP entries, including suspension. **To confirm:** the university's issuance path (direct to the wallet, or through an existing achievement-wallet program) and the presentation flow from the wallet to the HCP Provider. |
| **Acceptance** | The credential verifies in the storyboard (signature and status). Suspending it in the demo removes it from the advising agent's next read. |

### Stage 4: HCP context assembly

| | |
|---|---|
| **Scene** | Dana opens "My context" and sees three groups: *What I can prove* (credentials), *What I probably know* (estimates), *What I want* (goals, constraints, preferences). Dana adds a goal ("Cloud security role within 18 months") and a constraint ("about 8 hours a week, mostly weekends"), and sets a directive: "Ask me before you share my profile with an employer." |
| **System** | The HCP Provider holds all three kinds of entry with provenance. Dana issues the advising agent a *read* grant under the purpose `academic-and-career-advising`, covering credentials, estimates and goals. Sensitive categories (accommodations, financial aid, demographics) are not included. |
| **Artifact** | Grant with access blocks per category; the directive (`action: share`, `effect: ask-first`); `person-declared` entries for the goal and constraint. |
| **Learner control shown** | Toggle any category off and the agent's inputs change live. Revoke the grant and the agent's next request returns `invalid-token`. |
| **Value** | One place where Dana governs what any advising service sees, instead of a separate consent screen for every product. |
| **Feasibility** | **Demonstrated** for the access model: the repo's provider passes all 123 Track A fixture scenarios covering grants, purposes, expiry, revocation, standing rules and directives. New categories and purposes are configuration. |
| **Acceptance** | Every disclosure is logged and visible to Dana in an audit view. No excluded category ever appears in the agent's input. |

### Stage 5: University advising agent (three controlled inputs → three outputs)

| | |
|---|---|
| **Scene** | Dana asks: "What should I do next to get to cloud security?" The agent answers in three parts, each with a "why" that names its sources. |
| **Input 1: proven** | Credentials from stage 3 (`issuer-attested`). Treated as established. |
| **Input 2: likely** | P(Known) estimates from stage 2 (`model-inferred`). Weighted by confidence and never stated as fact. |
| **Input 3: wanted** | Goals, constraints and preferences from stage 4 (`person-declared`). Shapes priorities and pacing. |
| **Output 1: next best learning action** | "You're likely ready for the identity and access management assessment (P(Known) 0.91, high confidence). Two short practice sets first fit your weekend schedule." |
| **Output 2: pathway guidance** | "Cloud security analyst roles typically ask for 6 competencies. You have proven 3, are likely strong in 1, and have gaps in 2: incident response and security automation." Each item is marked proven, likely or gap. |
| **Output 3: learner-approved write-back** | "Save this plan to your context?" On confirmation, the plan is written to HCP as a `model-inferred` entry by the agent, with provenance. "Share a skills summary with an employer?" This triggers Dana's ask-first directive and requires explicit approval. |
| **Value** | Advice that is specific, honest about uncertainty, and grounded in evidence, with zero intake questions. |
| **Feasibility** | A scripted or rule-based agent is straightforward. It mirrors Track A's tutors, which already weigh evidence by declaration type. An LLM-backed agent is feasible, but needs guardrails: it must cite entry IDs for every claim, and it must not upgrade "likely" to "proven". Add an evaluation for this. |
| **Acceptance** | Every claim in the output links to the entries it used. No `model-inferred` input is presented as verified. Nothing is written or shared without Dana's confirmation. |

### Stage 6 (the payoff): Switching to Career app B

| | |
|---|---|
| **Scene** | Dana tries an independent career-navigation service. Instead of uploading a résumé, Dana grants it a temporary read. It starts from the same three inputs, plus university advising agent's saved plan, which is labelled as another service's inference. |
| **Value** | This is the portability proof. A second, independently built service benefits from context it did not create, through the same protocol, without a pairwise integration. |
| **Comparison shown** | With HCP: intake questions ≈ 0, and the first recommendation is on Dana's actual gaps. Without: a résumé upload, a self-assessment, and generic recommendations. |

---

## 6. Storyboard interface requirements

**Format:** a single-page web app in the same style as the existing Track A view (self-contained, works offline, light and dark themes, accessible).

**Layout**
- A top **stage rail** with stages 0–6 as numbered steps, showing progress; each stage is clickable.
- A main area with three panels per stage: **Learner view** (left, mock product UI), **System view** (centre, an animated flow showing which party sends what to whom), and **Under the hood** (right, collapsible JSON with key fields highlighted).
- A persistent **"Dana's controls"** drawer: grants list, category toggles, revoke button, directives, audit log.

**Interactions**
- R1. Step forward and back with Next and Back buttons, the arrow keys, or the stage rail.
- R2. A **With / without HCP** toggle on stages 5 and 6 that shows the cold-start version side by side.
- R3. Changing a control in the drawer (for example, turning off "What I probably know") re-runs the agent and visibly changes the outputs and their citations.
- R4. Revoking the advising grant makes the agent's next request fail, with the error shown.
- R5. Suspending the credential (an issuer action in the demo) removes it from the next read, and the agent's output downgrades that skill from "proven".
- R6. Every output sentence is hoverable to show its source entries.
- R7. A **presenter mode**: large type, one panel at a time, and speaker notes per stage.

**Data:** a synthetic university fixture in the same bundle shape as Track A (export, grants, scenarios with eligible, relevant and must-not-disclose sets), so `check_scenarios.py` validates it.

---

## 7. Feasibility assessment

| Component | Exists today | To build | Confidence | Owner / confirm with |
|---|---|---|---|---|
| HCP access model (grants, purposes, revocation, directives, audit) | Yes, in this repo; 123/123 fixture scenarios | New categories and purposes for career advising | High | Us |
| VC-backed HCP entries with status lists | Yes, in the Track A fixture | University issuer profile, competency descriptors | High | Us, with the university |
| Synthetic university learner fixture | No | Generator for assessment results, credentials, goals and scenarios | High | Us (ideally via Understudy) |
| Inference-engine P(Known) to HCP entry mapping | No | Adapter plus a confidence-band calibration | Medium: depends on the inference engine's output schema | Inference-engine partner |
| Wallet issuance and presentation | Supported by Open Badges 3.0 / VC wallets | Wallet → HCP presentation flow | Medium to high | Wallet partner, university |
| University assessment-result export | Unknown | Field mapping; sample (synthetic) export | **Unknown, the biggest dependency** | University |
| Advising agent, scripted | No (Track A tutors are the template) | Rules for the three outputs, with citations | High | Us |
| Advising agent, LLM | No | Prompting plus a citation guardrail and an "likely ≠ proven" evaluation | Medium | Us |
| Storyboard UI | Pattern exists (Track A HTML view) | Stage rail, three panels, controls drawer | High | Us |

**Verdict:** a storyboard backed by synthetic data is feasible now, with no partner dependencies. Live integration depends on three partner confirmations: the university's assessment export, the inference engine's output schema, and the wallet-to-HCP presentation path.

---

## 8. Success metrics

**For the storyboard (Phase 0)**
- The university, wallet and inference-engine partners each confirm their stage is represented accurately, or list the corrections.
- Non-technical viewers can explain the three inputs and the learner's controls after one walkthrough.
- `check_scenarios.py` passes 100% on the university fixture, with zero must-not-disclose leaks.

**For a pilot (later phases)**
- Intake questions before the first relevant recommendation, with vs without HCP.
- Expert-rated recommendation fit, blind to condition.
- Rate of the agent stating inferred skills as verified: target 0.
- Learner comprehension of grants and trust in the advice, by survey.
- Time to integrate a second advising service (the interoperability claim).

---

## 9. Phased plan

| Phase | Scope | Rough effort |
|---|---|---|
| **0. Storyboard** | Synthetic university fixture; stages 0–6; scripted agent; controls drawer; with/without toggle | 2–3 weeks, 1 to 2 people |
| **1. Partner-shaped data** | Replace synthetic structures with sample exports from the university and the inference engine, and real wallet test credentials (still synthetic learners) | 3–4 weeks after the partners provide samples |
| **2. Sandbox integration** | Live calls to the inference engine's and the wallet's test environments; an HCP Provider over the HTTP or MCP binding; an optional LLM agent with the citation guardrail | 6–8 weeks |
| **3. Pilot** | Consenting learners, under an appropriate research and privacy review | Design with the university |

---

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Inferences mistaken for credentials | Separate visual treatment; declaration type on every item; an evaluation that fails any output upgrading "likely" to "proven" |
| P(Known) miscalibrated, or overconfident on sparse evidence | Show the observation count; confidence bands require a minimum number of observations; estimates expire |
| HCP is still a draft and its wire format will change | Keep the storyboard at the data-model level; isolate the wire format in one adapter |
| Too many consent screens overwhelm the learner | A single "My context" surface; sensible default purposes; plain-language summaries |
| Sensitive data creeping into advising | Category-level exclusion by default; must-not-disclose scenarios in the fixture; audit view |
| Partner data not available | Phase 0 needs none; the fixture defines the shape partners can map to |

---

## 11. Open questions

- **Q1.** Who operates the HCP Provider for a university learner: the university, the wallet (wallet as provider), or a third party? This affects audit, revocation and trust.
- **Q2.** Should the inference engine write its estimates to HCP directly (as a client with a write grant), or should the university relay them?
- **Q3.** Which competency identifiers are shared across the university, the inference engine and career services, and is a crosswalk needed?
- **Q4.** What are the default grant lengths for advising: persistent for university advising agent, temporary for third-party career apps?
- **Q5.** Should the advising agent's saved plan be shareable onward (to Career app B), and under what directive?
- **Q6.** What does "three controlled inputs → three outputs" mean to the university team? This PRD proposes proven / likely / wanted → next action / pathway / write-back. Confirm or revise.

---

*All personas and data in the storyboard are synthetic. Partner capabilities marked "to confirm" are assumptions to be validated with the partners, not statements of what their systems do today.*
