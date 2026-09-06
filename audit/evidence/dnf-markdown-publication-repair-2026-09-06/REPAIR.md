# Categorical event-guide notation and archive preservation

The complete publication check failed on 6 September 2026 with 779 Markdown math findings.
All findings came from the three current event-guide documents and their three pre-acceptance
historical drafts. The staged index and captured source files stayed unchanged during that run.
The [terminal result](failed-full-pdf-set-RESULT.json), [standard output](failed-full-pdf-set-stdout.log)
and [diagnostics](failed-full-pdf-set-stderr.log) retain the actual failed check.

The current [explanation](../../formal/lean-sx-dnf-order/EXPOSITION.md),
[source map](../../formal/lean-sx-dnf-order/SOURCE_CORRESPONDENCE.md) and
[symbol map](../../formal/lean-sx-dnf-order/SYMBOL_MAP.md) now use GitHub math delimiters and
portable upright operator notation. Their formulas and the thirteen Lean targets are unchanged.
The explanation and source map also correct unsupported human-review labels: the available
paper mapping is author/model review, with no named human disposition recorded.

The three historical drafts remain byte-for-byte source evidence at their original paths. A
separate checker roster binds each complete path and SHA-256. It does not exempt a directory,
a filename pattern, or the active explanation. A changed historical byte fails the custody
check. The historical reviewer wording is part of the retained record; it supplies no human
review credit. Current prose is subject to the ordinary Markdown math checks.

The preimages directory preserves all three active documents, both checker scripts, and the
current-reader and outer packaging manifests before this correction. The reader manifest changes
only its three current-prose entries; the outer manifest changes only the corresponding reader
manifest identity. The original formal-verification manifest, proof source, targets, judges,
failed proof attempts and accepted kernel records retain their exact bytes and scoped status.

These changes concern publication and evidence presentation. They establish no new probability,
PID, estimator, runtime, numerical or application result. The failed aggregate run remains failed;
any later successful check is a separate execution with its own inputs and result.

The next complete run passed the revised workflow and results-guide PDFs and the Markdown check.
It then failed in the numerical-PDF test's accepted fixture: that temporary checkout lacked the
three historical inputs now required by the real Markdown checker. The [failure record](fixture-dependency-failure.json)
binds that separate run and its retained diagnostics. The test now copies the exact required files
into each fixture. Twelve added controls check missing files and changed bytes in both PDF gate
modes. The production Markdown and PDF checks remain unchanged. The [old fixture source](preimages/scripts/check-numerical-assurance-pdf-self-test.sh.txt)
preserves the failed dependency list. Test results are separate from this source correction.
