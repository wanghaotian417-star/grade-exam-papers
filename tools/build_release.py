#!/usr/bin/env python3
"""Build a reproducible, installable skill ZIP and SHA-256 checksum."""
import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def build(root, version):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Version must use major.minor.patch.')
    skill = root / 'skills' / 'grade-exam-papers'
    if not (skill / 'SKILL.md').is_file():
        raise ValueError('Skill entry point not found.')
    dist = root / 'dist'
    dist.mkdir(exist_ok=True)
    target = dist / f'grade-exam-papers-v{version}.zip'
    files = sorted(p for p in skill.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'})
    with ZipFile(target, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = 'grade-exam-papers/' + path.relative_to(skill).as_posix()
            entry = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes(), compresslevel=9)
    with ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive validation failed.')
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(f'{digest}  {target.name}\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='1.0.0')
    args = parser.parse_args()
    print(build(Path(__file__).resolve().parents[1], args.version))
