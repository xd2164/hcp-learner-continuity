# Track A: AI tutoring continuity

## Demonstration flow

| Step | What happens | In this repo |
|---|---|---|
| 1. Existing learner record | A synthetic student's knowledge, mastery history and gaps, mapped to standards (the learning-platform partner's knowledge graph in the pilot). | Understudy export: school-issued Open Badge credentials per standard, a mastery-frontier extract, assessments, practice estimates from a model, and the learner's own statements. |
| 2. Tutor A personalizes | Tutor A reads authorized context and targets the learner's frontier. | `plan_tutor_a`: picks the lowest not-yet-mastered standard, uses the learner's stated pacing, what helps and interests. |
| 3. New evidence | The learner practices; progress is written back to HCP with its source and permissions. | `run_session` writes a `model-inferred` practice estimate (medium confidence, validity window, rationale) under Tutor A's grant. |
| 4. Switch to Tutor B | The learner revokes Tutor A and grants Tutor B, an independent product. | Tutor A's next call gets `invalid-token`. Tutor B reads the updated context, including Tutor A's entry. |
| 5. Compare with and without HCP | Does Tutor B choose better practice, need less intake, and interpret prior evidence correctly? | `plan_cold_start` is Tutor B with no HCP. Reports compare intake, preference signals and continuity. |

## What Tutor B does with evidence it did not create

Tutor B treats context differently depending on who asserted it:

- **Issuer-attested** (a district's signed credential): taken as the baseline.
- **Model-inferred** (Tutor A's estimator, with confidence): newer and useful,
  but not authoritative. If it says "secure" on a standard the school record
  lists as not yet mastered, Tutor B confirms with two items rather than
  re-teaching or ignoring it.
- **Person-declared** (the learner's own words): shapes how to teach. Examples
  from the data: "can you explain what its asking first", "i only have about
  15 mins on school nights".

This is the protocol doing real work. Without provenance, a second tutor must
either trust everything or re-test everything.

## What Tutor B never receives

The access rules the fixture checks keep these out:

- support plans (IEP/504, intervention placements), which sit in a separate
  category the tutoring grant does not include;
- entries the learner restricted to other purposes (for example, an SEL screener
  limited to academic advising);
- expired practice estimates and credentials the issuer has suspended;
- anything after the grant is revoked;
- categories a standing rule denies to that operator.

Directives travel with the context: "Ask me before you sign me up for anything"
reaches Tutor B along with the entries it covers.

## Metrics

| Metric | How it's computed now | How a pilot would measure it |
|---|---|---|
| Intake burden | Diagnostic items needed before targeted practice (2 per unknown standard; with HCP only unassessed or to-be-confirmed standards) | Time to first targeted item; learner-reported effort |
| Appropriateness of first practice | Whether the first target is on the learner's frontier rather than already mastered | Expert rating; first-session accuracy in the productive band (60 to 85%) |
| Correct interpretation of prior evidence | Tutor B's handling of Tutor A's model-inferred estimate | Agreement between Tutor B's placement and a held-out assessment |
| Personalization | Count of learner preferences available | Learner and teacher ratings; engagement |
| Control | Zero `mustNotDisclose` disclosures; revocation enforced | Audit-log review; learner comprehension of grants |

## From demo to pilot

1. Replace the Understudy export with the learning-platform partner's synthetic records mapped
   to its knowledge graph (same HCP shape, so the provider and checker carry over).
2. Replace the rule-based tutors with two independently built tutors (for example,
   from two different tutoring providers), each calling a real
   HCP provider over the HTTP or MCP binding.
3. Run the with/without comparison on matched synthetic learners, then on
   consenting real learners under an IRB-style protocol.
4. Feed verified tutoring outcomes into the learner's wallet. This is where
   Track A meets Track B.
