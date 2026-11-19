"""Mathematical reference for positive original three-source count-table inputs.

A table is a tuple of (key, positive count) pairs. A key is a tuple of three
source states followed by a target state. Each state is a tuple of ASCII tokens.
The command enumerates its fixed finite example and reads no external data.
"""
from hashlib import sha256
from itertools import combinations, product
import json


DEFINITION = "makkeh-gutknecht-wibral-2021-empirical-sxpid3-nats-v1"
SCHEMA = "pid-rs/categorical-sxpid3-count-table/v1"
PREFIX = ('{"definition_revision":"' + DEFINITION + '","rows":[').encode("ascii")
SUFFIX = ('],"schema":"' + SCHEMA + '","sources":3,"units":"nats"}\n').encode("ascii")
TOKEN_ALPHABET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-")
MAX_ROWS = 1024
MAX_BYTES = 4 * 1024 * 1024
MAX_TOTAL = 2**8192 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal_string(value):
    digits = []
    while value:
        value, remainder = divmod(value, 10)
        digits.append(chr(48 + remainder))
    return "".join(reversed(digits))


def count_value(text):
    require(type(text) is str and 1 <= len(text) <= 4096, "count string length")
    require("1" <= text[0] <= "9", "positive initial digit")
    value = 0
    for digit in text:
        require("0" <= digit <= "9", "decimal digit")
        value = 10 * value + ord(digit) - 48
        require(value <= MAX_TOTAL, "count width")
    return value


def check_key(key):
    require(type(key) is tuple and len(key) == 4, "four-state joint key")
    for state in key:
        require(type(state) is tuple and 1 <= len(state) <= 64, "state length")
        for token in state:
            require(type(token) is str and 1 <= len(token) <= 128
                    and all(char in TOKEN_ALPHABET for char in token), "ASCII token")


def encode(rows):
    """Return the exact canonical byte vector for an admitted finite table."""
    require(type(rows) is tuple and 1 <= len(rows) <= MAX_ROWS, "support size")
    total = 0
    prior = None
    parts = [PREFIX]
    available = MAX_BYTES - len(PREFIX) - len(SUFFIX)
    for index, row in enumerate(rows):
        require(type(row) is tuple and len(row) == 2, "row")
        key, count = row
        check_key(key)
        require(prior is None or prior < key, "strict joint key order")
        prior = key
        require(type(count) is int and 0 < count <= MAX_TOTAL - total, "positive total width")
        total += count
        record = {"count": decimal_string(count), "source_states": key[:3], "target_state": key[3]}
        chunk = json.dumps(record, ensure_ascii=True, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("ascii")
        separator = b"," if index else b""
        available -= len(separator) + len(chunk)
        require(available >= 0, "complete input length")
        parts.extend((separator, chunk))
    parts.append(SUFFIX)
    return b"".join(parts)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "repeated object member")
        result[key] = value
    return result


def decode(data):
    """Read a canonical positive input as an ordered tuple of count-table rows."""
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES and data.endswith(b"\n"),
            "input length and line feed")
    parsed = json.loads(data[:-1].decode("ascii"), object_pairs_hook=unique_object)
    require(type(parsed) is dict
            and set(parsed) == {"definition_revision","rows","schema","sources","units"},
            "top-level members")
    require(parsed["definition_revision"] == DEFINITION and parsed["schema"] == SCHEMA
            and type(parsed["sources"]) is int and parsed["sources"] == 3
            and parsed["units"] == "nats", "schema identity")
    raw_rows = parsed["rows"]
    require(type(raw_rows) is list and 1 <= len(raw_rows) <= MAX_ROWS, "support size")
    rows = []
    for raw in raw_rows:
        require(type(raw) is dict and set(raw) == {"count","source_states","target_state"},
                "row members")
        sources = raw["source_states"]
        require(type(sources) is list and len(sources) == 3, "three source states")
        states = (*sources, raw["target_state"])
        require(all(type(state) is list and 1 <= len(state) <= 64 for state in states),
                "state arrays")
        key = tuple(tuple(state) for state in states)
        rows.append((key, count_value(raw["count"])))
    rows = tuple(rows)
    require(encode(rows) == data, "canonical spelling")
    return rows


def positive_census():
    """Enumerate the 29,403 tables specified in the accompanying report."""
    states = (("A",), ("A", "A"), ("AA",))
    keys = tuple(product(states, repeat=4))
    seen = set()
    digest = sha256()
    longest = 0
    sizes = [0, 0]
    for size in (1, 2):
        for support in combinations(keys, size):
            for counts in product((1, 9, 10), repeat=size):
                rows = tuple(zip(support, counts))
                wire = encode(rows)
                require(decode(wire) == rows and wire not in seen, "finite inverse or uniqueness")
                seen.add(wire)
                digest.update(len(wire).to_bytes(4, "big"))
                digest.update(wire)
                longest = max(longest, len(wire))
                sizes[size - 1] += 1
    require(sizes == [243, 29160] and len(seen) == 29403, "finite enumeration")
    return {"one_row_tables": sizes[0], "two_row_tables": sizes[1],
            "distinct_wires":len(seen), "max_wire_bytes":longest,
            "ordered_u32be_framed_sha256":digest.hexdigest()}


if __name__ == "__main__":
    print(json.dumps(positive_census(), sort_keys=True))
