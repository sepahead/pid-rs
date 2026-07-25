#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

EXPECTED=(
  "certified-sxpid2-executable-assurance"
  "dependency-colored-sxpid-concentration"
  "ecosystem-compatibility-audit"
  "exact-log-product-sxpid2-assurance"
  "finite-alphabet-plugin-convergence"
  "formal-tool-adoption-audit"
  "foundational-shared-exclusions-pid-audit"
  "mathematical-problem-solving-workflow"
  "support-change-tolerant-averaged-sxpid-continuity"
)

actual_tex=()
while IFS= read -r path; do
  actual_tex+=("$(basename "$path" .tex)")
done < <(find audit/formal/latex -maxdepth 1 -type f -name '*.tex' -print | LC_ALL=C sort)

actual_pdf=()
while IFS= read -r path; do
  actual_pdf+=("$(basename "$path" .pdf)")
done < <(find output/pdf -maxdepth 1 -type f -name '*.pdf' -print | LC_ALL=C sort)

if [[ "${actual_tex[*]}" != "${EXPECTED[*]}" ]]; then
  echo "formal PDF set: LaTeX source inventory differs from the declared set" >&2
  exit 1
fi

if [[ "${actual_pdf[*]}" != "${EXPECTED[*]}" ]]; then
  echo "formal PDF set: rendered PDF inventory differs from the declared set" >&2
  exit 1
fi

python3 scripts/check-formal-pdf-style.py
python3 scripts/check-formal-pdf-style-self-test.py

scripts/check-certified-sxpid2-assurance-pdf.sh "$MODE"
scripts/check-dependency-colored-sxpid-pdf.sh "$MODE"
scripts/check-ecosystem-compatibility-audit-pdf.sh "$MODE"
scripts/check-exact-log-product-sxpid2-pdf.sh "$MODE"
scripts/check-finite-alphabet-convergence-pdf.sh "$MODE"
scripts/check-formal-tool-adoption-pdf.sh "$MODE"
scripts/check-foundational-sxpid-audit-pdf.sh "$MODE"
scripts/check-mathematical-workflow-pdf.sh "$MODE"
scripts/check-support-change-tolerant-sxpid-pdf.sh "$MODE"

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: every declared formal LaTeX source has one warning-free same-toolchain-reproducible PDF"
else
  echo "OK: every declared formal LaTeX source has one warning-free cross-toolchain-structurally-equivalent PDF"
fi
