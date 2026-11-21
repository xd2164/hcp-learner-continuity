# HCP concepts used here

A map from the HCP 2.0-draft-3 concepts this repo relies on to where they appear
in code. It is a reading aid, not a restatement of the spec. The
[specification](https://github.com/loyalagents/hcp-spec) governs (currently in
private partner review; request access from the Loyal Agents initiative).

| Concept | Meaning in this repo | Code |
|---|---|---|
| Context entry | One unit of learner context with content, assertion, classification, evidence and record (status, version, provenance) | `Provider.entries` |
| Declaration type | `issuer-attested`, `model-inferred` (requires confidence) or `person-declared` | `tutors.build_context`, `plan_tutor_b` |
| Provenance | Who asserted the entry, through which client, under which grant | `Provider.create` |
| Grant | A client's access: actions, categories and purposes; persistent or temporary; can be revoked | `Provider.issue_grant`, `grant_in_force`, `revoke_grant` |
| Narrowed grant | Access limited to named entries | `query` (`narrowedTo`) |
| Purpose restriction | An entry is eligible only for named purposes | `query` (`permittedPurposes`) |
| Standing rule | The learner or guardian denies categories to operators, or to clients lacking a capability | `denied_categories` |
| Directive | An instruction that travels with the context (for example, ask first before signing up) | `query` → `QueryResult.directives` |
| Delegation | A guardian acting for a minor; the fixture's grants are authorized under it | in fixture data |
| VC evidence | A Verifiable Credential backing an entry; status lists can suspend or revoke it | `entry_active_at` |
| Audit log | Every grant, read, create and revocation is recorded | `Provider._log` |
| Errors | `invalid-token` (grant not in force) and `scope-denied` (purpose or category outside the grant) | `query` |

Not modelled: HTTP and MCP bindings, OAuth tokens, signature verification,
versioning and conflict resolution, onward-sharing reports, hard delete, import
validation against the JSON Schemas. A pilot should use a real HCP provider and
keep `check_scenarios.py` as a conformance smoke test.
