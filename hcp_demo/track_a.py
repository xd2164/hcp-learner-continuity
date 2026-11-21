"""Track A: one learner, two independent AI tutors, continuity through HCP.

    1. Start from the learner's existing record (Understudy export in HCP).
    2. The learner grants Tutor A; Tutor A reads context and personalizes.
    3. Tutor A runs a session and writes new evidence back to HCP.
    4. The learner revokes Tutor A and grants Tutor B, which has never met them.
    5. Tutor B continues from the updated context. Compare with Tutor B cold.

Usage:  python -m hcp_demo.track_a [bundle_dir] [--out reports/track-a]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import tutors as T
from .provider import Provider, iso, load_json

DEFAULT_BUNDLE = Path(__file__).resolve().parent.parent / "data" / "understudy-seed-2368342781"

# Demo timeline (after the fixture's own scenarios, which end 2026-07-01).
GRANT_A = datetime(2026, 7, 6, 16, 0, tzinfo=timezone.utc)
SESSION_A = datetime(2026, 7, 6, 16, 30, tzinfo=timezone.utc)
REVOKE_A = datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc)
GRANT_B = datetime(2026, 7, 20, 18, 5, tzinfo=timezone.utc)
READ_B = datetime(2026, 7, 20, 18, 10, tzinfo=timezone.utc)

MINUTES_PER_ITEM = 1.5


def why_withheld(p: Provider, entry: dict, at: datetime, disclosed: set[str], client: dict) -> str | None:
    if entry["id"] in disclosed:
        return None
    cats = set(entry["classification"]["categories"])
    if not cats & set(T.TUTOR_CATEGORIES):
        return "category not in the tutoring grant (e.g. support plans)"
    denied = p.denied_categories(client, at) or set()
    if cats <= denied:
        return "a standing rule set by the learner or guardian"
    permitted = entry["classification"].get("permittedPurposes")
    if permitted and T.TUTORING not in permitted:
        return "restricted by the learner to other purposes"
    if not p.entry_active_at(entry, at):
        st = entry["record"]["status"]
        return "suspended or revoked by the issuer" if st in ("suspended", "revoked") else "expired"
    return "eligible, not needed for these questions"


def run_learner(learner_dir: Path) -> dict:
    student = load_json(learner_dir / "understudy-record.json")["student"]
    lid = student["syntheticId"]
    p = Provider.from_bundle(learner_dir)
    start_entries = len(p.entries)

    # Steps 1-2: grant Tutor A and personalize.
    ga = p.issue_grant(client=T.TUTOR_A, access=T.tutoring_access(["read", "write"]), at=GRANT_A, label="A")
    ctx_a = T.read_context(p, ga["grantId"], T.TUTOR_A, GRANT_A)
    plan_a = T.plan_tutor_a(ctx_a)

    # Step 3: Tutor A's session produces new evidence, written to HCP.
    session = None
    if plan_a.target:
        session = T.run_session(p, ga["grantId"], lid, plan_a.target, ctx_a, SESSION_A)

    # Step 4: switch tutors. Tutor A loses access; Tutor B is granted.
    p.revoke_grant(ga["grantId"], REVOKE_A, reason="learner switched tutors")
    after = p.query(ga["grantId"], {"query": T.MATH_QUERY, "purpose": T.TUTORING}, READ_B, client=T.TUTOR_A)
    gb = p.issue_grant(client=T.TUTOR_B, access=T.tutoring_access(["read", "write"]), at=GRANT_B, label="B")
    ctx_b = T.read_context(p, gb["grantId"], T.TUTOR_B, READ_B)
    plan_b = T.plan_tutor_b(ctx_b)

    # Step 5: the counterfactual.
    plan_cold = T.plan_cold_start(ctx_b, student["grade"])

    disclosed = set(ctx_b.disclosed_ids)
    withheld: dict[str, int] = {}
    for e in p.entries.values():
        r = why_withheld(p, e, READ_B, disclosed, T.TUTOR_B)
        if r:
            withheld[r] = withheld.get(r, 0) + 1
    saw_tutor_a = bool(session and session["entry"]["id"] in disclosed)

    return {
        "learner": {"id": lid, "name": f"{student['firstName']} {student['lastName']}",
                    "grade": student["grade"], "state": student["stateName"],
                    "school": student["schoolName"], "profile": student["academicProfile"]},
        "hcp": {"entriesAtStart": start_entries, "entriesAtEnd": len(p.entries),
                "tutorBDisclosed": len(disclosed), "tutorBByDeclaration": ctx_b.by_declaration,
                "withheldFromTutorB": withheld, "tutorAAfterRevocation": after.error,
                "tutorBSawTutorAEvidence": saw_tutor_a,
                "auditEventsDuringDemo": len(p.audit_since(GRANT_A))},
        "context": {"course": ctx_b.course, "mastered": len(ctx_b.mastered),
                    "totalStandards": ctx_b.total_standards,
                    "notYetMastered": [n["standard"] for n in ctx_b.not_yet_mastered],
                    "notAssessed": ctx_b.not_assessed, "assessment": ctx_b.assessment,
                    "statements": ctx_b.statements, "interests": ctx_b.interests},
        "tutorA": {**plan_a.__dict__, "session": session and {"summary": session["summary"],
                                                              "secure": session["secure"],
                                                              "entryId": session["entry"]["id"]}},
        "tutorB": plan_b.__dict__,
        "coldStart": plan_cold.__dict__,
        "metrics": {
            "intakeItemsWithHCP": plan_b.intake_items,
            "intakeItemsWithoutHCP": plan_cold.intake_items,
            "intakeMinutesSaved": round((plan_cold.intake_items - plan_b.intake_items) * MINUTES_PER_ITEM),
            "shareOfPoolAlreadyMastered": round(len(ctx_b.mastered) / ctx_b.total_standards, 2) if ctx_b.total_standards else None,
            "personalizationSignalsWithHCP": len(ctx_b.statements) + (1 if ctx_b.interests else 0),
            "personalizationSignalsWithoutHCP": 0,
            "buildsOnTutorA": saw_tutor_a,
        },
    }


def render(r: dict) -> str:
    L, h, a, b, c, m = r["learner"], r["hcp"], r["tutorA"], r["tutorB"], r["coldStart"], r["metrics"]
    ctx = r["context"]
    lines = [
        f"# Track A: {L['name']} ({L['id']})",
        "",
        f"Grade {L['grade']}, {L['school']}, {L['state']}. Synthetic learner; no real student data.",
        "",
        "## 1. Starting record",
        f"- {h['entriesAtStart']} HCP entries from the Understudy record.",
        f"- Math course: {ctx['course'] or 'n/a'}; {ctx['mastered']} of {ctx['totalStandards']} standards mastered; "
        f"not yet mastered: {', '.join(ctx['notYetMastered']) or 'none'}; not yet assessed: {ctx['notAssessed']}.",
        f"- {ctx['assessment'] or ''}",
        "",
        "## 2. Tutor A personalizes",
        f"- Target: **{a['target'] or 'none'}** because {a['reason']}.",
        f"- Session length: {a['session_minutes']} minutes.",
        *[f"- {x}" for x in a["approach"]],
        "",
        "## 3. New evidence written to HCP",
        f"- {a['session']['summary']}" if a["session"] else "- No targeted session (nothing to remediate).",
        "- Recorded as `model-inferred`, medium confidence, asserted by Tutor A's estimator, under Tutor A's grant." if a["session"] else "",
        "",
        "## 4. Switch to Tutor B",
        f"- The learner revokes Tutor A. Tutor A's next query gets `{h['tutorAAfterRevocation']}`.",
        f"- Tutor B is granted tutoring access and receives {h['tutorBDisclosed']} entries "
        f"({', '.join(f'{v} {k}' for k, v in sorted(h['tutorBByDeclaration'].items()))}).",
        f"- Tutor B sees Tutor A's new evidence: **{'yes' if h['tutorBSawTutorAEvidence'] else 'no'}**.",
        "- Not given to Tutor B: " + ("nothing: Tutor B received every entry." if not h["withheldFromTutorB"] else "") + "; ".join(f"{v} {'entry' if v == 1 else 'entries'}: {k}" for k, v in sorted(h["withheldFromTutorB"].items())) + ("." if h["withheldFromTutorB"] else ""),
        "",
        "## 5. Tutor B continues",
        f"- Target: **{b['target'] or 'none'}** because {b['reason']}.",
        *[f"- {x}" for x in b["approach"]],
        *[f"- Directive honored: must ask first: \"{x}\"" for x in b["asks_first"]],
        "",
        "## With and without HCP (Tutor B)",
        "",
        "| | With HCP | Without HCP |",
        "|---|---|---|",
        f"| Intake items before targeted practice | {m['intakeItemsWithHCP']} | {m['intakeItemsWithoutHCP']} |",
        f"| Intake time saved (at {MINUTES_PER_ITEM} min/item) | {m['intakeMinutesSaved']} min | - |",
        f"| Known learner preferences (pacing, what helps, interests...) | {m['personalizationSignalsWithHCP']} | 0 |",
        f"| Share of the course already mastered (re-teaching risk) | known, skipped | {m['shareOfPoolAlreadyMastered']:.0%} at risk |" if m["shareOfPoolAlreadyMastered"] is not None else "",
        f"| Builds on Tutor A's session | {'yes' if m['buildsOnTutorA'] else 'n/a (no session)'} | no |",
        f"| First step | {b['target'] or 'short check'} | {c['reason']} |",
        "",
    ]
    return "\n".join(x for x in lines if x is not None)


def render_summary(results: list[dict]) -> str:
    rows = ["# Track A cohort summary", "",
            "Ten synthetic learners (Understudy seed 2368342781). Each runs the same five steps.", "",
            "| Learner | Grade | Tutor A target | Tutor A result | Tutor B target | B saw A's evidence | Intake items with / without HCP | Minutes saved | Preference signals |",
            "|---|---|---|---|---|---|---|---|---|"]
    tot_with = tot_without = 0
    for r in results:
        a, b, m, h = r["tutorA"], r["tutorB"], r["metrics"], r["hcp"]
        res = ("secure" if a["session"]["secure"] else "developing") if a["session"] else "-"
        rows.append(f"| [{r['learner']['name']}]({r['learner']['id']}.md) | {r['learner']['grade']} | {a['target'] or '-'} | {res} | "
                    f"{b['target'] or '-'} | {'yes' if h['tutorBSawTutorAEvidence'] else '-'} | "
                    f"{m['intakeItemsWithHCP']} / {m['intakeItemsWithoutHCP']} | {m['intakeMinutesSaved']} | {m['personalizationSignalsWithHCP']} |")
        tot_with += m["intakeItemsWithHCP"]
        tot_without += m["intakeItemsWithoutHCP"]
    rows += ["", f"Across the cohort Tutor B needs {tot_with} intake items with HCP versus {tot_without} without "
             f"({round((tot_without - tot_with) * MINUTES_PER_ITEM)} learner-minutes saved at {MINUTES_PER_ITEM} min/item).",
             "",
             "These tutors are rule-based stand-ins and the session outcomes are simulated from the record, so "
             "the figures show what the context makes possible, not measured learning gains. A pilot would "
             "replace them with real tutors and measured outcomes."]
    return "\n".join(rows) + "\n"


def main(argv: list[str]) -> int:
    args = [x for x in argv[1:] if not x.startswith("--")]
    bundle = Path(args[0]) if args else DEFAULT_BUNDLE
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else Path("reports/track-a")
    out.mkdir(parents=True, exist_ok=True)
    results = [run_learner(d) for d in sorted((bundle / "learners").iterdir())]
    for r in results:
        (out / f"{r['learner']['id']}.md").write_text(render(r), encoding="utf-8")
    (out / "README.md").write_text(render_summary(results), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(render_summary(results))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
