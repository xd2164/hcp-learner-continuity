import unittest
from pathlib import Path

from hcp_demo import track_a
from hcp_demo import tutors as T
from hcp_demo.check_scenarios import check_bundle
from hcp_demo.provider import Provider, load_json, ts

BUNDLE = Path(__file__).resolve().parent.parent / "data" / "understudy-seed-2368342781"
LEARNERS = sorted((BUNDLE / "learners").iterdir())


class FixtureConformance(unittest.TestCase):
    def test_every_scenario_passes(self):
        passed, total, failures, _ = check_bundle(BUNDLE)
        self.assertEqual(passed, total, "\n".join(failures))
        self.assertGreater(total, 100)


class TrackA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = [track_a.run_learner(d) for d in LEARNERS]

    def test_tutor_b_receives_tutor_a_evidence(self):
        for r in self.results:
            if r["tutorA"]["session"]:
                self.assertTrue(r["hcp"]["tutorBSawTutorAEvidence"], r["learner"]["id"])

    def test_revoked_tutor_a_is_refused(self):
        for r in self.results:
            self.assertEqual(r["hcp"]["tutorAAfterRevocation"], "invalid-token")

    def test_hcp_never_increases_intake(self):
        for r in self.results:
            m = r["metrics"]
            self.assertLessEqual(m["intakeItemsWithHCP"], m["intakeItemsWithoutHCP"])

    def test_deterministic(self):
        again = track_a.run_learner(LEARNERS[0])
        self.assertEqual(again, self.results[0])

    def test_tutor_b_never_sees_what_tutoring_must_not(self):
        # Anything the fixture says a tutoring client must not see stays hidden
        # from the new Tutor B too (support plans, purpose-restricted entries).
        for d in LEARNERS:
            sc = [s for s in load_json(d / "scenarios.json") if s["id"] == "tutor-open-query-excludes-support-plans"][0]
            p = Provider.from_bundle(d)
            hidden = set()
            for eid in sc["expect"]["mustNotDisclose"]:
                e = p.entries[eid]
                restricted = e["classification"].get("permittedPurposes")
                # Operator-specific standing rules aimed at the fixture's own tutor
                # do not apply to Tutor B, so only test the operator-independent cases.
                if not set(e["classification"]["categories"]) & set(T.TUTOR_CATEGORIES) or (restricted and T.TUTORING not in restricted):
                    hidden.add(eid)
            g = p.issue_grant(client=T.TUTOR_B, access=T.tutoring_access(["read"]), at=track_a.GRANT_B)
            ctx = T.read_context(p, g["grantId"], T.TUTOR_B, track_a.READ_B)
            self.assertFalse(hidden & set(ctx.disclosed_ids), d.name)


class ProviderRules(unittest.TestCase):
    def setUp(self):
        self.p = Provider.from_bundle(LEARNERS[0])
        self.g = self.p.issue_grant(client=T.TUTOR_A, access=T.tutoring_access(["read"]), at=track_a.GRANT_A)

    def test_write_requires_write_action(self):
        with self.assertRaises(PermissionError):
            self.p.create(self.g["grantId"], categories=[T.PROFILE], dimension="x", value="y",
                          declaration_type="person-declared", at=track_a.SESSION_A, purpose=T.TUTORING)

    def test_unknown_purpose_is_scope_denied(self):
        r = self.p.query(self.g["grantId"], {"query": "q", "purpose": "https://example/marketing"}, track_a.SESSION_A)
        self.assertEqual(r.error, "scope-denied")

    def test_before_issue_is_invalid(self):
        r = self.p.query(self.g["grantId"], {"query": "q", "purpose": T.TUTORING}, ts("2026-01-01T00:00:00Z"))
        self.assertEqual(r.error, "invalid-token")


if __name__ == "__main__":
    unittest.main()
