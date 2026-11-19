"""Lossless structural reader and explicit sort annotations for a bounded SMT grammar."""
from __future__ import annotations
import json
import re

LEX = re.compile(rb'[ \t\r\n]+|;[^\r\n]*|\(|\)|"(?:[^"]|"")*"|\|[^|\\]*\||[^()\s;"|]+')
NUM = re.compile(r"0|[1-9][0-9]*")
NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9-]*")


class InputError(ValueError):
    pass


def need(value, reason):
    if not value:
        raise InputError(str(reason))


def neutral(raw):
    need(raw.isascii(), "source is outside the registered ASCII fragment")
    roots = []
    stack = []
    spans = []
    pos = 0
    while pos < len(raw):
        m = LEX.match(raw, pos)
        need(m is not None, f"bad token at byte {pos}")
        token = m.group()
        end = m.end()
        if token[:1] in (b" ", b"\t", b"\r", b"\n"):
            kind = "space"
        elif token.startswith(b";"):
            kind = "comment"
        elif token == b"(":
            kind = "open"
            group = []
            (stack[-1] if stack else roots).append(group)
            stack.append(group)
        elif token == b")":
            kind = "close"
            need(stack, "unmatched close")
            stack.pop()
        else:
            kind = "atom"
            need(stack, "bare top-level token")
            stack[-1].append(token.decode("ascii"))
        spans.append([kind, pos, end])
        pos = end
    need(not stack, "open list at EOF")
    return roots, spans


def numeral(value):
    need(isinstance(value, str) and NUM.fullmatch(value), f"bad numeral {value!r}")
    return int(value)


def name(value):
    need(isinstance(value, str) and NAME.fullmatch(value), f"bad name {value!r}")
    return value


def ty(node):
    if node in ("Bool", "Int"):
        return [node.lower()]
    need(isinstance(node, list) and len(node) == 3 and node[:2] == ["_", "BitVec"],
         f"unsupported sort {node!r}")
    width = numeral(node[2])
    need(1 <= width <= 64, "bit width outside this declared fragment")
    return ["bv", width]


def rank(operator, args, env):
    if operator in env:
        expected, result = env[operator]
        need(args == expected, f"wrong arguments for {operator}")
        return result
    n = len(args)
    if operator in ("and", "or", "=>", "not"):
        need(n == 1 if operator == "not" else n >= 2, "logical arity")
        need(all(t == ["bool"] for t in args), "logical sorts")
        return ["bool"]
    if operator in ("=", "distinct"):
        need(n >= 2 and all(t == args[0] for t in args), "comparison arity or sorts")
        return ["bool"]
    if operator == "ite":
        need(n == 3 and args[0] == ["bool"] and args[1] == args[2], "ite arguments")
        return args[1]
    if operator in ("+", "-", "<=", ">=", "<", ">"):
        need(n >= (1 if operator == "-" else 2) and all(t == ["int"] for t in args),
             "integer operation arity/sorts")
        return ["int"] if operator in ("+", "-") else ["bool"]
    if operator in ("bvand", "bvor", "bvsub", "bvshl"):
        need(n == 2 and args[0] == args[1] and args[0][0] == "bv", "bit-vector arity/sorts")
        return args[0]
    raise InputError(f"unregistered operator {operator}")


def read_term(node, env, locals_):
    if isinstance(node, str):
        if node in ("true", "false"):
            return (["boolean", node == "true"], ["bool"])
        if NUM.fullmatch(node):
            return (["numeral", numeral(node)], ["int"])
        name(node)
        if node in locals_:
            sort = locals_[node]
        else:
            need(node in env and env[node][0] == [], f"unbound or unsaturated symbol {node}")
            sort = env[node][1]
        return (["name", sort, node], sort)
    need(isinstance(node, list) and node, "empty term")
    op, *children = node
    if isinstance(op, list):
        need(len(children) == 1 and len(op) >= 2 and op[0] == "_", "bad indexed operator")
        sample, xs = read_term(children[0], env, locals_)
        need(xs[0] == "bv", "indexed argument is not a bit vector")
        indices = [numeral(x) for x in op[2:]]
        if op[1] == "extract":
            need(len(indices) == 2 and 0 <= indices[1] <= indices[0] < xs[1], "invalid bit extraction")
            width = indices[0] - indices[1] + 1
        else:
            need(op[1] == "zero_extend" and len(indices) == 1, "unknown indexed operation")
            width = xs[1] + indices[0]
        need(width <= 64, "extended sort exceeds scope")
        return (["indexed", ["bv", width], op[1], indices, sample], ["bv", width])
    if op == "_":
        need(len(children) == 2 and isinstance(children[0], str) and children[0].startswith("bv"),
             "invalid bit literal")
        value, width = numeral(children[0][2:]), numeral(children[1])
        need(1 <= width <= 64 and value < 1 << width, "out of range bit literal")
        return (["bits", width, value], ["bv", width])
    head = name(op) if op not in ("=", "=>", "+", "-", "<=", ">=", "<", ">") else op
    need(head not in locals_, "cannot apply a local nonfunction")
    tagged = [read_term(x, env, locals_) for x in children]
    args = [a for a, _ in tagged]
    result = rank(head, [r for _, r in tagged], env)
    return (["app", result, head, args], result)


