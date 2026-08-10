# Retained revision-1 count-quantifier correction

## Failure

Revision 1 stated that an “exact nonzero natural-number count” was assigned to every complete
categorical key. Read literally, that requires full empirical support: every cell count is
strictly positive.

That prose contradicted all three of the revision-1 theorem design choices:

1. the quantified object was an unrestricted function from complete keys to `Nat`;
2. the only global premise was positive **total** count; and
3. `positiveSupport` existed precisely to exclude zero-count cells from logarithms and averaging.

It also excluded ordinary sparse categorical histograms without mathematical justification.

## Falsifying witness

Any nonempty table with at least one observed and one unobserved complete key satisfies positive
total count but falsifies “nonzero at every key.” For example, on a binary key space, assign count
one to `(0,0,0)` and zero to the other seven keys. The empirical law is valid, and its logarithm
domain is the singleton positive support.

## Correction

Revision 2 quantifies an arbitrary natural-valued count function, requires only positive total,
and restricts all local logarithms and averages to strictly positive count support. No theorem is
weakened: this is the quantification expressed by the checked signature from the outset.

## Preservation decision

`claim-v1.md` retains the revision-1 mathematical proposal, but now carries an explicit
superseded-status banner so direct readers cannot mistake it for current authority. `claim-v2.md`
supersedes it and links this note, so the correction is reviewable rather than silently replacing
the historical target.
