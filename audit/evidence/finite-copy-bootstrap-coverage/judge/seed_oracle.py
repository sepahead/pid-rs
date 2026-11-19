"""Index-only V1 comparator. Does not reference labels, entropy, or coverage."""
import hashlib
import json

MASK64 = (1 << 64) - 1
GAMMA = 0x9E3779B97F4A7C15

def nth_word(seed, ordinal):
    """Closed-form counter for the zero-based output word, with unsigned wrapping."""
    z = (seed + (ordinal + 1) * GAMMA) & MASK64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return z ^ (z >> 31)

def index_codes(seed=7):
    # For four starts the unsigned rejection threshold ((-4 mod 2^64) % 4) is zero.
    codes = []
    for replicate in range(200):
        code = 0
        for offset in range(4):
            code = (code << 2) | (nth_word(seed, 4 * replicate + offset) % 4)
        codes.append(code)
    return codes

def integer(value, description):
    if type(value) is not int:
        raise ValueError(description + ": integer primitive required")
    return value

def compare_codes(observed, expected):
    if type(observed) is not list or len(observed) != 200:
        raise ValueError("schedule length must be 200")
    if len(expected) != 200:
        raise ValueError("expected schedule length must be 200")
    for i, (a, b) in enumerate(zip(observed, expected)):
        if not 0 <= integer(a, "schedule code") < 256:
            raise ValueError("schedule code outside four-index domain")
        if a != b:
            raise ValueError("seed-7 schedule mismatch at replicate " + str(i))

def frozen_record():
    codes = index_codes()
    return {"schema":"pid-copy-v1-fixed-index-oracle-v2", "source_commit":"1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20",
            "seed":7, "row_count":4, "replicates":200, "block_size":1,
            "code_order":"first index in most significant two bits", "schedule_codes":codes,
            "packed_bytes_sha256":hashlib.sha256(bytes(codes)).hexdigest(),
            "scope":"index sequence only; no law, statistic, outer samples or coverage evaluated"}

if __name__ == "__main__":
    print(json.dumps(frozen_record(),sort_keys=True,separators=(",",":")))

