#!/usr/bin/env python3
"""Adversarial self-test for the separately encoded KSG SMT route.

Twelve solver-level semantic mutants remain the scientific countermodel evidence class. Bounded
lexer/parser, command-profile, exact-sort, custody-pin, immutable-snapshot, stdin-transport, and
exact-result controls are reported separately and must not inflate that 12-mutant claim.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-z3-ksg-integer-harmonic.py"
spec = importlib.util.spec_from_file_location("check_z3_ksg_harmonic", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load Z3 KSG harmonic checker")
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


MUTATIONS = (
    (
        "ksg-digamma-cancellation.smt2",
        "nonzero_cancellation_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-digamma-cancellation.smt2",
        "misbind_y_digamma_premise",
        b"(assert (= (psi y) (- (harmonic (- y 1)) euler_constant)))",
        b"(assert (= (psi y) (- (harmonic (- x 1)) euler_constant)))",
    ),
    (
        "ksg-symmetric-range.smt2",
        "nonzero_range_offset",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_min_with_left_argument",
        b"(define-fun min_xy () Int (ite (<= x y) x y))",
        b"(define-fun min_xy () Int x)",
    ),
    (
        "ksg-symmetric-range.smt2",
        "replace_max_with_left_argument",
        b"(define-fun max_xy () Int (ite (<= x y) y x))",
        b"(define-fun max_xy () Int x)",
    ),
    (
        "ksg-index-maps.smt2",
        "nonzero_exclusive_predecessor_offset",
        b"(define-fun mutation_offset () Int 0)",
        b"(define-fun mutation_offset () Int 1)",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_exclusive_x_twice",
        b"(define-fun exclusive_x () Int (+ nx 1))",
        b"(define-fun exclusive_x () Int (+ nx 2))",
    ),
    (
        "ksg-index-maps.smt2",
        "shift_anchor_inclusive_x",
        b"(define-fun inclusive_argument_x () Int inclusive_x)",
        b"(define-fun inclusive_argument_x () Int (+ inclusive_x 1))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "tighten_local_lower_bound",
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 1.0)",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_lower_harmonic_order_premise",
        b"(assert (<= h_k h_min))",
        b"(assert (<= h_min h_k))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_middle_harmonic_order_premise",
        b"(assert (<= h_min h_max))",
        b"(assert (<= h_max h_min))",
    ),
    (
        "ksg-local-bound-v4.smt2",
        "reverse_upper_harmonic_order_premise",
        b"(assert (<= h_max h_n))",
        b"(assert (<= h_n h_max))",
    ),
)

WRONG_THEOREM_BEFORE = b"""(define-fun theorem_holds () Bool
  (= (- (+ (psi k) (psi n)) (psi x) (psi y))
     (+ direct_harmonic mutation_offset)))"""
WRONG_THEOREM_AFTER = b"""(define-fun theorem_holds () Bool
  (= (+ mutation_offset (psi y))
     (- (harmonic (- y 1)) euler_constant)))"""
EXPECTED_WRONG_THEOREM_SHA256 = (
    "88e67f4289caf81770c9457d3ac77de4f470fe56d8bf3eb0a8139ac42c23ec52"
)


class SelfTestError(RuntimeError):
    """The baseline, a semantic mutant, a firewall control, or a boundary probe failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def replace_once(raw: bytes, before: bytes, after: bytes, label: str) -> bytes:
    require(raw.count(before) == 1, f"mutation anchor is absent or ambiguous: {label}")
    return raw.replace(before, after, 1)


def rebased_spec(proof_spec: object, raw: bytes) -> object:
    parsed = checker.parse_smt2(raw)
    return replace(
        proof_spec,
        sha256=checker.file_sha256(raw),
        token_stream_sha256=checker.token_stream_sha256(parsed.tokens),
    )


