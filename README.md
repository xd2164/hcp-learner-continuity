# HCP Learner Continuity

**One learner. Many AI applications. Continuous learning.**

This repository tests whether one open context layer, the
[Human Context Protocol (HCP)](https://github.com/loyalagents/hcp-spec), can carry a
learner's evidence from one AI application to another: what they have mastered,
what they are ready for next, and how they like to learn. Every hop is governed by
grants the learner controls. Each new product should not need its own integration
with each institution.

It runs two parallel demonstrations on the same infrastructure:

| | Track A: AI tutoring | Track B: Career navigation |
|---|---|---|
| Journey | Learning platform → HCP → Tutor A → Tutor B | University → HCP + learner wallet → Career app A → Career app B |
| Evidence | Assessment and mastery records | Institutional competencies and credentials |
| Status here | **Runnable demo on synthetic learners** | Interactive storyboard ([live](https://xd2164.github.io/hcp-learner-continuity/storyboard/)), [PRD](docs/track-b-storyboard-prd.md) and [design](docs/track-b-career-navigation.md) |

See [docs/vision.md](docs/vision.md) for the full argument and the investment question.

## The moment it demonstrates

> Tutor B knows what the learner has already mastered, and what they are ready to
> learn next, even though the learner has never used Tutor B before.

```
School record (issuer-attested credentials) ─┐
Practice system (model-inferred estimates) ──┼─► HCP Provider ──grant──► Tutor A
Learner's own statements (person-declared) ──┘        ▲                      │
                                                      └── new evidence ──────┘
                                     learner revokes A, grants B
                                                      │
                                                      ▼
                                                   Tutor B ── continues, no re-intake
```

## Quick start

Requires Python 3.10+ and nothing else (standard library only).

```bash
# 1. Check the demo provider against all 123 fixture scenarios
python -m hcp_demo.check_scenarios

# 2. Run Track A for the ten synthetic learners; writes reports/track-a/
python -m hcp_demo.track_a

# 3. Build the HTML view (docs/index.html; open it in a browser)
python -m hcp_demo.html_view

# 4. Tests
python -m unittest discover -s tests
```

**Interactive views:** Track A results at <https://xd2164.github.io/hcp-learner-continuity/>; the Track B storyboard at <https://xd2164.github.io/hcp-learner-continuity/storyboard/>. It has the cohort
chart, and you can follow any learner through the five steps. It is a single self-contained file
([docs/index.html](docs/index.html)) and works offline.

Results from the current fixture ([reports/track-a/](reports/track-a/README.md)):

- **123/123** fixture scenarios pass the access checks: correct errors for
  expired, revoked and out-of-scope requests, no `mustNotDisclose` entry ever
  returned, and eligible sets matching the fixture exactly.
- Across 10 learners, Tutor B needs **46 intake items with HCP versus 490 without**,
  and starts from 3 to 7 known learner preferences instead of none.
- In every case where Tutor A ran a session, Tutor B received Tutor A's new
  evidence, labelled as `model-inferred` with its confidence and source. Where
  that evidence said "secure", Tutor B confirmed with two items instead of
  re-teaching. Where it said "developing", Tutor B continued with a different
  approach.
- Support plans (IEP/504), purpose-restricted screeners, expired estimates and
  issuer-suspended credentials never reach either tutor.

The tutors are rule-based stand-ins and the session results are simulated. The
numbers show what the context makes possible, not measured learning gains. A pilot
replaces the stand-ins with real tutors and measured outcomes ([docs/track-a-tutoring.md](docs/track-a-tutoring.md)).

## Repository layout

```
data/understudy-seed-2368342781/   Understudy HCP bundles: 10 synthetic learners
                                   (exports, grants, scenarios, disclosures, manifest)
hcp_demo/provider.py               minimal in-memory HCP Provider (access decisions only)
hcp_demo/check_scenarios.py        scores the provider against the fixture scenarios
hcp_demo/tutors.py                 Tutor A, Tutor B and the cold-start counterfactual
hcp_demo/track_a.py                runs the five-step handoff and writes reports
hcp_demo/html_view.py              builds the self-contained HTML view (docs/index.html)
reports/track-a/                   generated per-learner and cohort reports
docs/                              vision, both tracks, data guide, HCP concept notes
tests/                             unit tests
```

## Important caveats

- **HCP is a working draft.** This repo follows 2.0-draft-3. Identifiers use the
  placeholder namespace `hcp.example`, and the wire format will change. The spec
  repository is in private partner review, so this repo links to it and does not
  copy its text.
- **The provider is not a conformant HCP implementation.** It has no HTTP or MCP
  binding, no tokens and no signature verification. It models the access
  decisions closely enough to pass the fixture's scenarios, which is what the
  demos depend on.
- **All data is synthetic.** It was generated by Understudy from seeded rules. No
  real student data and no PII. Issuer keys are public test keys. See
  `data/understudy-seed-2368342781/manifest.json`.
