# Provenance and custody route memo

## Route record

- **Claim:** SX-CERTIFIED-AVERAGED-PID2-001 revision 1
- **Route:** method provenance, source binding, and external-custody boundary
- **Date:** 2026-07-24
- **Disposition:** method provenance mapped; local source drift detection present; independent
  custody open

## Method provenance

The categorical shared-exclusions event construction is attributed to Makkeh, Gutknecht, and
Wibral (2021). The project does not rename the functional, define “colored PID,” or claim a new PID
measure in this packet.

The exact-count schemas, fixed two-source executable encoding, certificate, independent verifier,
resource policy, and mutation workflow are project-defined assurance artifacts.

## Local binding route

The producer embeds a 16-member source manifest, including its `Cargo.lock`, README, build script,
and all Rust source modules. The certificate reports the length-delimited manifest digest and
lockfile digest.

The independent verifier:

1. reads only fixed relative manifest members;
2. rejects symlinks and nonregular files;
3. bounds every member and the total;
4. checks file identity before, during, and after each read;
5. recomputes the producer's domain-separated manifest encoding;
6. compares it with the certificate; and
7. recomputes the manifest after containment verification to detect concurrent drift.

The verifier also reports its own source SHA-256 and checks its bytes again after verification.

## What the hashes establish

If the hash functions and reads behave correctly, a matching digest establishes byte equality with
the named local files under the declared encoding.

It does not establish:

- who authored the files;
- that the source came from an authentic repository;
- that the source was independently reviewed;
- that an executable was compiled from it;
- that native archives match it;
- that another machine has the same files; or
- that the source is scientifically correct.

## Repository binding and remaining custody gap

The independent verifier and qualification harness are committed unchanged at
`b8b9a48b88cb28d812d8cbd70b8f999a3bac5a8e`. Their checked-out SHA-256 values match values
recomputed from `git show` of that commit. [../bindings.md](../bindings.md) also records the exact
current 16-member producer source-manifest digest. The verifier bytes are already retrievable by
that commit. This packet and its final manifest value are not bound to that earlier commit; their
repository address is the first later public commit whose tree contains these exact bytes. This
memo deliberately neither embeds nor pre-claims that enclosing commit, which avoids circular
self-reference. Public availability must be checked from repository history.

Before such publication, the packet is not publicly retrievable. After publication, ordinary Git
repository source identity still does not establish independent custody, authorship, executable
identity, or an external transparency timestamp. Those are explicit open obligations, not
clerical omissions.

## External closure procedure

Independent custody requires another person or organization to:

1. obtain the committed source through an independently selected channel;
2. record the exact commit and file digests before execution;
3. review the claim boundary and verifier source;
4. replay the qualification and one or more new hidden inputs;
5. retain commands, stdout/stderr, exit status, environment identity, and produced hashes;
6. sign or otherwise bind the evidence through their own process; and
7. report failures and abstentions without threshold adjustment after unblinding.

Until then, “independently implemented” describes the code path. It does not mean independently
authored, independently reviewed, or independently executed.

## Distribution boundary

The source-only route avoids distributing the Rug/MPFR/GMP-linked executable. Any producer binary
distribution requires a separate license review, an LGPL-compliant source/relinking route, and
artifact/native-archive evidence. The Python verifier does not change those producer obligations.
