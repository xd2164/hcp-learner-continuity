"""Two independent, rule-based AI tutors that read and write HCP context.

The tutors are deliberately simple and deterministic (no model calls) so the
demo is repeatable and the comparison is about *context*, not tutor quality.
A real pilot would swap these for independently built tutoring
products; the HCP calls they make would be the same.
"""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .provider import Provider, QueryResult

TUTORING = "https://understudy.example/hcp/purposes/tutoring"
DIRECTIVES_CLAIM = "https://hcp.example/spec/clients/directives/2.0"
PROFILE = "education_learner_profile"
TUTOR_CATEGORIES = [PROFILE, "goals_and_constraints", "general_preferences"]

MATH_QUERY = ("What has this learner mastered in mathematics, which standards are "
              "not yet mastered, and what recent practice evidence is there?")
PRACTICE_QUERY = "Most recent practice estimate evidence for mathematics standards."
LEARNER_QUERY = ("Learner statement: what helps, pacing, difficulty, strength, goal "
                 "and interests outside school.")


def tutor_client(slug: str, name: str, operator_name: str) -> dict:
    return {
        "id": f"https://{slug}.demo.example/clients/hcp",
        "name": name,
        "operator": {"id": f"https://{slug}.demo.example", "name": operator_name},
        "claims": [DIRECTIVES_CLAIM],
    }


TUTOR_A = tutor_client("tutor-a", "Tutor A: Stepwise Math (synthetic)", "Stepwise Learning Co. (synthetic)")
TUTOR_B = tutor_client("tutor-b", "Tutor B: Next Step Math (synthetic)", "Next Step Tutoring (synthetic)")


def tutoring_access(actions: list[str]) -> list[dict]:
    return [{
        "type": "https://hcp.example/spec/authorization/context-access",
        "actions": actions,
        "categories": TUTOR_CATEGORIES,
        "purposes": [{"code": TUTORING, "description": "Personalized math tutoring"}],
    }]


# --------------------------------------------------------------------------
# What a tutor can understand from disclosed HCP entries
# --------------------------------------------------------------------------
@dataclass
class Evidence:
    standard: str
    level: str               # e.g. Mastery, Near Mastery, secure, developing
    source: str              # declarationType
    asserted_by: str         # client / issuer name
    confidence: str | None
    detail: str
    asserted_at: str = ""


@dataclass
class LearnerContext:
    course: str | None = None
    grade_pool: str | None = None
    total_standards: int = 0
    mastered: list[str] = field(default_factory=list)
    not_yet_mastered: list[dict] = field(default_factory=list)
    practice: dict[str, Evidence] = field(default_factory=dict)
    statements: dict[str, str] = field(default_factory=dict)
    interests: str | None = None
    assessment: str | None = None
    directives: list[dict] = field(default_factory=list)
    disclosed_ids: list[str] = field(default_factory=list)
    by_declaration: dict[str, int] = field(default_factory=dict)

    @property
    def not_assessed(self) -> int:
        return max(self.total_standards - len(self.mastered) - len(self.not_yet_mastered), 0)


def _asserter(entry: dict) -> str:
    prov = entry["record"]["provenance"]
    client = prov.get("submittedByClient") or {}
    for ev in entry.get("evidence") or []:
        issuer = (ev.get("credential") or {}).get("issuer", {})
        if issuer.get("name"):
            return issuer["name"]
    return client.get("name") or prov["assertedBy"]["id"]


