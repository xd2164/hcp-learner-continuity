"""Score the demo provider against every scenario in an Understudy bundle.

For each learner and each scenario, the provider is put the scenario's query
as the named client at the stated moment. A scenario passes when:

* the outcome (entries or error) and the error code match,
* nothing in ``mustNotDisclose`` is returned,
* every returned entry is in ``eligibleEntryIds``,
* the provider's eligible set equals ``eligibleEntryIds`` exactly,
* ``categoriesSearched`` and the directive ids / ``whenDisclosing`` match.

Retrieval quality against ``relevantEntryIds`` is reported, not enforced:
the fixture says relevance is ground truth for scoring, and the provider's
keyword ranker is deliberately simple.

Usage:  python -m hcp_demo.check_scenarios [bundle_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

from .provider import Provider, load_json, ts

DEFAULT_BUNDLE = Path(__file__).resolve().parent.parent / "data" / "understudy-seed-2368342781"


def check_bundle(bundle: Path, verbose: bool = False) -> tuple[int, int, list[str], dict]:
    passed = total = 0
    failures: list[str] = []
    rel_hit = rel_total = returned_total = returned_relevant = 0
    for learner_dir in sorted((bundle / "learners").iterdir()):
        scenarios = load_json(learner_dir / "scenarios.json")
        provider = Provider.from_bundle(learner_dir)
        for sc in scenarios:
            total += 1
            exp = sc["expect"]
            res = provider.query(sc["grantId"], sc["request"], ts(sc["at"]), log=False, client=sc.get("client"))
            problems = []
            if res.outcome != exp["outcome"]:
                problems.append(f"outcome {res.outcome} != {exp['outcome']}")
            if exp["outcome"] == "error" and res.error != exp.get("error"):
                problems.append(f"error {res.error} != {exp.get('error')}")
            leaked = set(res.entry_ids) & set(exp.get("mustNotDisclose") or [])
            if leaked:
                problems.append(f"disclosed {len(leaked)} mustNotDisclose entries")
            if exp["outcome"] == "entries":
                eligible = set(exp.get("eligibleEntryIds") or [])
                if not set(res.entry_ids) <= eligible:
                    problems.append("returned an entry outside eligibleEntryIds")
                if set(res.eligible_ids) != eligible:
                    extra = len(set(res.eligible_ids) - eligible)
                    missing = len(eligible - set(res.eligible_ids))
                    problems.append(f"eligible set differs (+{extra} / -{missing})")
                if res.categories_searched != exp.get("categoriesSearched"):
                    problems.append(f"categoriesSearched {res.categories_searched} != {exp.get('categoriesSearched')}")
                want_dir = sorted((d["directiveId"], tuple(d["whenDisclosing"])) for d in exp.get("directives", []))
                got_dir = sorted((d["directiveId"], tuple(d["whenDisclosing"])) for d in res.directives)
                if want_dir != got_dir:
                    problems.append("directives differ")
                relevant = set(exp.get("relevantEntryIds") or [])
                rel_total += min(len(relevant), sc["request"].get("maxEntries") or len(relevant))
                rel_hit += len(relevant & set(res.entry_ids))
                returned_total += len(res.entry_ids)
                returned_relevant += len(relevant & set(res.entry_ids))
            label = f"{learner_dir.name}/{sc['id']}"
            if problems:
                failures.append(f"FAIL {label}: " + "; ".join(problems))
            else:
                passed += 1
                if verbose:
                    print(f"ok   {label}")
    retrieval = {
        "relevantRecalledWithinLimit": rel_hit,
        "relevantAvailableWithinLimit": rel_total,
        "returned": returned_total,
        "returnedRelevant": returned_relevant,
    }
    return passed, total, failures, retrieval


def main(argv: list[str]) -> int:
    bundle = Path(argv[1]) if len(argv) > 1 else DEFAULT_BUNDLE
    passed, total, failures, r = check_bundle(bundle, verbose="-v" in argv)
    for f in failures:
        print(f)
    print(f"\n{passed}/{total} scenarios pass the access checks.")
    if r["relevantAvailableWithinLimit"]:
        recall = r["relevantRecalledWithinLimit"] / r["relevantAvailableWithinLimit"]
        print(f"Retrieval (informational): recalled {r['relevantRecalledWithinLimit']} of "
              f"{r['relevantAvailableWithinLimit']} relevant entries within maxEntries ({recall:.0%}); "
              f"{r['returnedRelevant']} of {r['returned']} returned entries were relevant.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
