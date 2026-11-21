# The Understudy fixture

`data/understudy-seed-2368342781/` is an Understudy cohort export: 10 synthetic
learners (grades K to 10, seven states), each converted to HCP 2.0-draft-3
context. Learner statements use sentence frames, so the bundle is byte-for-byte
reproducible from its seed. The bundle's own [README](../data/understudy-seed-2368342781/README.md)
and `manifest.json` (parameters, counts, SHA-256 of every file) are the
authoritative description.

Per learner (`learners/<SYN-id>/`):

| File | Contents | Used by |
|---|---|---|
| `export.json` | HCP export: entries, superseded versions, standing rules, directives, delegation (guardian), audit log | provider |
| `grants.json` | Every grant (school records, student portal, practice system, tutor, advisor, summer program) with its status | provider |
| `scenarios.json` | Queries with timestamps and expected outcomes: `eligibleEntryIds`, `relevantEntryIds`, `mustNotDisclose`, error codes | checker |
| `reads.json`, `disclosure-summary.json`, `sharing-reports.json` | What each client was given; onward sharing | reference |
| `understudy-record.json` | The synthetic school record the HCP context was made from | reports (name, grade, school) |

Kinds of entry in a typical learner:

- **issuer-attested** (about 80%): Open Badge 3.0 credentials per standard
  ("CCSS 8.NS.A.1: Exceeds Mastery"), plus record extracts for mastery frontier,
  assessments, course progress, attendance, EL status and work habits. They are
  signed by the district's `did:key` and carry status-list entries.
- **model-inferred**: practice-system estimates per standard, with confidence,
  validity window and rationale.
- **person-declared**: the learner's own statements (interests, activities,
  difficulty, what helps, pacing, goals).

Scenario coverage per learner: math mastery, missing work, an open query that
must exclude support plans, a request that names a category it was not granted,
a purpose the grant does not allow, advisor queries before and after the grant
expires, a narrowed grant, a standing rule, a purpose-restricted entry, and use
after revocation.

To regenerate or extend: use the Understudy HCP record tool (a cohort download of
up to 25 learners in the UI, or `npm run hcp-bulk-export -- --count 200 --seed 42`
in its `backend/`). Drop the new bundle under `data/` and pass its path to
either script.
