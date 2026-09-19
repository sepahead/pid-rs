# Publication-check corrections

These corrections concern the publication tools. They change no PID definition, mathematical
statement, proof, manuscript or selected PDF. The source review identified two defects before
the new papers entered the public tree.

## Exact observation identity

The old reference check used Python dictionary equality. Python treats `13.0 == 13` and
`1 == True` as true. A rebound expected record could therefore change the type of the page count
or first-page flag and still satisfy that comparison. Separate PDF and TeX byte checks remained
in force. This witness does not show acceptance of a different PDF or a false theorem.

The [old source](negative-observation-equality-v1/builder-before-correction.py.txt) and
[minimal witnesses](negative-observation-equality-v1/witnesses.json) are inert historical
evidence. Do not use them as current acceptance code. Their purpose is to make the defect and
its limited scope reproducible without running a PDF tool.

The corrected predicate compares the complete key sets, list lengths and order, exact node
types, and values recursively. Dictionary keys must be strings. Floating-point values must be
finite. PDF bytes must also match. The same type comparison checks the two fresh observations.
The existing JSON reader separately rejects duplicate keys and nonfinite JSON constants.

Nineteen new controls exercise this combined predicate. They include both current reference
observations, nested numeric type substitutions, missing and extra keys, list and string changes,
nonfinite values, and an altered PDF byte. Together with the previous 56 controls, all 75 passed
in normal and optimized Python. These controls do not parse PDFs. Exact native reproduction
has its own outcome in the [publication record](PUBLICATION_OBSERVATION.json).

The first exact build after this repair produced the selected PDF bytes, then failed the typed
comparison. A separately recorded read of that existing PDF found 63 destination names stored
as the reader's `TextStringObject` subclass. Their JSON strings matched the reference, but the
in-memory observation had not completed the conversion to JSON types. The
[failed builder](negative-observation-equality-v1/builder-before-text-projection.py.txt) and
[observed witness](negative-observation-equality-v1/text-projection-witness.json) retain this
result. Nineteen native commands had run; the remaining planned calls were not issued.

The observer now requires each destination name to be text and extracts its native string
payload. It does not stringify numbers, bytes or other objects, and it does not convert expected
JSON values. Twenty further controls call the actual observer with a finite reader substitute.
They check native and subclass strings, Unicode and ordering, an overridden display conversion,
invalid inputs, strict expected types and altered PDF bytes. Bypassing the conversion must
reproduce the original type failure. All 95 controls passed in each Python mode. The substitute
parses no PDF syntax; native reproduction remains a separate check.

## Preflight before registered work

The aggregate formerly checked the derivative registrations after four bias calls. A missing
derivative input could thus consume fresh bias work before the aggregate stopped. All 29 required
bias and derivative fields are now checked before any of the eight registered calls. Call order
and the original caller deadlines stay unchanged.

The expanded dispatch suite runs the complete early source block with inert call recorders.
It checks absent and empty values for all 29 fields, all eight failure positions, mode separation,
argument forwarding and explicit cross-toolchain refusals. Its negative control moves the guards
back to their old position and observes four bias calls before rejection. The current position
must reject the same missing field with zero calls. All 79 cases passed in each Python mode.
The [old aggregate](negative-observation-equality-v1/aggregate-before-preflight.sh.txt) is retained
as inert source evidence.

These tests establish their stated finite software predicates. They do not establish PDF safety
for every viewer, mathematical correctness, estimator calibration or useful learning behavior.
