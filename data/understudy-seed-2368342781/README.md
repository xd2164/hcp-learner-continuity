# HCP learner bundles from Understudy

Synthetic learners, each as Human Context Protocol (HCP v2, 2.0-draft-3)
context. Every person, school, district, client, organization and key here is
synthetic. See `manifest.json` for the notice, the parameters and a SHA-256
of every file.

HCP v2 is a working draft: identifiers use the placeholder namespace
hcp.example and the format will change. Issuer keys are public test keys
(`issuers.json`); the credentials verify but secure nothing.

## Layout

    manifest.json                parameters, counts, check results, file hashes
    issuers.json                 district issuer DIDs (did:key)
    status-lists.json            each district's signed revocation and suspension
                                 lists (Bitstring Status List), which every
                                 credential names a slot in
    learners/<id>/
      export.json                the learner's HCP export: entries, superseded
                                 versions, standing rules, directives, delegation,
                                 audit log
      grants.json                every grant, with its status
      scenarios.json             queries, each with the moment it is asked and
                                 what a provider may and may not answer with
      reads.json                 what each reading client could be given at the
                                 export, as disclosures
      disclosure-summary.json    what each client received, from the audit log
      sharing-reports.json       onward shares a client reported
      understudy-record.json     the synthetic school record it was made from

## Using it

Import each `export.json` into an HCP Provider, establish the grants in
`grants.json`, then put each query in `scenarios.json` to it as the named
client at the stated time:

- `eligibleEntryIds`: everything the grant and purpose reach. A conformant
  response is a subset.
- `relevantEntryIds`: the eligible entries that bear on the question. Ground
  truth for scoring retrieval.
- `mustNotDisclose`: entries the grant does not reach. Returning one is a
  conformance failure.
- An `error` outcome names the code a provider should answer with.

The provider's audit log can be compared with `export.json`'s `audit`. Reads
are logged there as one plausible provider's answers, not the only correct ones.

## Reproducing it

The same parameters and Understudy build give the same files, byte for byte,
unless learner statements were worded by a model (see `manifest.json`).
