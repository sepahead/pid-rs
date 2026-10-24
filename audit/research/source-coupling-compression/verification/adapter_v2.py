"""Pinned transport between separately authored finite-law implementations."""

import hashlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def load(name, path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("module hash mismatch: " + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("module loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = load('candidate_frozen', ROOT / 'candidate_v2.py',
         '7235481051451579eb4a2e993c3623c662b20853b323df17f80c5012529c90f6')
R = load('reference_frozen', ROOT / 'council-verifier-v1/exact_reference.py',
         'a5f01e63cb3466dc08ec9482dc57f7394ac45e6274d16b110f00d9caf53a333f')


def compare(raw, target_size, candidate):
    ref = R.evaluate_counts(raw, target_size=target_size)
    C.require(ref['total_count'] == candidate['n'], 'reference normalization')
    C.require(set(ref['keys']) == set(candidate['nodes']), 'reference semantic keys')
    for stage in ('cumulative', 'atoms'):
        for component in ('plus', 'minus', 'net'):
            for i, key in enumerate(candidate['nodes']):
                C.require(ref[stage][component][key] == C.exact_product(candidate[stage][component][i]),
                          'independent exact product mismatch: ' + str((stage, component, key)))


def refusal(function):
    try:
        function()
    except (ValueError, R.ReferenceError):
        return
    raise ValueError('expected refusal did not occur')

