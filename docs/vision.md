# Vision: one learner, many AI applications

## The problem today

Each tutor, institution and career-navigation application understands only a
fragment of the learner. Every new product starts with intake: placement tests,
questionnaires, "tell me about yourself". Every new partnership needs another
bespoke integration with each institution's systems.

## The aspiration

Learning evidence generated in one environment can support the learner in
another. Shared meaning makes this possible, along with trusted sources and
control by the learner.

- **Shared meaning:** evidence is tied to common frameworks (standards,
  competencies, a knowledge graph), so a second application interprets it the
  same way as the first.
- **Trusted sources:** every piece of context says who asserted it and how. It
  might be a school's signed credential, a model's estimate with a confidence,
  or the learner's own words. Each application can weigh them differently.
- **Learner control:** applications receive context only under grants the learner
  (or guardian) issues, for stated purposes, and those grants can be revoked.
  Sensitive categories stay out unless granted explicitly.

## The test

Can a shared, open context infrastructure enable this across two quite
different educational journeys?

**Shared infrastructure:** institutional learning records, a knowledge graph,
HCP, and a wallet the learner controls.

### Track A: AI tutoring

Learning platform → HCP → AI Tutor A → AI Tutor B

A learner switches tutors without losing their mastery history,
misconceptions or learning progress. Potential partners: a learning-platform
partner with a knowledge graph, and AI tutoring providers. Details: [track-a-tutoring.md](track-a-tutoring.md).

### Track B: Career navigation

University → HCP + learner wallet → Career app A → Career app B

A learner carries verified skills, achievements and career goals across
independent advising services. Potential partners: a competency-based
university, a workforce-learning partner, and independent career-navigation providers. Details: [track-b-career-navigation.md](track-b-career-navigation.md).

## How the two tracks reinforce each other

|                     | AI tutoring                            | Career navigation                          |
| ------------------- | -------------------------------------- | ------------------------------------------ |
| Primary goal        | Better personalized learning           | Better personalized pathways               |
| Source of evidence  | Assessment and mastery records         | Institutional competencies and credentials |
| HCP contribution    | Portable learning context              | Portable skills, goals and experience      |
| Wallet contribution | Optional for the initial tutoring demo | Important for verified achievements        |
| What it shows       | Two tutors sharing learning continuity | Two career services using portable skills  |
| Outcome to test     | Learning relevance and progress        | Recommendation quality and reduced intake  |

A learner wallet is not required for the first tutoring demo. It
would add complexity without showing more value to the learner. It becomes useful
once verified tutoring outcomes feed into a broader learner record, which is
where the two tracks meet.

## Sequencing

1. **Tutoring first.** A learning-platform partner already has a prototype that turns
   synthetic records into HCP, so this is the nearest-term demonstration. This
   repo runs that handoff end to end on the Understudy fixture.
2. **Career navigation next.** It connects institutional achievements to
   credentials the learner holds and to AI services.

The progression is: **personalized tutoring → accumulated learning evidence →
portable skills and achievements → lifelong career navigation.**

## The investment question

> Can one interoperable infrastructure layer enable many kinds of AI learning
> applications, rather than requiring a new integration for every product and
> institution?

What would count as evidence:

- A second, independently built application uses context it did not create,
  and does better because of it (less intake, more appropriate next steps).
- It does this through the same protocol calls the first application used, with
  no pairwise integration.
- The learner's controls (grants, purposes, revocation, sensitive-category
  exclusions) hold at every hop and can be audited.
