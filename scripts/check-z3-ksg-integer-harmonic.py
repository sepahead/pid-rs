#!/usr/bin/env python3
"""Check separately encoded exact KSG harmonic/index obligations with pinned Z3.

The SMT route proves four-term cancellation under explicit positive-integer digamma instances,
the min/max range identity and source symmetry for an arbitrary harmonic-value function, the
exclusive/inclusive index maps, and the local full-tail bound under explicit harmonic-order
instances. It does not prove the digamma premise, define or prove monotonicity of harmonic finite
sums, or establish neighbor geometry, estimator behavior, support, floating point, PID semantics,
or Rust refinement. The finite-sum definition, recurrence, monotonicity, and unconditional
rational harmonic bound are checked separately by Lean.

The accepted SMT-LIB surface is intentionally much smaller than general SMT-LIB 2.6. A bounded
ASCII lexer, S-expression parser, ordered per-proof command profile, and exact-sort checker reject
commands or syntax outside the four reviewed snapshots before any bytes reach Z3. Raw-file and
comment/whitespace-insensitive token-stream digests are correlated custody checks, not independent
proofs. Deliberately rebasing both pins and the reviewed statements remains a human review cut.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PROOF_DIR = ROOT / "audit/formal/z3-ksg-harmonic"
EXPECTED_Z3_VERSION = "Z3 version 4.16.0 - 64 bit"
TIMEOUT_SECONDS = 30

MAX_SOURCE_BYTES = 16_384
MAX_TOKENS = 2_048
MAX_DEPTH = 16
MAX_TOP_LEVEL_FORMS = 64
MAX_LIST_ITEMS = 64
MAX_ATOM_BYTES = 64
MAX_STRING_BYTES = 128

TOKEN_STREAM_DOMAIN = b"pid-rs/smtlib-token-stream/v1\0"
NEGATIVE_ASSERTION = b"(assert (not theorem_holds))"
POSITIVE_ASSERTION = b"(assert theorem_holds)"
ASCII_WHITESPACE = frozenset(b" \t\r\n")
TOKEN_TAGS = {
    "open": b"L",
    "close": b"R",
    "atom": b"A",
    "string": b"S",
}
SIMPLE_SYMBOL = re.compile(rb"[A-Za-z_][A-Za-z0-9_]*\Z")
INTEGER_LITERAL = re.compile(rb"(?:0|[1-9][0-9]*)\Z")
REAL_LITERAL = re.compile(rb"(?:0|[1-9][0-9]*)\.[0-9]+\Z")
BUILTIN_SYMBOLS = frozenset({"+", "-", "<", "<=", "=", ">=", "and", "ite", "not"})
SORTS = frozenset({"Bool", "Int", "Real"})


class Z3KsgHarmonicError(RuntimeError):
    """A source, grammar, profile, pin, solver preflight, or exact result check failed."""


@dataclass(frozen=True)
class Token:
    kind: str
    raw: bytes
    start: int
    end: int


@dataclass(frozen=True)
class SExpr:
    kind: str
    raw: bytes | None
    items: tuple["SExpr", ...]
    start: int
    end: int


@dataclass(frozen=True)
class SymbolType:
    arguments: tuple[str, ...]
    result: str


@dataclass(frozen=True)
class ProofSpec:
    filename: str
    sha256: str
    token_stream_sha256: str
    ordered_profile: tuple[str, ...]
    obligation: str
    typed_premise: str


@dataclass(frozen=True)
class ParsedSource:
    raw: bytes
    tokens: tuple[Token, ...]
    forms: tuple[SExpr, ...]


@dataclass(frozen=True)
class ValidatedProof:
    spec: ProofSpec
    raw: bytes
    positive_raw: bytes
    raw_sha256: str
    token_stream_sha256: str


@dataclass(frozen=True)
class Z3Identity:
    resolved_path: str
    sha256: str
    version: str


@dataclass(frozen=True)
class VerificationResult:
    identity: Z3Identity
    proofs: tuple[ValidatedProof, ...]


COMMON_N_K_X_Y_PROFILE = (
    "set-info::smt-lib-version:2.6",
    'set-info::category:"crafted"',
    "set-logic:QF_UFLIRA",
    "declare-const:n:Int",
    "declare-const:k:Int",
    "declare-const:x:Int",
    "declare-const:y:Int",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
)

DIGAMMA_PROFILE = COMMON_N_K_X_Y_PROFILE + (
    "declare-fun:harmonic:(Int)->Real",
    "declare-fun:psi:(Int)->Real",
    "declare-const:euler_constant:Real",
    "assert",
    "assert",
    "assert",
    "assert",
    "define-fun:direct_harmonic:()->Real",
    "define-fun:mutation_offset:()->Real",
    "define-fun:theorem_holds:()->Bool",
    "assert",
    "check-sat",
    "exit",
)

INDEX_PROFILE = (
    "set-info::smt-lib-version:2.6",
    'set-info::category:"crafted"',
    "set-logic:QF_UFLIRA",
    "declare-const:n:Int",
    "declare-const:k:Int",
    "declare-const:nx:Int",
    "declare-const:ny:Int",
    "declare-const:inclusive_x:Int",
    "declare-const:inclusive_y:Int",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "assert",
    "declare-fun:harmonic:(Int)->Real",
    "define-fun:exclusive_x:()->Int",
    "define-fun:exclusive_y:()->Int",
    "define-fun:inclusive_argument_x:()->Int",
    "define-fun:inclusive_argument_y:()->Int",
    "define-fun:exclusive_direct:()->Real",
    "define-fun:exclusive_count_form:()->Real",
    "define-fun:inclusive_direct:()->Real",
    "define-fun:inclusive_count_form:()->Real",
    "define-fun:mutation_offset:()->Int",
    "define-fun:theorem_holds:()->Bool",
    "assert",
    "check-sat",
    "exit",
)

LOCAL_BOUND_PROFILE = COMMON_N_K_X_Y_PROFILE + (
    "declare-fun:harmonic:(Int)->Real",
    "define-fun:min_xy:()->Int",
    "define-fun:max_xy:()->Int",
    "define-fun:h_k:()->Real",
    "define-fun:h_n:()->Real",
    "define-fun:h_min:()->Real",
    "define-fun:h_max:()->Real",
    "assert",
    "assert",
    "assert",
    "define-fun:direct_value:()->Real",
    "define-fun:range_value:()->Real",
    "define-fun:full_tail:()->Real",
    "define-fun:mutation_offset:()->Real",
    "define-fun:theorem_holds:()->Bool",
    "assert",
    "check-sat",
    "exit",
)

SYMMETRIC_RANGE_PROFILE = COMMON_N_K_X_Y_PROFILE + (
    "declare-fun:harmonic:(Int)->Real",
    "define-fun:min_xy:()->Int",
    "define-fun:max_xy:()->Int",
    "define-fun:min_yx:()->Int",
    "define-fun:max_yx:()->Int",
    "define-fun:direct_xy:()->Real",
    "define-fun:direct_yx:()->Real",
    "define-fun:range_xy:()->Real",
    "define-fun:range_yx:()->Real",
    "define-fun:mutation_offset:()->Real",
    "define-fun:theorem_holds:()->Bool",
    "assert",
    "check-sat",
    "exit",
)


PROOFS = (
    ProofSpec(
        filename="ksg-digamma-cancellation.smt2",
        sha256="8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4",
        token_stream_sha256="46d504aea109ae875598404a7d680e8dceb93635a4f91ab3d11bd51b08de5292",
        ordered_profile=DIGAMMA_PROFILE,
        obligation="four-term exact-real cancellation at four positive integer arguments",
        typed_premise=(
            "four asserted instances psi(m)=harmonic(m-1)-euler_constant; analytic truth open"
        ),
    ),
    ProofSpec(
        filename="ksg-index-maps.smt2",
        sha256="71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1",
        token_stream_sha256="7e655ca85f042c4275042fc8e9368a72aef10b1e0cbde3dce7b87c67769a7f2c",
        ordered_profile=INDEX_PROFILE,
        obligation="exclusive count+1 and anchor-inclusive identity maps with exact domains",
        typed_premise="declared integer count bounds; neighbor production and geometry open",
    ),
    ProofSpec(
        filename="ksg-local-bound-v4.smt2",
        sha256="33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31",
        token_stream_sha256="9f20298f0fb6a630167995b96638f6446a07e4005b9bc1a265a136302a73f284",
        ordered_profile=LOCAL_BOUND_PROFILE,
        obligation=(
            "direct/range equality and full-tail bound under explicit local harmonic-order premises"
        ),
        typed_premise=(
            "H(k-1)<=H(min-1)<=H(max-1)<=H(n-1); universal harmonic monotonicity is proved in Lean"
        ),
    ),
    ProofSpec(
        filename="ksg-symmetric-range.smt2",
        sha256="add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9",
        token_stream_sha256="e7d9605f13384e1f7d04b0f1b6b4a61848adc70a6ae1925a06eeeddca2475aa1",
        ordered_profile=SYMMETRIC_RANGE_PROFILE,
        obligation="min/max range reassociation and source exchange for arbitrary harmonic values",
        typed_premise="positive integer index order only; harmonic values are uninterpreted",
    ),
)


def file_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Z3KsgHarmonicError(message)


def _append_token(tokens: list[Token], kind: str, raw: bytes, start: int, end: int) -> None:
    require(len(tokens) < MAX_TOKENS, f"SMT token limit exceeds {MAX_TOKENS}")
    tokens.append(Token(kind=kind, raw=raw, start=start, end=end))


def lex_smt2(raw: bytes) -> tuple[Token, ...]:
    """Lex the deliberately bounded ASCII subset; comments and whitespace emit no tokens."""

    require(len(raw) <= MAX_SOURCE_BYTES, f"SMT source exceeds {MAX_SOURCE_BYTES} bytes")
    for offset, byte in enumerate(raw):
        require(byte < 128, f"SMT source contains non-ASCII byte at offset {offset}")
        require(
            byte >= 32 or byte in ASCII_WHITESPACE,
            f"SMT source contains disallowed control byte at offset {offset}",
        )
        require(byte != 127, f"SMT source contains DEL at offset {offset}")

    tokens: list[Token] = []
    cursor = 0
    while cursor < len(raw):
        byte = raw[cursor]
        if byte in ASCII_WHITESPACE:
            cursor += 1
            continue
        if byte == ord(";"):
            newline = raw.find(b"\n", cursor + 1)
            cursor = len(raw) if newline < 0 else newline + 1
            continue
        if byte == ord("("):
            _append_token(tokens, "open", b"(", cursor, cursor + 1)
            cursor += 1
            continue
        if byte == ord(")"):
            _append_token(tokens, "close", b")", cursor, cursor + 1)
            cursor += 1
            continue
        if byte == ord('"'):
            start = cursor
            cursor += 1
            while cursor < len(raw):
                require(
                    raw[cursor] != ord("\\"),
                    f"SMT string contains unsupported backslash at offset {cursor}",
                )
                if raw[cursor] == ord('"'):
                    if cursor + 1 < len(raw) and raw[cursor + 1] == ord('"'):
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            else:
                raise Z3KsgHarmonicError(
                    f"unterminated SMT string beginning at offset {start}"
                )
            lexeme = raw[start:cursor]
            require(
                len(lexeme) <= MAX_STRING_BYTES,
                f"SMT string exceeds {MAX_STRING_BYTES} bytes",
            )
            _append_token(tokens, "string", lexeme, start, cursor)
            continue

        start = cursor
        while (
            cursor < len(raw)
            and raw[cursor] not in ASCII_WHITESPACE
            and raw[cursor] not in b"();"
        ):
            cursor += 1
        lexeme = raw[start:cursor]
        require(lexeme, f"empty SMT atom at offset {start}")
        require(
            len(lexeme) <= MAX_ATOM_BYTES,
            f"SMT atom exceeds {MAX_ATOM_BYTES} bytes",
        )
        require(
            b"|" not in lexeme and b"\\" not in lexeme and b'"' not in lexeme,
            f"SMT atom uses unsupported quoted or escaped syntax at offset {start}",
        )
        _append_token(tokens, "atom", lexeme, start, cursor)

    return tuple(tokens)


def _parse_node(
    tokens: tuple[Token, ...],
    index: int,
    depth: int,
) -> tuple[SExpr, int]:
    require(index < len(tokens), "unexpected end of SMT token stream")
    token = tokens[index]
    if token.kind == "close":
        raise Z3KsgHarmonicError(f"unexpected ')' at byte offset {token.start}")
    if token.kind in {"atom", "string"}:
        return (
            SExpr(
                kind=token.kind,
                raw=token.raw,
                items=(),
                start=token.start,
                end=token.end,
            ),
            index + 1,
        )

    require(token.kind == "open", f"unknown SMT token kind: {token.kind}")
    require(depth < MAX_DEPTH, f"SMT nesting depth exceeds {MAX_DEPTH}")
    children: list[SExpr] = []
    cursor = index + 1
    while True:
        require(cursor < len(tokens), f"unclosed '(' at byte offset {token.start}")
        if tokens[cursor].kind == "close":
            close = tokens[cursor]
            return (
                SExpr(
                    kind="list",
                    raw=None,
                    items=tuple(children),
                    start=token.start,
                    end=close.end,
                ),
                cursor + 1,
            )
        require(
            len(children) < MAX_LIST_ITEMS,
            f"SMT list exceeds {MAX_LIST_ITEMS} direct items",
        )
        child, cursor = _parse_node(tokens, cursor, depth + 1)
        children.append(child)


def parse_smt2(raw: bytes) -> ParsedSource:
    tokens = lex_smt2(raw)
    forms: list[SExpr] = []
    cursor = 0
    while cursor < len(tokens):
        require(
            len(forms) < MAX_TOP_LEVEL_FORMS,
            f"SMT source exceeds {MAX_TOP_LEVEL_FORMS} top-level forms",
        )
        form, cursor = _parse_node(tokens, cursor, 0)
        require(form.kind == "list", "every SMT top-level form must be a list")
        forms.append(form)
    return ParsedSource(raw=raw, tokens=tokens, forms=tuple(forms))


def token_stream_sha256(tokens: tuple[Token, ...]) -> str:
    """Hash token kind and raw lexeme with unambiguous, domain-separated framing."""

    digest = hashlib.sha256()
    digest.update(TOKEN_STREAM_DOMAIN)
    digest.update(struct.pack(">I", len(tokens)))
    for token in tokens:
        tag = TOKEN_TAGS[token.kind]
        digest.update(tag)
        digest.update(struct.pack(">I", len(token.raw)))
        digest.update(token.raw)
    return digest.hexdigest()


def _atom(node: SExpr, label: str) -> bytes:
    require(node.kind == "atom" and node.raw is not None, f"{label} must be an atom")
    return node.raw


def _string(node: SExpr, label: str) -> bytes:
    require(
        node.kind == "string" and node.raw is not None,
        f"{label} must be a string literal",
    )
    return node.raw


def _list(node: SExpr, label: str) -> tuple[SExpr, ...]:
    require(node.kind == "list", f"{label} must be a list")
    return node.items


def _sort(node: SExpr, label: str) -> str:
    raw = _atom(node, label)
    decoded = raw.decode("ascii")
    require(decoded in SORTS, f"{label} uses unsupported sort {decoded!r}")
    return decoded


def _symbol(node: SExpr, label: str) -> str:
    raw = _atom(node, label)
    require(SIMPLE_SYMBOL.fullmatch(raw) is not None, f"{label} is not a simple symbol")
    decoded = raw.decode("ascii")
    require(decoded not in BUILTIN_SYMBOLS, f"{label} shadows builtin {decoded!r}")
    require(decoded not in SORTS, f"{label} shadows sort {decoded!r}")
    return decoded


def _head(form: SExpr, label: str) -> str:
    items = _list(form, label)
    require(items, f"{label} cannot be empty")
    return _atom(items[0], f"{label} head").decode("ascii")


def _command_profile(form: SExpr, index: int) -> str:
    label = f"top-level form {index}"
    items = _list(form, label)
    require(items, f"{label} cannot be empty")
    head = _atom(items[0], f"{label} head")
    if head == b"set-info":
        require(len(items) == 3, f"{label}: set-info must have two arguments")
        key = _atom(items[1], f"{label} set-info key")
        if key == b":smt-lib-version":
            value = _atom(items[2], f"{label} SMT-LIB version")
        elif key == b":category":
            value = _string(items[2], f"{label} category")
        else:
            raise Z3KsgHarmonicError(f"{label}: unsupported set-info key {key!r}")
        return f"set-info:{key.decode('ascii')}:{value.decode('ascii')}"
    if head == b"set-logic":
        require(len(items) == 2, f"{label}: set-logic must have one argument")
        logic = _atom(items[1], f"{label} logic").decode("ascii")
        return f"set-logic:{logic}"
    if head == b"declare-const":
        require(len(items) == 3, f"{label}: declare-const must have two arguments")
        name = _symbol(items[1], f"{label} declared constant")
        result = _sort(items[2], f"{label} declared constant sort")
        return f"declare-const:{name}:{result}"
    if head == b"declare-fun":
        require(len(items) == 4, f"{label}: declare-fun must have three arguments")
        name = _symbol(items[1], f"{label} declared function")
        arguments = tuple(
            _sort(item, f"{label} function argument sort")
            for item in _list(items[2], f"{label} function arguments")
        )
        result = _sort(items[3], f"{label} function result sort")
        return f"declare-fun:{name}:({','.join(arguments)})->{result}"
    if head == b"define-fun":
        require(len(items) == 5, f"{label}: define-fun must have four arguments")
        name = _symbol(items[1], f"{label} defined function")
        arguments = _list(items[2], f"{label} function parameters")
        require(not arguments, f"{label}: only nullary define-fun is accepted")
        result = _sort(items[3], f"{label} function result sort")
        return f"define-fun:{name}:()->{result}"
    if head == b"assert":
        require(len(items) == 2, f"{label}: assert must have one argument")
        return "assert"
    if head in {b"check-sat", b"exit"}:
        require(len(items) == 1, f"{label}: {head.decode()} takes no arguments")
        return head.decode("ascii")
    raise Z3KsgHarmonicError(
        f"{label}: unsupported command {head.decode('ascii', errors='replace')!r}"
    )


def _infer_expression(node: SExpr, symbols: dict[str, SymbolType], label: str) -> str:
    if node.kind == "string":
        raise Z3KsgHarmonicError(f"{label}: strings are not expressions")
    if node.kind == "atom":
        raw = _atom(node, label)
        if INTEGER_LITERAL.fullmatch(raw):
            return "Int"
        if REAL_LITERAL.fullmatch(raw):
            return "Real"
        require(SIMPLE_SYMBOL.fullmatch(raw) is not None, f"{label}: invalid expression atom")
        name = raw.decode("ascii")
        signature = symbols.get(name)
        require(signature is not None, f"{label}: undefined symbol {name!r}")
        require(
            not signature.arguments,
            f"{label}: function {name!r} requires {len(signature.arguments)} arguments",
        )
        return signature.result

    items = _list(node, label)
    require(items, f"{label}: empty expression list")
    operator = _atom(items[0], f"{label} operator").decode("ascii")
    arguments = items[1:]

    if operator in symbols:
        signature = symbols[operator]
        require(
            len(arguments) == len(signature.arguments),
            f"{label}: {operator!r} expects {len(signature.arguments)} arguments, "
            f"got {len(arguments)}",
        )
        actual = tuple(
            _infer_expression(argument, symbols, f"{label} {operator} argument")
            for argument in arguments
        )
        require(
            actual == signature.arguments,
            f"{label}: {operator!r} argument sorts are {actual}, expected "
            f"{signature.arguments}",
        )
        return signature.result

    require(operator in BUILTIN_SYMBOLS, f"{label}: unsupported operator {operator!r}")
    if operator == "not":
        require(len(arguments) == 1, f"{label}: not expects one argument")
        result = _infer_expression(arguments[0], symbols, f"{label} not argument")
        require(result == "Bool", f"{label}: not argument must be Bool, got {result}")
        return "Bool"
    if operator == "and":
        require(len(arguments) >= 2, f"{label}: and expects at least two arguments")
        for argument in arguments:
            result = _infer_expression(argument, symbols, f"{label} and argument")
            require(result == "Bool", f"{label}: and argument must be Bool, got {result}")
        return "Bool"
    if operator == "ite":
        require(len(arguments) == 3, f"{label}: ite expects three arguments")
        condition = _infer_expression(arguments[0], symbols, f"{label} ite condition")
        left = _infer_expression(arguments[1], symbols, f"{label} ite true branch")
        right = _infer_expression(arguments[2], symbols, f"{label} ite false branch")
        require(condition == "Bool", f"{label}: ite condition must be Bool")
        require(left == right, f"{label}: ite branch sorts differ: {left} and {right}")
        return left
    if operator == "+":
        require(len(arguments) == 2, f"{label}: + expects exactly two arguments")
    elif operator == "-":
        require(
            1 <= len(arguments) <= 3,
            f"{label}: - expects one, two, or three arguments",
        )
    else:
        require(len(arguments) == 2, f"{label}: {operator} expects two arguments")

    sorts = tuple(
        _infer_expression(argument, symbols, f"{label} {operator} argument")
        for argument in arguments
    )
    require(len(set(sorts)) == 1, f"{label}: {operator} operand sorts differ: {sorts}")
    operand_sort = sorts[0]
    if operator in {"+", "-"}:
        require(
            operand_sort in {"Int", "Real"},
            f"{label}: {operator} operands must be numeric, got {operand_sort}",
        )
        return operand_sort
    if operator == "=":
        return "Bool"
    require(
        operand_sort in {"Int", "Real"},
        f"{label}: {operator} operands must be numeric, got {operand_sort}",
    )
    return "Bool"


def _require_new_symbol(
    symbols: dict[str, SymbolType],
    name: str,
    signature: SymbolType,
    label: str,
) -> None:
    require(name not in symbols, f"{label}: duplicate symbol {name!r}")
    symbols[name] = signature


def _validate_types(forms: tuple[SExpr, ...]) -> None:
    symbols: dict[str, SymbolType] = {}
    for index, form in enumerate(forms):
        label = f"top-level form {index}"
        items = _list(form, label)
        head = _atom(items[0], f"{label} head")
        if head in {b"set-info", b"set-logic", b"check-sat", b"exit"}:
            continue
        if head == b"declare-const":
            name = _symbol(items[1], f"{label} declared constant")
            result = _sort(items[2], f"{label} declared constant sort")
            _require_new_symbol(symbols, name, SymbolType((), result), label)
            continue
        if head == b"declare-fun":
            name = _symbol(items[1], f"{label} declared function")
            arguments = tuple(
                _sort(item, f"{label} function argument sort")
                for item in _list(items[2], f"{label} function arguments")
            )
            result = _sort(items[3], f"{label} function result sort")
            _require_new_symbol(
                symbols,
                name,
                SymbolType(arguments, result),
                label,
            )
            continue
        if head == b"define-fun":
            name = _symbol(items[1], f"{label} defined function")
            require(
                not _list(items[2], f"{label} function parameters"),
                f"{label}: only nullary define-fun is accepted",
            )
            expected = _sort(items[3], f"{label} defined function result sort")
            actual = _infer_expression(items[4], symbols, f"{label} definition")
            require(
                actual == expected,
                f"{label}: definition sort is {actual}, declared {expected}",
            )
            _require_new_symbol(symbols, name, SymbolType((), expected), label)
            continue
        require(head == b"assert", f"{label}: unsupported typed command")
        actual = _infer_expression(items[1], symbols, f"{label} assertion")
        require(actual == "Bool", f"{label}: assertion has non-Bool sort {actual}")

    theorem = symbols.get("theorem_holds")
    require(
        theorem == SymbolType((), "Bool"),
        "theorem_holds must be exactly one nullary Bool definition",
    )


def _matches_atom(node: SExpr, expected: bytes) -> bool:
    return node.kind == "atom" and node.raw == expected


def _require_terminal_form(forms: tuple[SExpr, ...], polarity: str) -> SExpr:
    require(len(forms) >= 3, "SMT source lacks the three terminal commands")
    assertion_items = _list(forms[-3], "terminal assertion")
    require(
        len(assertion_items) == 2 and _matches_atom(assertion_items[0], b"assert"),
        "third-last command must be the terminal assertion",
    )
    if polarity == "negative":
        body = _list(assertion_items[1], "negative terminal assertion body")
        require(
            len(body) == 2
            and _matches_atom(body[0], b"not")
            and _matches_atom(body[1], b"theorem_holds"),
            "negative terminal assertion must be exactly (assert (not theorem_holds))",
        )
    elif polarity == "positive":
        require(
            _matches_atom(assertion_items[1], b"theorem_holds"),
            "positive terminal assertion must be exactly (assert theorem_holds)",
        )
    else:
        raise Z3KsgHarmonicError(f"unknown terminal polarity {polarity!r}")
    require(
        _head(forms[-2], "penultimate command") == "check-sat"
        and len(forms[-2].items) == 1,
        "penultimate command must be exactly (check-sat)",
    )
    require(
        _head(forms[-1], "last command") == "exit" and len(forms[-1].items) == 1,
        "last command must be exactly (exit)",
    )
    return forms[-3]


def _validate_unpinned(
    spec: ProofSpec,
    raw: bytes,
    polarity: str,
) -> ParsedSource:
    parsed = parse_smt2(raw)
    profile = tuple(
        _command_profile(form, index) for index, form in enumerate(parsed.forms)
    )
    require(
        profile == spec.ordered_profile,
        f"{spec.filename}: ordered command profile mismatch: got {profile!r}",
    )
    _validate_types(parsed.forms)
    _require_terminal_form(parsed.forms, polarity)
    return parsed


def _derive_positive(
    spec: ProofSpec,
    negative: ParsedSource,
) -> bytes:
    terminal = _require_terminal_form(negative.forms, "negative")
    positive = (
        negative.raw[: terminal.start]
        + POSITIVE_ASSERTION
        + negative.raw[terminal.end :]
    )
    _validate_unpinned(spec, positive, "positive")
    return positive


def validate_pinned_negative(spec: ProofSpec, raw: bytes) -> ValidatedProof:
    actual_raw_sha256 = file_sha256(raw)
    require(
        actual_raw_sha256 == spec.sha256,
        f"{spec.filename}: raw digest mismatch: got {actual_raw_sha256}",
    )
    parsed = _validate_unpinned(spec, raw, "negative")
    actual_token_sha256 = token_stream_sha256(parsed.tokens)
    require(
        actual_token_sha256 == spec.token_stream_sha256,
        f"{spec.filename}: token-stream digest mismatch: got {actual_token_sha256}",
    )
    return ValidatedProof(
        spec=spec,
        raw=raw,
        positive_raw=_derive_positive(spec, parsed),
        raw_sha256=actual_raw_sha256,
        token_stream_sha256=actual_token_sha256,
    )


def _validate_semantic_mutant_for_self_test(
    spec: ProofSpec,
    raw: bytes,
) -> ValidatedProof:
    """Validate the grammar/profile/types of a deliberate mutant while bypassing custody pins."""

    parsed = _validate_unpinned(spec, raw, "negative")
    return ValidatedProof(
        spec=spec,
        raw=raw,
        positive_raw=_derive_positive(spec, parsed),
        raw_sha256=file_sha256(raw),
        token_stream_sha256=token_stream_sha256(parsed.tokens),
    )


def _read_regular_file_once(path: Path, maximum_bytes: int) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    else:
        require(not path.is_symlink(), f"file is symlinked: {path}")
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        require(stat.S_ISREG(metadata.st_mode), f"file is not regular: {path}")
        require(
            metadata.st_size <= maximum_bytes,
            f"file exceeds {maximum_bytes} bytes: {path}",
        )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            require(total <= maximum_bytes, f"file exceeds {maximum_bytes} bytes: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def require_exact_proof_set() -> None:
    require(
        PROOF_DIR.is_dir() and not PROOF_DIR.is_symlink(),
        f"proof directory is missing or symlinked: {PROOF_DIR}",
    )
    expected = {spec.filename for spec in PROOFS}
    actual = {entry.name for entry in PROOF_DIR.iterdir()}
    require(
        actual == expected,
        f"proof manifest mismatch: missing={sorted(expected - actual)}, "
        f"unexpected={sorted(actual - expected)}",
    )


def load_proof_snapshot() -> tuple[ValidatedProof, ...]:
    """Load each proof once, validate stored bytes, and never pass proof paths to Z3."""

    require_exact_proof_set()
    snapshot = tuple(
        validate_pinned_negative(
            spec,
            _read_regular_file_once(PROOF_DIR / spec.filename, MAX_SOURCE_BYTES),
        )
        for spec in PROOFS
    )
    # A second observation detects a concurrent manifest change during the bounded load. The four
    # pinned byte strings, rather than a claim of an atomic filesystem snapshot, are authoritative.
    require_exact_proof_set()
    return snapshot


def find_z3(explicit: str | None = None) -> Path:
    candidate = explicit if explicit is not None else shutil.which("z3")
    require(candidate is not None, "z3 executable was not found on PATH")
    path = Path(candidate).expanduser().resolve()
    require(
        path.is_file() and os.access(path, os.X_OK), f"z3 is not executable: {path}"
    )
    return path


def _sha256_regular_file(path: Path) -> str:
    digest = hashlib.sha256()
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        require(stat.S_ISREG(os.fstat(descriptor).st_mode), f"file is not regular: {path}")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def z3_version(z3: Path) -> str:
    process = subprocess.run(
        [str(z3), "--version"],
        capture_output=True,
        text=False,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )
    require(
        process.returncode == 0
        and process.stdout == (EXPECTED_Z3_VERSION + "\n").encode("ascii")
        and process.stderr == b"",
        "unexpected z3 version result: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )
    return process.stdout.decode("ascii").strip()


def observe_z3_identity(z3: Path) -> Z3Identity:
    return Z3Identity(
        resolved_path=str(z3),
        sha256=_sha256_regular_file(z3),
        version=z3_version(z3),
    )


def run_z3(
    z3: Path,
    source: bytes,
    *,
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[bytes]:
    """Run an already captured byte string through stdin; no proof path is reopened."""

    return subprocess.run(
        [str(z3), "-smt2", "-in"],
        input=source,
        capture_output=True,
        text=False,
        timeout=timeout_seconds,
        check=False,
    )


def require_exact_result(
    process: subprocess.CompletedProcess[bytes],
    expected: str,
    label: str,
) -> None:
    expected_bytes = (expected + "\n").encode("ascii")
    require(
        process.returncode == 0
        and process.stdout == expected_bytes
        and process.stderr == b"",
        f"{label} did not return exact {expected.upper()}: "
        f"exit={process.returncode}, stdout={process.stdout!r}, stderr={process.stderr!r}",
    )


def require_unsat(z3: Path, source: bytes, label: str) -> None:
    require_exact_result(run_z3(z3, source), "unsat", label)


def require_satisfiable_positive_preflight(
    z3: Path,
    proof: ValidatedProof,
) -> None:
    require_exact_result(
        run_z3(z3, proof.positive_raw),
        "sat",
        f"{proof.spec.filename} positive preflight",
    )


def verify_all(z3: Path) -> VerificationResult:
    identity_before = observe_z3_identity(z3)
    snapshot = load_proof_snapshot()
    for proof in snapshot:
        require_satisfiable_positive_preflight(z3, proof)
        require_unsat(z3, proof.raw, proof.spec.filename)
    identity_after = observe_z3_identity(z3)
    require(
        identity_after == identity_before,
        "observed Z3 path/hash/version changed during verification",
    )
    return VerificationResult(identity=identity_before, proofs=snapshot)


def main() -> int:
    try:
        z3 = find_z3()
        verification = verify_all(z3)
        result = {
            "schema": "pid-rs/z3-ksg-integer-harmonic-check/v3",
            "status": "passed",
            "z3_observed_identity": {
                "resolved_path": verification.identity.resolved_path,
                "sha256": verification.identity.sha256,
                "version": verification.identity.version,
                "interpretation": (
                    "observed executable identity only; not provenance, authenticity, or an "
                    "attestation, and not an atomic execute-by-hash guarantee"
                ),
            },
            "checker_source_sha256": file_sha256(Path(__file__).resolve().read_bytes()),
            "parser_limits": {
                "maximum_atom_bytes": MAX_ATOM_BYTES,
                "maximum_depth": MAX_DEPTH,
                "maximum_list_items": MAX_LIST_ITEMS,
                "maximum_source_bytes": MAX_SOURCE_BYTES,
                "maximum_string_bytes": MAX_STRING_BYTES,
                "maximum_tokens": MAX_TOKENS,
                "maximum_top_level_forms": MAX_TOP_LEVEL_FORMS,
            },
            "proofs": [
                {
                    "filename": proof.spec.filename,
                    "raw_sha256": proof.raw_sha256,
                    "token_stream_sha256": proof.token_stream_sha256,
                    "top_level_form_count": len(proof.spec.ordered_profile),
                    "obligation": proof.spec.obligation,
                    "typed_premise": proof.spec.typed_premise,
                    "positive_preflight": "sat",
                    "negated_obligation": "unsat",
                }
                for proof in verification.proofs
            ],
            "custody_boundary": (
                "Raw and token-stream SHA-256 pins are correlated custody checks. The token pin "
                "excludes comments and whitespace and makes a semantic edit require two explicit "
                "pin updates; it is not a second proof. The parser/profile/type firewall prevents "
                "unreviewed general SMT-LIB commands. A deliberate dual rebase of pins and a "
                "well-typed but wrong reviewed statement remains a human/code-review cut."
            ),
            "scientific_boundary": (
                "Quantifier-free exact Int/Real/uninterpreted-function obligations only. The "
                "local bound uses explicit harmonic-order premises; finite-sum recurrence and "
                "universal rational harmonic monotonicity are separately kernel-checked in Lean; "
                "the statements, signs, maps, and analytic premise remain shared human cuts. "
                "Digamma truth, count geometry, binary64, estimators, support, PID semantics, "
                "Rust refinement, calibration, and consumers remain outside scope."
            ),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        Z3KsgHarmonicError,
    ) as error:
        print(f"Z3 KSG integer-harmonic check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