def build_context(results: list[QueryResult]) -> LearnerContext:
    ctx = LearnerContext()
    seen: set[str] = set()
    for res in results:
        ctx.directives += [d for d in res.directives if d["directiveId"] not in {x["directiveId"] for x in ctx.directives}]
        for e in res.entries:
            if e["id"] in seen:
                continue
            seen.add(e["id"])
            ctx.disclosed_ids.append(e["id"])
            decl = e["assertion"]["declarationType"]
            ctx.by_declaration[decl] = ctx.by_declaration.get(decl, 0) + 1
            dim = e["classification"].get("dimension", "")
            value = e.get("content", {}).get("value")
            creds = [ev.get("credential") for ev in e.get("evidence") or [] if ev.get("credential")]
            cred = creds[0] if creds else None
            if cred and dim.startswith("https://understudy.example/standards/CCSS/"):
                desc = cred["credentialSubject"]["achievement"].get("description", "")
                if "Mathematics" in desc:
                    level = cred["name"].split(": ", 1)[-1]
                    std = dim.rsplit("/", 1)[-1]
                    if level in ("Mastered", "Mastery", "Exceeds Mastery"):
                        ctx.mastered.append(std)
            elif cred and dim == "mastery_frontier/mathematics":
                ex = cred["credentialSubject"]["extract"]
                ctx.course = ex.get("course")
                ctx.grade_pool = ex.get("poolGrade")
                ctx.total_standards = ex.get("totalStandards", 0)
                ctx.not_yet_mastered = sorted(ex.get("notYetMastered", []), key=lambda n: (n["rollup"], n["standard"]))
            elif cred and dim == "assessment/mathematics":
                ctx.assessment = cred["credentialSubject"]["extract"].get("summary")
            elif dim.startswith("practice_estimate/") and isinstance(value, dict):
                std = value["standard"]
                prev = ctx.practice.get(std)
                ev = Evidence(std, "secure" if "secure" in value["summary"].lower() else "developing",
                              decl, _asserter(e), e["assertion"].get("confidence"), value["summary"],
                              e["record"]["provenance"]["assertedAt"])
                if prev is None or ev.asserted_at >= prev.asserted_at:  # newest evidence wins
                    ctx.practice[std] = ev
            elif dim.startswith("learner_statement/") and isinstance(value, str):
                ctx.statements[dim.split("/", 1)[1]] = value
            elif dim == "interests" and isinstance(value, str):
                ctx.interests = value
    # The school's credentials list mastered standards; keep the count honest
    # with the frontier summary when both are present.
    ctx.mastered = sorted(set(ctx.mastered))
    return ctx


def read_context(provider: Provider, grant_id: str, client: dict, at: datetime) -> LearnerContext:
    math = provider.query(grant_id, {"query": MATH_QUERY, "categories": [PROFILE],
                                     "purpose": TUTORING, "maxEntries": 60}, at, client=client)
    practice = provider.query(grant_id, {"query": PRACTICE_QUERY, "categories": [PROFILE],
                                         "purpose": TUTORING, "maxEntries": 15},
                              at + timedelta(seconds=1), client=client)
    about = provider.query(grant_id, {"query": LEARNER_QUERY, "purpose": TUTORING,
                                      "maxEntries": 12}, at + timedelta(seconds=2), client=client)
    for r in (math, practice, about):
        if r.outcome != "entries":
            raise PermissionError(r.error)
    return build_context([math, practice, about])


# --------------------------------------------------------------------------
# Tutoring decisions
# --------------------------------------------------------------------------
def _minutes(statement: str | None) -> int | None:
    if not statement:
        return None
    m = re.search(r"(\d+)\s*(?:min|minute)", statement.lower())
    return int(m.group(1)) if m else None


def _rng(*parts: str) -> random.Random:
    return random.Random(int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:12], 16))


@dataclass
class Plan:
    tutor: str
    target: str | None
    reason: str
    session_minutes: int
    approach: list[str]
    intake_items: int
    asks_first: list[str]


def choose_target(ctx: LearnerContext, skip: set[str] = frozenset()) -> tuple[str | None, str]:
    for n in ctx.not_yet_mastered:
        if n["standard"] in skip:
            continue
        return n["standard"], (f"school record: {n['level']} (rollup {n['rollup']}/4, last evidence "
                               f"{n['lastEvidence']})")
    low = [p for p in ctx.practice.values() if p.level == "developing" and p.standard not in skip]
    if low:
        return low[0].standard, f"practice evidence still developing ({low[0].detail})"
    if ctx.not_assessed:
        return None, f"{ctx.not_assessed} standards in the course are not yet assessed: start with a short check"
    return None, "all standards in the course are mastered: offer enrichment from the next course"