def expect_rejected(
    results: list[dict[str, object]],
    group: str,
    name: str,
    action: Callable[[], object],
    expected_message: str,
) -> None:
    try:
        action()
    except checker.Z3KsgHarmonicError as error:
        require(
            expected_message in str(error),
            f"{name} failed at the wrong boundary: {error!s}",
        )
    else:
        raise SelfTestError(f"firewall control was accepted: {name}")
    results.append({"group": group, "name": name, "passed": True})


def record_pass(
    results: list[dict[str, object]],
    group: str,
    name: str,
) -> None:
    results.append({"group": group, "name": name, "passed": True})


def semantic_mutation_results(
    z3: Path,
    baselines: dict[str, object],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for filename, name, before, after in MUTATIONS:
        baseline = baselines[filename]
        mutated = replace_once(baseline.raw, before, after, name)
        validated = checker._validate_semantic_mutant_for_self_test(
            baseline.spec,
            mutated,
        )
        process = checker.run_z3(z3, validated.raw)
        checker.require_exact_result(process, "sat", name)
        try:
            checker.require_unsat(z3, validated.raw, name)
        except checker.Z3KsgHarmonicError:
            pass
        else:
            raise SelfTestError(f"SAT mutation unexpectedly passed: {name}")
        results.append(
            {
                "proof": filename,
                "name": name,
                "killed": True,
                "mutant_sha256": hashlib.sha256(mutated).hexdigest(),
            }
        )
    require(len(results) == 12, "the retained semantic mutation count must remain 12")
    return results


def lexer_parser_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    expect_rejected(
        results,
        "lexer_parser",
        "source_byte_limit",
        lambda: checker.lex_smt2(b";" + b"a" * checker.MAX_SOURCE_BYTES),
        "source exceeds",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "token_count_limit",
        lambda: checker.lex_smt2(b"()" * (checker.MAX_TOKENS // 2 + 1)),
        "token limit exceeds",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "nesting_depth_limit",
        lambda: checker.parse_smt2(
            b"(" * (checker.MAX_DEPTH + 1)
            + b"x"
            + b")" * (checker.MAX_DEPTH + 1)
        ),
        "nesting depth exceeds",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "top_level_form_limit",
        lambda: checker.parse_smt2(b"(x)" * (checker.MAX_TOP_LEVEL_FORMS + 1)),
        "top-level forms",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "list_item_limit",
        lambda: checker.parse_smt2(
            b"(" + b"x " * (checker.MAX_LIST_ITEMS + 1) + b")"
        ),
        "direct items",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "atom_byte_limit",
        lambda: checker.lex_smt2(b"a" * (checker.MAX_ATOM_BYTES + 1)),
        "atom exceeds",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "string_byte_limit",
        lambda: checker.lex_smt2(b'"' + b"a" * checker.MAX_STRING_BYTES + b'"'),
        "string exceeds",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "non_ascii_byte",
        lambda: checker.lex_smt2(b"(x \xc3\xa9)"),
        "non-ASCII",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "nul_control_byte",
        lambda: checker.lex_smt2(b"(x\x00)"),
        "control byte",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "del_control_byte",
        lambda: checker.lex_smt2(b"(x\x7f)"),
        "DEL",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "unterminated_string",
        lambda: checker.lex_smt2(b'(set-info :category "crafted)'),
        "unterminated SMT string",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "backslash_string_escape",
        lambda: checker.lex_smt2(b'(set-info :category "craft\\ed")'),
        "unsupported backslash",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "quoted_symbol",
        lambda: checker.lex_smt2(b"(|theorem_holds|)"),
        "unsupported quoted or escaped syntax",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "unclosed_list",
        lambda: checker.parse_smt2(b"(x"),
        "unclosed",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "unexpected_close",
        lambda: checker.parse_smt2(b")"),
        "unexpected ')'",
    )
    expect_rejected(
        results,
        "lexer_parser",
        "top_level_atom",
        lambda: checker.parse_smt2(b"x"),
        "top-level form must be a list",
    )
    return results


def profile_type_controls(digamma: object) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    raw = digamma.raw
    proof_spec = digamma.spec

    def reject_source(name: str, mutated: bytes, message: str) -> None:
        expect_rejected(
            results,
            "profile_type",
            name,
            lambda: checker._validate_semantic_mutant_for_self_test(
                proof_spec,
                mutated,
            ),
            message,
        )

    reject_source(
        "smuggled_positive_assertion",
        replace_once(
            raw,
            b"(check-sat)",
            b"(assert theorem_holds)\n(check-sat)",
            "smuggled positive assertion",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "command_after_exit",
        raw + b"\n(assert theorem_holds)\n",
        "ordered command profile mismatch",
    )
    reject_source(
        "whitespace_split_quantifier_command",
        replace_once(
            raw,
            b"(check-sat)",
            b"( forall ((q Int)) true)\n(check-sat)",
            "whitespace quantifier command",
        ),
        "unsupported command 'forall'",
    )
    reject_source(
        "include_command",
        replace_once(
            raw,
            b"(check-sat)",
            b'(include "other.smt2")\n(check-sat)',
            "include command",
        ),
        "unsupported command 'include'",
    )
    reject_source(
        "check_sat_assuming_command",
        replace_once(
            raw,
            b"(check-sat)",
            b"(check-sat-assuming ())",
            "check-sat-assuming command",
        ),
        "unsupported command 'check-sat-assuming'",
    )
    reject_source(
        "get_model_command",
        replace_once(
            raw,
            b"(check-sat)",
            b"(get-model)\n(check-sat)",
            "get-model command",
        ),
        "unsupported command 'get-model'",
    )
    reject_source(
        "push_command",
        replace_once(
            raw,
            b"(check-sat)",
            b"( push 1 )\n(check-sat)",
            "push command",
        ),
        "unsupported command 'push'",
    )
    reject_source(
        "extra_check_sat",
        replace_once(
            raw,
            b"(check-sat)",
            b"(check-sat)\n(check-sat)",
            "extra check-sat",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "missing_exit",
        replace_once(raw, b"(exit)", b"", "missing exit"),
        "ordered command profile mismatch",
    )
    reject_source(
        "wrong_logic",
        replace_once(
            raw,
            b"(set-logic QF_UFLIRA)",
            b"(set-logic ALL)",
            "wrong logic",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "reordered_declarations",
        replace_once(
            raw,
            b"(declare-const x Int)\n(declare-const y Int)",
            b"(declare-const y Int)\n(declare-const x Int)",
            "reordered declarations",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "renamed_declared_symbol",
        replace_once(
            raw,
            b"(declare-const x Int)",
            b"(declare-const q Int)",
            "renamed symbol",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "wrong_declared_sort",
        replace_once(
            raw,
            b"(declare-const x Int)",
            b"(declare-const x Real)",
            "wrong declared sort",
        ),
        "ordered command profile mismatch",
    )
    reject_source(
        "non_nullary_definition",
        replace_once(
            raw,
            b"(define-fun direct_harmonic () Real",
            b"(define-fun direct_harmonic ((q Real)) Real",
            "non-nullary definition",
        ),
        "only nullary define-fun",
    )
    reject_source(
        "undefined_expression_symbol",
        replace_once(
            raw,
            b"(= (- (+ (psi k) (psi n))",
            b"(= (- (+ (psi q) (psi n))",
            "undefined expression symbol",
        ),
        "undefined symbol 'q'",
    )
    reject_source(
        "function_application_arity",
        replace_once(
            raw,
            b"(= (- (+ (psi k) (psi n))",
            b"(= (- (+ (psi k n) (psi n))",
            "function application arity",
        ),
        "'psi' expects 1 arguments",
    )
    reject_source(
        "plus_operator_arity",
        replace_once(
            raw,
            b"(+ (harmonic (- k 1)) (harmonic (- n 1)))",
            b"(+ (harmonic (- k 1)) (harmonic (- n 1)) 0.0)",
            "plus operator arity",
        ),
        "+ expects exactly two arguments",
    )
    reject_source(
        "minus_operator_arity",
        replace_once(
            raw,
            b"(- (+ (psi k) (psi n)) (psi x) (psi y))",
            b"(- (+ (psi k) (psi n)) (psi x) (psi y) 0.0)",
            "minus operator arity",
        ),
        "- expects one, two, or three arguments",
    )
    reject_source(
        "not_operator_arity",
        replace_once(
            raw,
            checker.NEGATIVE_ASSERTION,
            b"(assert (not theorem_holds theorem_holds))",
            "not operator arity",
        ),
        "not expects one argument",
    )
    reject_source(
        "mixed_equality_sorts",
        replace_once(
            raw,
            b"(+ direct_harmonic mutation_offset)))",
            b"k))",
            "mixed equality sorts",
        ),
        "operand sorts differ",
    )
    reject_source(
        "non_bool_assertion",
        replace_once(
            raw,
            b"(assert (>= n 2))",
            b"(assert n)",
            "non-bool assertion",
        ),
        "assertion has non-Bool sort Int",
    )
    reject_source(
        "string_expression",
        replace_once(
            raw,
            b"(assert (>= n 2))",
            b'(assert "n")',
            "string expression",
        ),
        "strings are not expressions",
    )
    reject_source(
        "quantifier_expression",
        replace_once(
            raw,
            b"(assert (>= n 2))",
            b"(assert ( forall ((q Int)) true))",
            "quantifier expression",
        ),
        "unsupported operator 'forall'",
    )
    reject_source(
        "let_expression",
        replace_once(
            raw,
            b"(assert (>= n 2))",
            b"(assert (let ((q n)) (>= q 2)))",
            "let expression",
        ),
        "unsupported operator 'let'",
    )
    reject_source(
        "or_expression",
        replace_once(
            raw,
            b"(assert (>= n 2))",
            b"(assert (or (>= n 2) (>= n 2)))",
            "or expression",
        ),
        "unsupported operator 'or'",
    )
    return results


def custody_transport_controls(
    z3: Path,
    digamma: object,
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    raw = digamma.raw
    proof_spec = digamma.spec

    whitespace_mutant = raw + b" "
    expect_rejected(
        results,
        "custody_transport",
        "raw_pin_rejects_whitespace_change",
        lambda: checker.validate_pinned_negative(proof_spec, whitespace_mutant),
        "raw digest mismatch",
    )
    require(
        checker.token_stream_sha256(checker.parse_smt2(whitespace_mutant).tokens)
        == proof_spec.token_stream_sha256,
        "whitespace control must leave the token-stream digest unchanged",
    )

    token_mutant = replace_once(
        raw,
        b"(define-fun mutation_offset () Real 0.0)",
        b"(define-fun mutation_offset () Real 0.00)",
        "token pin mutation",
    )
    raw_only_rebase = replace(
        proof_spec,
        sha256=checker.file_sha256(token_mutant),
    )
    expect_rejected(
        results,
        "custody_transport",
        "token_pin_rejects_raw_only_rebase",
        lambda: checker.validate_pinned_negative(raw_only_rebase, token_mutant),
        "token-stream digest mismatch",
    )

    smuggled = replace_once(
        raw,
        b"(check-sat)",
        b"(assert theorem_holds)\n(check-sat)",
        "rebased smuggled positive",
    )
    expect_rejected(
        results,
        "custody_transport",
        "dual_rebase_rejects_smuggled_positive",
        lambda: checker.validate_pinned_negative(rebased_spec(proof_spec, smuggled), smuggled),
        "ordered command profile mismatch",
    )

    split_quantifier = replace_once(
        raw,
        b"(check-sat)",
        b"( forall ((q Int)) true)\n(check-sat)",
        "rebased whitespace quantifier",
    )
    expect_rejected(
        results,
        "custody_transport",
        "dual_rebase_rejects_whitespace_quantifier",
        lambda: checker.validate_pinned_negative(
            rebased_spec(proof_spec, split_quantifier),
            split_quantifier,
        ),
        "unsupported command 'forall'",
    )

    with tempfile.TemporaryDirectory(prefix="pid-ksg-z3-snapshot-") as directory:
        path = Path(directory) / proof_spec.filename
        path.write_bytes(raw)
        captured = checker.validate_pinned_negative(
            proof_spec,
            checker._read_regular_file_once(path, checker.MAX_SOURCE_BYTES),
        )
        path.write_bytes(captured.positive_raw)
        checker.require_unsat(
            z3,
            captured.raw,
            "immutable-byte snapshot after path overwrite",
        )
    record_pass(
        results,
        "custody_transport",
        "path_overwrite_cannot_change_captured_solver_input",
    )

    with tempfile.TemporaryDirectory(prefix="pid-ksg-z3-stdin-") as directory:
        fake = Path(directory) / "fake-z3"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "raw = sys.stdin.buffer.read()\n"
            "if sys.argv[1:] != ['-smt2', '-in'] or raw != b'(check-sat)\\n':\n"
            "    print('transport mismatch', file=sys.stderr)\n"
            "    raise SystemExit(9)\n"
            "print('unsat')\n",
            encoding="utf-8",
        )
        fake.chmod(0o700)
        checker.require_exact_result(
            checker.run_z3(fake, b"(check-sat)\n"),
            "unsat",
            "stdin transport",
        )
    record_pass(results, "custody_transport", "solver_uses_exact_stdin_transport")

    anomalous_results = (
        (
            "extra_stdout_rejected",
            subprocess.CompletedProcess([], 0, b"unsat\nsat\n", b""),
            "did not return exact UNSAT",
        ),
        (
            "nonempty_stderr_rejected",
            subprocess.CompletedProcess([], 0, b"unsat\n", b"warning\n"),
            "did not return exact UNSAT",
        ),
        (
            "nonzero_exit_rejected",
            subprocess.CompletedProcess([], 7, b"unsat\n", b""),
            "did not return exact UNSAT",
        ),
        (
            "wrong_polarity_rejected",
            subprocess.CompletedProcess([], 0, b"sat\n", b""),
            "did not return exact UNSAT",
        ),
    )
    for name, process, message in anomalous_results:
        expect_rejected(
            results,
            "custody_transport",
            name,
            lambda process=process: checker.require_exact_result(
                process,
                "unsat",
                name,
            ),
            message,
        )

    with tempfile.TemporaryDirectory(prefix="pid-ksg-z3-timeout-") as directory:
        sleeper = Path(directory) / "fake-z3-sleeper"
        sleeper.write_text(
            "#!/usr/bin/env python3\n"
            "import time\n"
            "time.sleep(1.0)\n",
            encoding="utf-8",
        )
        sleeper.chmod(0o700)
        try:
            checker.run_z3(
                sleeper,
                b"(check-sat)\n",
                timeout_seconds=0.01,
            )
        except subprocess.TimeoutExpired:
            pass
        else:
            raise SelfTestError("solver timeout control did not time out")
    record_pass(results, "custody_transport", "solver_timeout_propagates_fail_closed")
    return results


def retained_dual_rebase_boundary(
    z3: Path,
    baselines: dict[str, object],
) -> dict[str, object]:
    digamma = baselines["ksg-digamma-cancellation.smt2"]
    wrong = replace_once(
        digamma.raw,
        WRONG_THEOREM_BEFORE,
        WRONG_THEOREM_AFTER,
        "well-typed wrong theorem",
    )
    require(
        hashlib.sha256(wrong).hexdigest() == EXPECTED_WRONG_THEOREM_SHA256,
        "wrong-theorem boundary digest drifted",
    )
    deliberately_rebased = rebased_spec(digamma.spec, wrong)
    accepted = checker.validate_pinned_negative(deliberately_rebased, wrong)
    checker.require_satisfiable_positive_preflight(z3, accepted)
    checker.require_unsat(z3, accepted.raw, "deliberately dual-rebased wrong theorem")

    still_killed = 0
    for filename, name, before, after in MUTATIONS:
        baseline = baselines[filename]
        base_raw = wrong if filename == digamma.spec.filename else baseline.raw
        mutated = replace_once(base_raw, before, after, f"dual-rebase boundary {name}")
        validated = checker._validate_semantic_mutant_for_self_test(
            baseline.spec,
            mutated,
        )
        checker.require_exact_result(
            checker.run_z3(z3, validated.raw),
            "sat",
            f"dual-rebase boundary {name}",
        )
        still_killed += 1
    require(
        still_killed == len(MUTATIONS) == 12,
        "wrong-theorem boundary must retain all 12 old SAT mutation outcomes",
    )
    return {
        "count": 1,
        "name": "well_typed_wrong_theorem_after_deliberate_raw_and_token_pin_rebase",
        "mutant_sha256": hashlib.sha256(wrong).hexdigest(),
        "mutant_token_stream_sha256": accepted.token_stream_sha256,
        "positive_preflight": "sat",
        "negated_obligation": "unsat",
        "retained_semantic_mutants_still_killed": still_killed,
        "interpretation": (
            "This is a retained adequacy boundary, not a passing verification lens: the bounded "
            "profile and type checker reject command smuggling but do not determine that a "
            "well-typed theorem is the intended theorem. Deliberately rebasing both correlated "
            "pins plus approving the statement can still produce green; human statement review "
            "and independent formal/compiled routes remain required."
        ),
    }


def main() -> int:
    try:
        z3 = checker.find_z3()
        verification = checker.verify_all(z3)
        baselines = {proof.spec.filename: proof for proof in verification.proofs}

        semantic_results = semantic_mutation_results(z3, baselines)
        firewall_results = (
            lexer_parser_controls()
            + profile_type_controls(baselines["ksg-digamma-cancellation.smt2"])
            + custody_transport_controls(
                z3,
                baselines["ksg-digamma-cancellation.smt2"],
            )
        )
        group_counts: dict[str, int] = {}
        for result in firewall_results:
            group = str(result["group"])
            group_counts[group] = group_counts.get(group, 0) + 1
        boundary = retained_dual_rebase_boundary(z3, baselines)

        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-self-test/v3",
            "status": "passed",
            "z3_observed_identity": {
                "resolved_path": verification.identity.resolved_path,
                "sha256": verification.identity.sha256,
                "version": verification.identity.version,
                "interpretation": "observed identity only; not authenticity or attestation",
            },
            "checker_source_sha256": checker.file_sha256(CHECKER.read_bytes()),
            "self_test_source_sha256": checker.file_sha256(
                Path(__file__).resolve().read_bytes()
            ),
            "semantic_mutations_killed": len(semantic_results),
            "semantic_mutations": semantic_results,
            "firewall_controls_passed": len(firewall_results),
            "firewall_control_group_counts": group_counts,
            "firewall_controls": firewall_results,
            "retained_dual_rebase_boundary": boundary,
            "accounting_boundary": (
                "Only the 12 solver-SAT theorem/premise/index/bound mutants count as semantic "
                "countermodel evidence. Lexer/parser/profile/type/pin/snapshot/transport/result "
                "controls test checker fail-closed behavior and are reported separately. The "
                "retained dual-rebase witness is a negative adequacy result, not a killed mutant."
            ),
            "scientific_boundary": (
                "The semantic mutations expose changed cancellation, premise binding, min/max, "
                "exclusive successor, inclusive identity, predecessor consequences, explicit "
                "harmonic-order premises, and the local bound as SAT. They do not validate the "
                "analytic digamma premise, harmonic finite-sum recurrence or monotonicity, count "
                "geometry, estimator, support, floating-point, PID, or Rust claims."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        SelfTestError,
        checker.Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG harmonic self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
