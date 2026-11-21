# Track B: Career navigation (design)

Status: design. Not yet runnable. No institutional fixture exists for this
track yet, and building one is step 1 below.

## Journey

University → HCP + learner wallet → Career app A → Career app B

A learner carries verified skills, achievements and career goals across
independent advising services. The second service gives better recommendations
with less intake, because it starts from evidence the learner already holds.

## Why it reuses Track A's infrastructure

The Track A fixture already shows the pattern Track B needs. In it, institutional
achievements are W3C Verifiable Credentials (Open Badges 3.0) carried as
`issuer-attested` HCP entries, with status lists for revocation and suspension.
Career navigation changes the issuer and the vocabulary, not the mechanism.

| Track A (K-12 tutoring) | Track B (career navigation) |
|---|---|
| District issues an `OpenBadgeCredential` per CCSS standard | The university issues credentials per competency or course (Open Badges 3.0 / CLR 2.0) |
| Standards as `classification.dimension` | Competencies and skills (for example, Open Skills Network / RSD URIs) as dimensions |
| Learner statements: what helps, pacing | Learner statements: career goals, constraints (location, schedule, pay) |
| Practice system's `model-inferred` estimate | Career app A's inferred skill gaps or fit scores, with confidence |
| Tutoring grant, `tutoring` purpose | Advising grant, `career-advising` purpose, often temporary |
| Support plans excluded by category | Sensitive data excluded by category: disability accommodations, financial aid, demographic data |

## Where the wallet fits

In Track B the learner holds the credentials in a learner wallet and
presents them. The HCP Provider records them as entries whose evidence is the
presented credential. Applications therefore get both a portable, verifiable
achievement and governed, purpose-bound context around it (goals, preferences,
inferred gaps). Neither the wallet nor HCP alone provides both.

Open question for the partners: does the wallet act as the HCP Provider, or as
a source the provider imports from? It affects who runs the audit log and where
revocation is enforced.

## Demonstration flow

1. **Institutional record.** A synthetic university learner with completed competencies,
   credentials and transcript-level data.
2. **Wallet.** The credentials are issued to the learner's wallet and
   presented into HCP as `issuer-attested` entries.
3. **Career app A.** It reads skills and goals under a temporary advising grant,
   recommends a pathway, and writes `model-inferred` skill-gap entries.
4. **Career app B.** An independent service gets a new grant and continues from
   the verified skills and app A's inferred gaps, without re-collecting a
   résumé or self-assessment.
5. **Compare.** Recommendation quality (expert-rated fit), intake questions
   avoided, and whether app B interprets app A's inferences with the right weight.

## Build plan

1. **Fixture.** Generate synthetic adult learners in the Understudy bundle shape
   (export, grants, scenarios with eligible, relevant and `mustNotDisclose`).
   Ideally do this through Understudy, so the same checker validates it.
2. **Provider reuse.** Run `hcp_demo/check_scenarios.py` on the new bundle. The
   access logic carries over; new categories and purposes are configuration.
3. **Career apps.** Add `career.py`, mirroring `tutors.py`: A recommends and writes
   gaps; B continues; the cold-start counterfactual asks for a résumé.
4. **Wallet integration.** Replace fixture credentials with credentials issued to
   and presented from a test wallet.

## Open questions

- Competency framework alignment between the university, the knowledge graph and the career
  apps' skill taxonomies. Is a crosswalk needed, or a shared skills registry?
- Grant duration for advising. The fixture's advisor grant is temporary and
  expires within hours. Is that the right default for career services?
- Which HCP categories should Track B define, and should they be proposed
  upstream as an extension of the Education Context profile?
