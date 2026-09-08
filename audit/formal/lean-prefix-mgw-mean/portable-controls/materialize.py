#!/usr/bin/env python3
"""Materialize exact inert control inputs into a fresh ignored directory.

This new distribution setup is source-reviewed only. It runs no controls or Lean.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile

HERE = Path(__file__).resolve().parent
MANIFEST_SHA = '1da681a27a9f9e54af4ceba44c9bea4fdf3e5b675a9d1e124af3338ee84204ab'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            'requires Python -I -S -B')
    destination = args.destination.absolute()
    require(destination.parent == destination.parent.resolve(strict=True)
            and '.local' in destination.parts and not destination.exists()
            and not destination.is_symlink(), 'fresh canonical ignored destination required')
    raw = (HERE / 'DISTRIBUTION.json').read_bytes()
    require(sha(raw) == MANIFEST_SHA, 'distribution manifest changed')
    manifest = json.loads(raw)
    archive_raw = (HERE / manifest['archive']['path']).read_bytes()
    require(len(archive_raw) == manifest['archive']['bytes']
            and sha(archive_raw) == manifest['archive']['sha256'], 'input archive changed')
    sources = {}
    for relative, expected in manifest['files'].items():
        data = (HERE / relative).read_bytes()
        require(len(data) == expected['bytes'] and sha(data) == expected['sha256'],
                'control source changed: ' + relative)
        sources[relative] = data
    # Validate every inert archive member before creating any destination.
    payload = {}
    with tarfile.open(fileobj=io.BytesIO(archive_raw), mode='r:') as archive:
        for member in archive.getmembers():
            relative = member.name
            path = PurePosixPath(relative)
            require(not path.is_absolute() and '..' not in path.parts
                    and str(path) == relative and path.parts[0] == 'inputs'
                    and relative not in payload, 'unsafe or duplicate archive member')
            expected = manifest['members'].get(relative)
            require(expected is not None and member.mode == expected['mode'], 'archive inventory changed')
            if expected['kind'] == 'directory':
                require(member.isdir(), 'archive directory type changed')
                data = None
            else:
                require(member.isfile() and not member.issym() and not member.islnk(),
                        'archive member must be a regular file')
                data = archive.extractfile(member).read()
                require(len(data) == expected['bytes'] and sha(data) == expected['sha256'],
                        'archive source bytes changed')
            payload[relative] = data
    require(set(payload) == set(manifest['members']), 'archive member set changed')
    destination.mkdir(mode=0o700)
    # Keep partial setup after any failure; never reuse, overwrite, or clean another stage.
    for relative in sorted(payload, key=lambda value: (len(PurePosixPath(value).parts), value)):
        target = destination / relative
        if payload[relative] is None:
            target.mkdir(mode=0o700)
        else:
            with target.open('xb') as stream:
                stream.write(payload[relative])
            target.chmod(manifest['members'][relative]['mode'])
    for relative in sorted(payload, key=lambda value: len(PurePosixPath(value).parts), reverse=True):
        if payload[relative] is None:
            (destination / relative).chmod(manifest['members'][relative]['mode'])
    (destination / 'proposed').mkdir(mode=0o755)
    for relative, data in sources.items():
        with (destination / relative).open('xb') as stream:
            stream.write(data)
        (destination / relative).chmod(manifest['files'][relative]['mode'])
    with (destination / 'DISTRIBUTION.json').open('xb') as stream:
        stream.write(raw)
    print('Materialized exact inert control inputs; no controls or proof execution.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
