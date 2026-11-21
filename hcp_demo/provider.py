"""A minimal, in-memory HCP Provider for demonstration.

It loads one learner's HCP export (from an Understudy bundle) and answers
context queries under grants, enforcing the rules the Understudy fixtures
encode for HCP 2.0-draft-3:

* the grant must be in force at the moment of the request (issued, not
  expired, not revoked) -> otherwise ``invalid-token``
* the request's purpose must be one the grant names, and any categories the
  request names must be readable under that purpose -> otherwise ``scope-denied``
* only entries that are active at that moment are eligible (not yet expired,
  not suspended or revoked on the issuer's status list, already recorded)
* an entry restricted to ``permittedPurposes`` is only eligible for those purposes
* a grant ``narrowedTo`` specific entries reaches only those entries
* a standing rule that denies the client's operator removes what it covers
* directives that cover a disclosed category travel with the response

This is not a conformant HCP implementation (no HTTP/MCP binding, no
cryptographic verification, no token handling). It is a fixture-checked model
of the access decisions, sufficient to drive the demos honestly. See
``check_scenarios.py`` for how it is scored against the fixture.
"""
from __future__ import annotations

import copy
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEMO_NS = uuid.UUID("6f1c3a52-8e0b-4f53-9a57-0c3d2b7e9a11")
PROVIDER_ID = "https://hcp-provider.understudy.example"


def ts(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def demo_uuid(*parts: str) -> str:
    """Deterministic identifiers so every run produces identical output."""
    return f"urn:uuid:{uuid.uuid5(DEMO_NS, '|'.join(parts))}"


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


_WORD = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*")
_STOP = {
    "a", "an", "and", "any", "are", "as", "be", "do", "does", "for", "has",
    "have", "i", "in", "is", "it", "know", "like", "me", "of", "on", "or",
    "should", "tell", "the", "their", "they", "this", "to", "what", "which",
    "who", "with", "work", "learner", "about", "how", "next", "so", "at",
}


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD.findall(text.lower()) if t not in _STOP}


def entry_text(entry: dict) -> str:
    """Searchable text for an entry: its dimension, value and credential."""
    parts = [entry["classification"].get("dimension", "")]
    content = entry.get("content", {})
    value = content.get("value")
    if isinstance(value, str):
        parts.append(value)
    elif isinstance(value, dict):
        parts.append(str(value.get("summary", "")))
    for ev in entry.get("evidence", []) or []:
        cred = ev.get("credential") or {}
        parts.append(cred.get("name", ""))
        subj = cred.get("credentialSubject", {})
        ach = subj.get("achievement", {})
        parts.append(ach.get("description", ""))
        parts.append(str(subj.get("extract", {}).get("summary", "")))
    text = " ".join(parts)
    return text.replace("_", " ").replace("/", " ").replace("-", " ")


def _operator_match(operator_id: str, operators: list[str]) -> bool:
    """Operators may be named by URL or by bare host."""
    host = re.sub(r"^https?://", "", operator_id).rstrip("/")
    return any(re.sub(r"^https?://", "", o).rstrip("/") == host for o in operators)


@dataclass
class QueryResult:
    outcome: str                      # "entries" | "error"
    error: str | None = None
    entries: list[dict] = field(default_factory=list)
    eligible_ids: list[str] = field(default_factory=list)
    categories_searched: list[str] = field(default_factory=list)
    directives: list[dict] = field(default_factory=list)

    @property
    def entry_ids(self) -> list[str]:
        return [e["id"] for e in self.entries]