def typed_script(tree):
    env = {}
    typed = []
    head = ["set-logic", "ALL"]
    option = ["set-option", ":produce-models", "true"]
    need(len(tree) >= 7 and tree[:2] == [head, option] and tree[-2:] == [["check-sat"], ["exit"]],
         "invalid script header, single query, or terminal")
    seen_echo = 0
    count = 0
    for i, cmd in enumerate(tree):
        need(isinstance(cmd, list) and cmd, "invalid command")
        verb, *a = cmd
        if i < 2:
            typed.append(["logic", "ALL"] if i == 0 else ["option", ":produce-models", "true"])
        elif i >= len(tree) - 2:
            typed.append(["check"] if i == len(tree)-2 else ["exit"])
        elif verb == "declare-const":
            need(len(a) == 2 and count == 0, "invalid declaration")
            label, sort = name(a[0]), ty(a[1])
            need(label not in env, "duplicate top-level symbol")
            env[label] = ([], sort)
            typed.append(["constant", label, sort])
        elif verb == "define-fun":
            need(len(a) == 4 and count == 0, "invalid definition")
            label, inputs, result, body = name(a[0]), a[1], ty(a[2]), a[3]
            need(label not in env and isinstance(inputs, list), "invalid/duplicate definition name")
            args = []
            for pair in inputs:
                need(isinstance(pair, list) and len(pair) == 2, "invalid formal parameter")
                args.append([name(pair[0]), ty(pair[1])])
            local = dict(args)
            need(len(local) == len(args), "duplicate formal parameter")
            term, inferred = read_term(body, env, local)
            need(inferred == result, "definition has wrong result sort")
            env[label] = ([v for _, v in args], result)
            typed.append(["define", label, args, result, term])
        elif verb == "echo":
            need(len(a) == 1 and isinstance(a[0], str) and a[0].startswith('"') and
                 a[0].endswith('"') and seen_echo == 0 and not count, "invalid echo")
            seen_echo += 1
            typed.append(["echo", a[0]])
        elif verb == "assert":
            need(len(a) == 1 and seen_echo == 1, "invalid assertion")
            term, inferred = read_term(a[0], env, {})
            need(inferred == ["bool"], "non-Boolean assertion")
            count += 1
            typed.append(["assertion", term])
        else:
            raise InputError(f"unregistered or misplaced command {verb}")
    need(count == 2 and seen_echo == 1, "two assertions and one echo required")
    return typed


def lean_str(value):
    return json.dumps(value, ensure_ascii=True)


def lean_sort(raw):
    return "(Ty." + raw[0] + (" " + str(raw[1]) if len(raw) == 2 else "") + ")"


def many(parts):
    return "[" + ", ".join(parts) + "]"


def lean_term(raw):
    tag, *a = raw
    if tag == "boolean": tail = str(a[0]).lower()
    elif tag == "numeral": tail = str(a[0])
    elif tag == "bits": tail = f"{a[0]} {a[1]}"
    elif tag == "name": tail = f"{lean_sort(a[0])} {lean_str(a[1])}"
    elif tag == "app": tail = f"{lean_sort(a[0])} {lean_str(a[1])} {many(map(lean_term,a[2]))}"
    elif tag == "indexed": tail = f"{lean_sort(a[0])} {lean_str(a[1])} {many(map(str,a[2]))} {lean_term(a[3])}"
    else: raise InputError(tag)
    return "(Term." + tag + " " + tail + ")"


def lean_cmd(raw):
    tag, *a = raw
    if tag in ("logic", "echo"): tail = " " + lean_str(a[0])
    elif tag == "option": tail = " " + lean_str(a[0]) + " " + lean_str(a[1])
    elif tag == "constant": tail = " " + lean_str(a[0]) + " " + lean_sort(a[1])
    elif tag == "define":
        params = many("(" + lean_str(n) + ", " + lean_sort(t) + ")" for n,t in a[1])
        tail = f" {lean_str(a[0])} {params} {lean_sort(a[2])} {lean_term(a[3])}"
    elif tag == "assertion": tail = " " + lean_term(a[0])
    elif tag in ("check", "exit"): tail = ""
    else: raise InputError(tag)
    return "(Cmd." + tag + tail + ")"


def lean_definition(identifier, typed):
    return "def " + identifier + " : List Cmd := [\n" + ",\n".join("  "+lean_cmd(x) for x in typed) + "\n]\n"

