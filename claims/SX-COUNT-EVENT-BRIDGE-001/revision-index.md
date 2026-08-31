# Revision index for SX-COUNT-EVENT-BRIDGE-001

| Revision | Claim | Obligations | Routes | Decision | Status |
|---|---|---|---|---|---|
| 1 | [claim-v1.md](claim-v1.md) | [obligations.md](obligations.md) | [routes.md](routes.md) | Not issued; revision superseded before acceptance | Superseded, explicitly bannered, and retained for audit only |
| 2 | [claim-v2.md](claim-v2.md) | [obligations-v2.md](obligations-v2.md) | [routes-v2.md](routes-v2.md) | [decision-v2.md](decision-v2.md) | Complete within bounded supplied-count formal-semantics scope |

[Decision revision 2](decision-v2.md) is the current adjudication pointer for this claim ID. Its
word “complete” is limited to the supplied-count, two-source formal-semantics scope stated there;
it is not an end-to-end executable, estimator, population, release, or consumer certificate.

Revision 2 changes the count quantifier only: zero-count complete keys are permitted, positive
total is required, and logarithms are restricted to positive support. The exact correction and
falsifying sparse table are retained under `failures/`. Revision-1 files retain their historical
mathematical and route content, with only explicit superseded labels and whitespace normalization
added to prevent stale-agent use.