class Provider:
    """One learner's context, held by an HCP Provider."""

    def __init__(self, export: dict, grants: list[dict]):
        self.export = copy.deepcopy(export)
        self.subject = export["subject"]
        self.entries: dict[str, dict] = {e["id"]: e for e in self.export["entries"]}
        self.grants: dict[str, dict] = {g["grantId"]: copy.deepcopy(g) for g in grants}
        self.rules: list[dict] = list(self.export.get("rules", []))
        self.directives: list[dict] = list(self.export.get("directives", []))
        self.audit: list[dict] = list(self.export.get("audit", []))
        # Moments that change access, recovered from the audit log.
        self.revoked_at: dict[str, datetime] = {}
        self.entry_status_changes: dict[str, list[tuple[datetime, str]]] = {}
        for ev in self.audit:
            t = ts(ev["timestamp"])
            if ev["eventType"] == "grant.revoked" and ev.get("grantId"):
                self.revoked_at[ev["grantId"]] = t
            if ev["eventType"] == "context.credentialStatus" and ev.get("entryId"):
                status = (ev.get("data") or {}).get("entryStatus")
                if status:
                    self.entry_status_changes.setdefault(ev["entryId"], []).append((t, status))

    @classmethod
    def from_bundle(cls, learner_dir: Path) -> "Provider":
        return cls(load_json(learner_dir / "export.json"), load_json(learner_dir / "grants.json"))

    # ------------------------------------------------------------------ grants
    def grant_in_force(self, grant: dict, at: datetime) -> bool:
        issued = ts(grant.get("issuedAt"))
        if issued and at < issued:
            return False
        expires = ts(grant.get("expiresAt"))
        if expires and at >= expires:
            return False
        revoked = self.revoked_at.get(grant["grantId"])
        if revoked and at >= revoked:
            return False
        if grant.get("status") == "revoked" and grant["grantId"] not in self.revoked_at:
            return False
        return True

    def issue_grant(self, *, client: dict, access: list[dict], at: datetime,
                    grant_type: str = "persistent", expires_at: datetime | None = None,
                    label: str = "") -> dict:
        grant_id = demo_uuid(self.subject["id"], "grant", client["id"], label, iso(at))
        scopes = [f"hcp:{c}:{a}" for blk in access for c in blk["categories"] for a in blk["actions"]]
        grant = {
            "grantId": grant_id,
            "subject": {"id": demo_uuid(self.subject["id"], "pairwise", client["id"])},
            "client": client,
            "access": access,
            "scopes": scopes,
            "grantType": grant_type,
            "issuedAt": iso(at),
            "expiresAt": iso(expires_at) if expires_at else None,
            "status": "active",
        }
        self.grants[grant_id] = grant
        self._log("grant.issued", at, role="authorization-service", grant_id=grant_id,
                  categories=sorted({c for b in access for c in b["categories"]}),
                  data={"client": client["id"], "access": access})
        return grant

    def revoke_grant(self, grant_id: str, at: datetime, reason: str = "learner") -> None:
        self.grants[grant_id]["status"] = "revoked"
        self.revoked_at[grant_id] = at
        self._log("grant.revoked", at, role="management-client", grant_id=grant_id,
                  data={"reason": reason})

    # ----------------------------------------------------------------- entries
    def entry_active_at(self, entry: dict, at: datetime) -> bool:
        prov = entry["record"].get("provenance", {})
        recorded = ts(prov.get("recordedAt") or prov.get("assertedAt"))
        if recorded and recorded > at:
            return False
        status = entry["record"]["status"]
        valid_until = ts(entry["assertion"].get("validUntil"))
        if valid_until and at >= valid_until:
            return False
        if status in ("active", "expired"):
            # "expired" at export time may still have been valid at `at`;
            # validUntil above is the deciding fact.
            pass
        elif status in ("suspended", "revoked"):
            if not self.entry_status_changes.get(entry["id"]):
                return False
        else:  # deprecated, conflicted, deleted
            return False
        # The issuer's status list decides: the latest change at or before `at`
        # wins (a credential can be suspended and later reinstated).
        latest = None
        for t, s in sorted(self.entry_status_changes.get(entry["id"], [])):
            if t <= at:
                latest = s
        if latest in ("suspended", "revoked"):
            return False
        if latest is None and status in ("suspended", "revoked"):
            return True  # suspended only after `at`
        return True

    def _rule_applies(self, rule: dict, client: dict, at: datetime) -> bool:
        """Does a deny rule in force at `at` reach this client?"""
        if rule.get("effect") != "deny":
            return False
        if ts(rule.get("createdAt")) and ts(rule["createdAt"]) > at:
            return False
        if "operators" in rule and not _operator_match(client["operator"]["id"], rule["operators"]):
            return False
        if "requires" in rule:
            claims = set(client.get("claims", []))
            if set(rule["requires"]) <= claims:
                return False  # the client has what the rule requires
        return True

    def denied_categories(self, client: dict, at: datetime) -> set[str] | None:
        """Categories a standing rule denies this client. None = everything."""
        denied: set[str] = set()
        for rule in self.rules:
            if self._rule_applies(rule, client, at):
                if not rule.get("categories"):
                    return None
                denied |= set(rule["categories"])
        return denied

    # ------------------------------------------------------------------- query
    def query(self, grant_id: str, request: dict, at: datetime, *, log: bool = True,
              client: dict | None = None) -> QueryResult:
        """Answer a context query. `client` is the client as it presents
        itself (with any claims); it defaults to the client the grant names."""
        grant = self.grants.get(grant_id)
        if grant is None or not self.grant_in_force(grant, at):
            return QueryResult(outcome="error", error="invalid-token")
        client = client or grant["client"]
        denied = self.denied_categories(client, at)
        if denied is None:
            return QueryResult(outcome="error", error="scope-denied")

        purpose = request.get("purpose")
        blocks = [b for b in grant["access"]
                  if "read" in b["actions"] and any(p["code"] == purpose for p in b["purposes"])]
        if not blocks:
            return QueryResult(outcome="error", error="scope-denied")
        readable: list[str] = []
        for b in blocks:
            for c in b["categories"]:
                if c not in readable:
                    readable.append(c)
        requested = request.get("categories")
        if requested:
            if any(c not in readable or c in denied for c in requested):
                return QueryResult(outcome="error", error="scope-denied")
            searched = [c for c in requested]
        else:
            searched = [c for c in readable if c not in denied]

        narrowed: set[str] | None = None
        for b in blocks:
            if "narrowedTo" in b:
                narrowed = (narrowed or set()) | set(b["narrowedTo"].get("entryIds", []))

        operator_id = client["operator"]["id"]
        eligible = []
        for entry in self.entries.values():
            cats = entry["classification"]["categories"]
            if not set(cats) & set(searched):
                continue
            if not self.entry_active_at(entry, at):
                continue
            permitted = entry["classification"].get("permittedPurposes")
            if permitted and purpose not in permitted:
                continue
            if narrowed is not None and entry["id"] not in narrowed:
                continue
            eligible.append(entry)

        ranked = self._rank(eligible, request.get("query", ""))
        limit = request.get("maxEntries") or len(ranked)
        disclosed = ranked[:limit]

        directives = []
        for d in self.directives:
            if ts(d.get("createdAt")) and ts(d["createdAt"]) > at:
                continue
            if "operators" in d and not _operator_match(operator_id, d["operators"]):
                continue
            when = [c for c in searched if c in d.get("categories", [])]
            if when:
                directives.append({"directiveId": d["directiveId"], "whenDisclosing": when,
                                   "action": d.get("action"), "effect": d.get("effect"),
                                   "text": d.get("text")})

        if log:
            self._log("context.read", at, role="context-client", grant_id=grant_id,
                      categories=searched, purpose=purpose,
                      data={"client": grant["client"]["id"], "query": request.get("query"),
                            "disclosed": [e["id"] for e in disclosed]})
        return QueryResult(outcome="entries", entries=copy.deepcopy(disclosed),
                           eligible_ids=[e["id"] for e in eligible],
                           categories_searched=searched, directives=directives)

    @staticmethod
    def _rank(entries: list[dict], query: str) -> list[dict]:
        q = _tokens(query)
        # Light synonym expansion so "math" finds "mathematics", etc.
        if q & {"math", "mathematics"}:
            q |= {"math", "mathematics", "ccss", "mastery", "frontier", "practice", "estimate"}
        if q & {"mastered", "master", "standards"}:
            q |= {"mastery", "frontier", "standard"}

        def score(e: dict) -> tuple:
            toks = _tokens(entry_text(e))
            prov = e["record"].get("provenance", {})
            recorded = ts(prov.get("recordedAt") or prov.get("assertedAt"))
            newest_first = -recorded.timestamp() if recorded else 0.0
            return (-len(q & toks), newest_first, e["classification"].get("dimension", ""), e["id"])

        return sorted(entries, key=score)

    # ------------------------------------------------------------------ create
    def create(self, grant_id: str, *, categories: list[str], dimension: str, value: Any,
               declaration_type: str, at: datetime, purpose: str,
               confidence: str | None = None, valid_until: datetime | None = None,
               basis: dict | None = None, asserted_by: dict | None = None,
               source: str = "integration") -> dict:
        grant = self.grants.get(grant_id)
        if grant is None or not self.grant_in_force(grant, at):
            raise PermissionError("invalid-token")
        writable = {c for b in grant["access"] if "write" in b["actions"]
                    and any(p["code"] == purpose for p in b["purposes"]) for c in b["categories"]}
        if not set(categories) <= writable:
            raise PermissionError("scope-denied")
        if declaration_type == "model-inferred" and confidence is None:
            raise ValueError("model-inferred entries must state a confidence")
        client = grant["client"]
        entry_id = demo_uuid(self.subject["id"], "entry", client["id"], dimension, iso(at))
        assertion: dict[str, Any] = {"declarationType": declaration_type,
                                     "confidence": confidence,
                                     "validUntil": iso(valid_until) if valid_until else None}
        if basis:
            assertion["basis"] = basis
        entry = {
            "@context": ["https://hcp.example/contexts/v2"],
            "schema": "https://hcp.example/spec/entry/2.0",
            "id": entry_id,
            "type": ["ContextEntry"],
            "subject": {"id": self.subject["id"], "relationship": None},
            "content": {"profile": "https://hcp.example/spec/profiles/general-context/2.0",
                        "value": value, "language": "en"},
            "assertion": assertion,
            "classification": {"categories": categories, "dimension": dimension},
            "record": {
                "status": "active",
                "version": 1,
                "provenance": {
                    "assertedBy": asserted_by or {"id": client["id"], "assurance": "authenticated"},
                    "assertedAt": iso(at),
                    "source": source,
                    "submittedByClient": client,
                    "authorizedUnder": grant_id,
                    "recordedByProvider": PROVIDER_ID,
                    "recordedAt": iso(at),
                },
                "relationships": [],
                "metadata": {"synthetic": True, "generator": "hcp-learner-continuity-demo"},
            },
        }
        self.entries[entry_id] = entry
        self._log("context.created", at, role="context-client", grant_id=grant_id,
                  categories=categories, purpose=purpose, entry_id=entry_id,
                  data={"client": client["id"], "dimension": dimension})
        return entry

    # ------------------------------------------------------------------- audit
    def _log(self, event_type: str, at: datetime, *, role: str, grant_id: str | None = None,
             categories: list[str] | None = None, purpose: str | None = None,
             entry_id: str | None = None, data: dict | None = None) -> None:
        self.audit.append({
            "eventId": demo_uuid(self.subject["id"], "audit", event_type, iso(at), str(len(self.audit))),
            "eventType": event_type,
            "timestamp": iso(at),
            "participants": {"initiator": {"role": role}, "provider": {"id": PROVIDER_ID}},
            "entryId": entry_id,
            "categories": categories or [],
            "purpose": purpose,
            "grantId": grant_id,
            "data": data or {},
        })

    def audit_since(self, at: datetime) -> list[dict]:
        return [e for e in self.audit if ts(e["timestamp"]) >= at]


__all__ = ["Provider", "QueryResult", "ts", "iso", "demo_uuid", "load_json", "entry_text"]

# Convenience for scripts
ONE_DAY = timedelta(days=1)
