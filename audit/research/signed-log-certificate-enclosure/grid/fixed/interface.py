"""Render only the bounded, ordinary Lean tactic bodies in the fixed template."""

import json
import re
import unicodedata


class Refusal(ValueError):
    pass


def need(test, reason):
    if not test:
        raise Refusal(reason)


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON member")
        result[key] = value
    return result


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


SLOTS = ('ceiling_le', 'width_residue', 'sharp_max', 'two_grid', 'next_width', 'both_padded', 'next_padding', 'unit_cell', 'counted_envelope')
PLAIN = {
    "rfl", "omega", "grind", "simp", "simp_all", "assumption", "constructor",
    "trivial", "ac_rfl", "contradiction", "decide", "left", "right", "exact_mod_cast",
}
HEADS = {
    "intro", "intros", "exact", "apply", "refine", "rw", "rwa", "simp", "simp_all",
    "simp_arith", "unfold", "change", "show", "have", "suffices", "let", "obtain",
    "rcases", "cases", "case", "induction", "by_cases", "by_contra", "subst",
    "revert", "specialize", "rename_i", "generalize", "congr", "constructor", "calc",
    "conv_lhs", "conv_rhs", "next", "repeat", "first", "skip", "grind", "omega",
}
DENIED = {
    "axiom", "axioms", "theorem", "lemma", "def", "abbrev", "instance", "opaque",
    "example", "unsafe", "partial", "sorry", "sorryAx", "admit", "native_decide",
    "implemented_by", "extern", "run_tac", "run_cmd", "elab", "elab_rules", "syntax",
    "macro", "macro_rules", "tactic", "eval", "set_option", "import", "namespace",
    "section", "end", "initialize", "attribute", "termination_by", "decreasing_by",
    "where", "ofReduceBool", "ofReduceNat", "trustCompiler", "IO", "Lean", "System",
    "run", "do", "include", "omit", "open", "mutual", "scoped", "command", "unsafeCast",
    "export", "universe", "variable", "deriving", "local", "infix", "notation",
}
PUNCT = set(" _'.,()[]{}:<>!?=+*/%|&^-@→←↔∧∨¬∃∀≤≥≠·⟨⟩⊢⇒↦ℕℤ₀₁₂₃₄₅₆₇₈₉")
WORDS = re.compile(r"[^\W\d]\w*'?|\w+_\w+", re.UNICODE)


def body(lines):
    need(type(lines) is list and 0 < len(lines) <= 700, "body line count")
    result = []
    for line in lines:
        need(type(line) is str and line and line.rstrip() == line and len(line) <= 2048 and
             all(ch not in line for ch in (chr(9), chr(10), chr(13))),
             "line form")
        need(unicodedata.normalize("NFC", line) == line and
             all(ch in PUNCT or ch.isascii() and ch.isalnum() or
                 unicodedata.name(ch, "").startswith("GREEK SMALL LETTER") for ch in line),
             "line alphabet")
        indent = len(line) - len(line.lstrip(" "))
        need(indent <= 40 and indent % 2 == 0, "indentation")
        s = line.lstrip(" ")
        need(not any(t in s for t in ("--", "/-", "-/", "..", ":::", ";;")),
             "comment or compound syntax")
        words = set(WORDS.findall(s))
        need(not (words & DENIED), "forbidden declaration or execution")
        # Tactic blocks start at a trusted tactic head or occupy a local subproof.
        # All source lines are additionally indented inside the fixed theorem by the renderer.
        head = s.split(" ", 1)[0]
        if head == "·":
            tail = s[1:].lstrip()
            need(not tail or tail in PLAIN or tail.split(" ",1)[0] in HEADS, "bullet tactic")
        elif head not in HEADS and s not in PLAIN:
            # An ordinary calc calculation supplies a local proof of its displayed relation.
            need(indent > 0 and " := " in s and any(x in s for x in ("≤", "≥", "=", "<", ">")),
                 "tactic or calc row")
        if "by" in words:
            need(s.endswith(":= by") or " := by " in s or
                 re.search(r"\(by (?:omega|rfl|decide|simp)\)",s) is not None,
                 "local proof boundary")
        result.append("  " + line)
    return "\n".join(result)


def render(data, template):
    need(0 < len(data) <= 98304, "payload bytes")
    try:
        value = json.loads(data, object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise Refusal("payload JSON") from error
    need(type(value) is dict and set(value) == set(SLOTS), "exact proof fields")
    need(canonical(value) == data, "canonical payload")
    result = template
    for slot in SLOTS:
        marker = "@@" + slot + "@@"
        need(result.count(marker) == 1, "bound template marker")
        result = result.replace(marker, body(value[slot]))
    return result