def personalize(ctx: LearnerContext) -> tuple[int, list[str]]:
    minutes = _minutes(ctx.statements.get("pacing")) or 20
    approach = []
    if ctx.statements.get("what_helps"):
        approach.append(f'Learner asked: "{ctx.statements["what_helps"]}"')
    if ctx.statements.get("difficulty"):
        approach.append(f'Known difficulty: "{ctx.statements["difficulty"]}"')
    if ctx.interests:
        approach.append(f"Frame word problems around stated interests: {ctx.interests}")
    return minutes, approach


def plan_tutor_a(ctx: LearnerContext) -> Plan:
    target, reason = choose_target(ctx)
    minutes, approach = personalize(ctx)
    return Plan(TUTOR_A["name"], target, reason, minutes, approach,
                intake_items=0 if target else 2 * ctx.not_assessed, asks_first=[])


def run_session(provider: Provider, grant_id: str, learner_id: str, target: str,
                ctx: LearnerContext, at: datetime) -> dict:
    """Simulate a Tutor A practice session and write its evidence to HCP."""
    rollup = next((n["rollup"] for n in ctx.not_yet_mastered if n["standard"] == target), 2)
    rng = _rng(learner_id, target)
    attempts = 10
    results = []
    for i in range(attempts):
        p = min(0.95, 0.40 + 0.10 * rollup + 0.04 * i)   # learning within the session
        results.append(rng.random() < p)
    recent = sum(results[-5:])
    correct = sum(results)
    secure = recent >= 4
    summary = (f"Tutored practice on CCSS {target}: {recent} of the last 5 attempts correct "
               f"({correct} of {attempts} in all). Estimated {'secure' if secure else 'developing'}.")
    entry = provider.create(
        grant_id, categories=[PROFILE], dimension=f"practice_estimate/CCSS/{target}",
        value={"summary": summary, "standard": target, "framework": "CCSS",
               "attempts": attempts, "correct": correct, "recentCorrect": recent,
               "recentAttempts": 5},
        declaration_type="model-inferred", confidence="medium", at=at, purpose=TUTORING,
        valid_until=at + timedelta(days=120),
        basis={"drawnFrom": ["observation"], "task": "Mathematics tutoring session",
               "setting": "Tutor A (synthetic)",
               "rationale": "Estimated from correctness on the last five of ten tutored items."},
        asserted_by={"id": "https://tutor-a.demo.example/models/estimator/0.1", "assurance": "authenticated"},
    )
    return {"entry": entry, "secure": secure, "summary": summary}


def plan_tutor_b(ctx: LearnerContext) -> Plan:
    """Tutor B weighs evidence by who asserted it and how."""
    skip: set[str] = set()
    confirm_items = 0
    notes = []
    for std, ev in ctx.practice.items():
        school_gap = any(n["standard"] == std for n in ctx.not_yet_mastered)
        if school_gap and ev.source == "model-inferred" and ev.level == "secure" and ev.confidence in ("medium", "high"):
            skip.add(std)
            confirm_items += 2
            notes.append(f"{std}: school record says not yet mastered, but newer practice evidence from "
                         f"{ev.asserted_by} ({ev.source}, {ev.confidence} confidence) says secure. "
                         f"Model-inferred, so confirm with 2 items rather than re-teach.")
        elif school_gap and ev.level == "developing" and ev.asserted_at > "2026-07":
            notes.append(f"{std}: {ev.asserted_by} already practiced this ({ev.detail}). Continue it, "
                         f"switching representation rather than repeating the same explanation.")
    target, reason = choose_target(ctx, skip)
    minutes, approach = personalize(ctx)
    asks_first = [d["text"] for d in ctx.directives if d.get("effect") == "ask-first"]
    plan = Plan(TUTOR_B["name"], target, reason, minutes, notes + approach,
                intake_items=confirm_items + (0 if target else 2 * ctx.not_assessed),
                asks_first=asks_first)
    return plan


def plan_cold_start(ctx_truth: LearnerContext, grade: str) -> Plan:
    """Tutor B with no HCP: it knows only the grade the learner types in."""
    items = 2 * ctx_truth.total_standards
    return Plan(TUTOR_B["name"] + " without HCP", None,
                f"no prior context: diagnostic across all {ctx_truth.total_standards} standards in "
                f"the course (learner reports grade {grade}) before any targeted practice",
                20, ["Generic explanations; no known preferences, pacing or interests"],
                intake_items=items, asks_first=[])
