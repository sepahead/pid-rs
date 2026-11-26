"""Restore the exact originally checked sources, including six terminal line feeds and the original product notation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path


EXPECTED_ARCHIVE_MANIFEST = 'ad453bfe63403946f2df7168ebd9974a676a813f3483d5738eb80c483148576e'
EXPECTED_CHANGED = {'FIRST.md', 'NUMERICAL-PACKET.md', 'candidate/nested.py',
                    'define_fixtures.py', 'direct.py', 'judge.py'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def restore(source, output):
    manifest = source / 'MANIFEST.json'
    require(sha256(manifest.read_bytes()).hexdigest() == EXPECTED_ARCHIVE_MANIFEST, 'original manifest')
    originals = json.loads(manifest.read_bytes())
    transport = json.loads((source / 'TRANSPORT.json').read_bytes())
    require(set(transport) == EXPECTED_CHANGED and len(originals) == 15, 'source roster')
    output.mkdir(exist_ok=False)
    for name, record in originals.items():
        data = (source / name).read_bytes()
        if name in transport:
            correction = transport[name]
            fields = {'public_sha256', 'original_sha256', 'append_hex'}
            if name == 'FIRST.md':
                fields.add('without_product_sign_sha256')
            require(set(correction) == fields, 'transport fields')
            require(correction['append_hex'] == '0a' and correction['original_sha256'] == record['sha256'], name)
            require(sha256(data).hexdigest() == correction['public_sha256'] and data.endswith(b'\n')
                    and not data.endswith(b'\n\n'), 'public source: ' + name)
            if name == 'FIRST.md':
                public_product = '[L_j precedes α]·(v_j-v_{j-1})'.encode()
                original_product = '[L_j precedes α](v_j-v_{j-1})'.encode()
                require(data.count(public_product) == 1 and original_product not in data,
                        'unique explicit multiplication sign')
                data = data.replace(public_product, original_product)
                require(sha256(data).hexdigest() == correction['without_product_sign_sha256'],
                        'source before the visible multiplication sign')
            data += b'\n'
        require(len(data) == record['bytes'] and sha256(data).hexdigest() == record['sha256'], 'original source: ' + name)
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    (output / 'MANIFEST.json').write_bytes(manifest.read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path, help='a new directory')
    args = parser.parse_args()
    restore(args.source, args.output)
