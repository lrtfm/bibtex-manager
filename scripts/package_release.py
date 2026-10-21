#!/usr/bin/env python3
"""Validate and build a deterministic, allowlisted release archive (stdlib only)."""
from pathlib import Path
import hashlib
import os
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    '.gitignore', '.github/workflows/ci.yml', 'SKILL.md', 'README.md',
    'LICENSE', 'VERSION', 'CHANGELOG.md', 'PUBLISHING.md',
    'scripts/bibtex_manager.py', 'scripts/package_release.py',
    'tests/test_bibtex_manager.py', 'tests/test_regressions.py',
    'examples/strang_splitting_references.bib', 'references/reading-plan.md',
]


def main():
    version = (ROOT/'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise SystemExit('VERSION must contain a three-part numeric version')
    tag = os.environ.get('GITHUB_REF', '')
    if tag.startswith('refs/tags/') and tag != f'refs/tags/v{version}':
        raise SystemExit('Tag does not match VERSION')
    skill = (ROOT/'SKILL.md').read_text()
    if not skill.startswith('---\nname: bibtex-manager\ndescription: ') or '\nlicense: MIT\n---\n' not in skill:
        raise SystemExit('Unexpected Skill frontmatter; validate before packaging')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/bibtex_manager.py', 'validate',
                    'examples/strang_splitting_references.bib'], cwd=ROOT, check=True)
    dest = ROOT/'dist'
    dest.mkdir(exist_ok=True)
    archive = dest/f'bibtex-manager-{version}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(FILES):
            info = zipfile.ZipInfo(f'bibtex-manager/{name}', date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (ROOT/name).read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    print(f'Built {archive.name}\nSHA256 {digest}')


if __name__ == '__main__':
    main()
