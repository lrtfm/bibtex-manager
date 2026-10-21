#!/usr/bin/env python3
"""Conservative, dependency-free BibTeX/JabRef library merge utility.

Designed for safe append/annotation, NOT a full BibTeX interpreter.
No network access or metadata verification is performed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import unicodedata

SPECIAL = {"comment", "string", "preamble"}
VERSION = (Path(__file__).resolve().parents[1] / 'VERSION').read_text().strip()


class BibError(ValueError):
    pass


@dataclass(frozen=True)
class Field:
    name: str
    value: str
    value_start: int  # offset into entry raw text
    value_end: int


@dataclass(frozen=True)
class Entry:
    kind: str
    key: str
    start: int
    end: int
    raw: str
    fields: dict[str, Field]

    def field(self, name: str) -> str:
        x = self.fields.get(name.lower())
        return clean_value(x.value) if x else ""


def _skip_space(text: str, i: int) -> int:
    while i < len(text) and text[i].isspace():
        i += 1
    return i


def _read_braces(text: str, pos: int, op: str = '{', cl: str = '}') -> int:
    """Return first index AFTER matching closing delimiter. Does not interpret TeX."""
    depth = 1
    i = pos + 1
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            i += 2
            continue
        if text[i] == op:
            depth += 1
        elif text[i] == cl:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise BibError(f"unclosed @{op}...{cl} block at offset {pos}")


def _field_end(text: str, i: int) -> int:
    depth = 0
    quoted = False
    while i < len(text):
        c = text[i]
        if c == '\\' and i + 1 < len(text):
            i += 2
            continue
        if c == '"' and depth == 0:
            quoted = not quoted
        elif not quoted:
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth < 0:
                    raise BibError('unbalanced brace in field value')
            elif c == ',' and depth == 0:
                return i
        i += 1
    if depth != 0 or quoted:
        raise BibError('unbalanced field value')
    return i


def _parse_fields(raw: str, key_end: int, block_end: int) -> dict[str, Field]:
    fields = {}
    i = key_end
    while i < block_end:
        i = _skip_space(raw, i)
        if i >= block_end:
            break
        if raw[i] == ',':
            i += 1
            continue
        m = re.match(r'[A-Za-z][A-Za-z0-9_:-]*', raw[i:])
        if not m:
            raise BibError(f"invalid field near {raw[i:i+45]!r}")
        name = m.group(0).lower()
        i += len(m.group(0))
        i = _skip_space(raw, i)
        if i >= block_end or raw[i] != '=':
            raise BibError(f"missing = after field {name!r}")
        i = _skip_space(raw, i + 1)
        vstart = i
        vend = _field_end(raw[:block_end], i)
        if vend == i:
            raise BibError(f"empty field {name!r}")
        if name in fields:
            raise BibError(f"duplicate field {name!r}")
        fields[name] = Field(name, raw[vstart:vend].strip(), vstart, vend)
        i = vend
        if i < block_end and raw[i] != ',':
            raise BibError(f"expected comma after field {name!r}")
    return fields


def parse_bib(text: str) -> list[Entry]:
    """Scan BibTeX entries while retaining every original character of the file."""
    entries = []
    i = 0
    while i < len(text):
        if text[i] == '%':
            newline = text.find('\n', i)
            i = len(text) if newline < 0 else newline + 1
            continue
        if text[i] != '@':
            i += 1
            continue
        # Only recognize @type{...}, not email addresses and incidental @ characters.
        m = re.match(r'@\s*([A-Za-z]+)\s*([({])', text[i:])
        if not m:
            i += 1
            continue
        kind = m.group(1).lower()
        opening = m.group(2)
        body_open = i + m.end() - 1
        closing = '}' if opening == '{' else ')'
        end = _read_braces(text, body_open, opening, closing)
        raw = text[i:end]
        if kind not in SPECIAL:
            kstart = (body_open - i) + 1
            comma = raw.find(',', kstart)
            if comma < 0 or comma >= len(raw) - 1:
                raise BibError(f"@{kind} missing citation key/fields at offset {i}")
            key = raw[kstart:comma].strip()
            if not key or re.search(r'[\s{},]', key):
                raise BibError(f"invalid citation key {key!r}")
            fields = _parse_fields(raw, comma + 1, len(raw) - 1)
            entries.append(Entry(kind, key, i, end, raw, fields))
        i = end
    keys = [e.key.lower() for e in entries]
    if len(keys) != len(set(keys)):
        raise BibError('duplicate citation keys in input library')
    return entries


def clean_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] in '{"' and value[-1] == ('}' if value[0] == '{' else '"'):
        value = value[1:-1]
    return value.strip()


def norm_doi(raw: str) -> str:
    v = clean_value(raw).strip().lower()
    v = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', v)
    v = re.sub(r'^doi:\s*', '', v)
    return v.strip()


def norm_title(raw: str) -> str:
    v = clean_value(raw).lower()
    # TeX accent handling for duplicate hints, not for high-stakes verification.
    v = re.sub(r'\\(?:\"|\'|`|\^|~|c|v|u)\s*\{?([a-z])\}?', r'\1', v)
    v = re.sub(r'\\[a-zA-Z]+', '', v)
    v = unicodedata.normalize('NFKD', v)
    v = ''.join(c for c in v if not unicodedata.combining(c))
    return re.sub(r'[^\w]+', '', v)


def _match(target: Entry, incoming: Entry) -> str | None:
    td, sd = norm_doi(target.field('doi')), norm_doi(incoming.field('doi'))
    if td and sd and td == sd:
        tt, st = norm_title(target.field('title')), norm_title(incoming.field('title'))
        if tt and st and tt != st:
            return 'conflict: same DOI but different title'
        return 'same DOI'
    tt, st = norm_title(target.field('title')), norm_title(incoming.field('title'))
    ty, sy = target.field('year'), incoming.field('year')
    if tt and tt == st and ty and ty == sy:
        if td and sd and td != sd:
            return 'conflict: same title/year but different DOI'
        return 'same title/year'
    if target.key.lower() == incoming.key.lower():
        return 'conflict: citation key already used by another work'
    return None


def _comment_text(existing: str, addition: str) -> str:
    addition = addition.strip()
    if not addition:
        return existing
    if addition in existing:
        return existing
    return existing.rstrip() + ('\n\n' if existing.strip() else '') + addition


def _validate_balanced_braces(value: str):
    # Comment text is represented inside braces, so ensure it cannot terminate early.
    wrapped = '{' + value + '}'
    if _read_braces(wrapped, 0) != len(wrapped):
        raise BibError('unbalanced braces in new comment')


def update_comment(raw: str, entry: Entry, addition: str, newline: str = '\n') -> str:
    """Replace only the comment value, or add the single field near entry end."""
    old = entry.fields.get('comment')
    if old:
        original = clean_value(old.value)
        combined = _comment_text(original, addition)
        if combined == original:
            return raw
        _validate_balanced_braces(combined)
        return raw[:old.value_start] + '{' + combined + '}' + raw[old.value_end:]
    _validate_balanced_braces(addition)
    endpos = len(raw) - 1
    prefix = raw[:endpos].rstrip()
    needs_comma = prefix[-1] != ','
    suffix = raw[len(prefix):endpos]
    indent = '  '
    # insert near the end, preserve trailing pre-closing whitespace except for insertion
    insertion = (',' if needs_comma else '') + newline + indent + 'comment = {' + addition + '}'
    return prefix + insertion + suffix + raw[endpos:]


def newline_of(text: str) -> str:
    return '\r\n' if '\r\n' in text else '\n'


def merge(target_text: str, incoming_text: str, comment_key: str | None = None,
          comment_text: str = '') -> tuple[str, dict]:
    targets = parse_bib(target_text)
    sources = parse_bib(incoming_text)
    report: dict = {'added': [], 'matched': [], 'comments_updated': [], 'conflicts': [], 'unchanged': []}
    source_notes = {}
    if comment_key:
        if comment_key.lower() not in {e.key.lower() for e in sources}:
            raise BibError('--comment-key does not identify an incoming entry')
        source_notes[comment_key.lower()] = comment_text
    elif comment_text:
        raise BibError('--comment-file requires --comment-key')

    changes: dict[str, str] = {}
    additions = {}
    working = list(targets)
    for src in sources:
        matches = [(t, desc) for t in working if (desc := _match(t, src))]
        matched_same = [(t, desc) for t, desc in matches if not desc.startswith('conflict:')]
        conflict_matches = [(t, desc) for t, desc in matches if desc.startswith('conflict:')]
        if conflict_matches or len(matched_same) > 1:
            details = '; '.join(f'{t.key}: {reason}' for t, reason in matches)
            report['conflicts'].append(f'{src.key}: {details}')
            continue
        if matched_same:
            target, why = matched_same[0]
            report['matched'].append(f'{src.key} -> {target.key} ({why})')
            # Preserve any existing target comment and append novel source notes.
            note = src.field('comment')
            if src.key.lower() in source_notes:
                note = _comment_text(note, source_notes[src.key.lower()])
            if note:
                original = changes.get(target.key.lower(), additions.get(target.key.lower(), target.raw))
                # reparse current entry to find current field offsets
                updated_entry = parse_bib(original)[0]
                revised = update_comment(original, updated_entry, note, newline_of(target_text))
                if revised != original:
                    if target.key.lower() in additions:
                        additions[target.key.lower()] = revised
                    else:
                        changes[target.key.lower()] = revised
                    report['comments_updated'].append(target.key)
                else:
                    report['unchanged'].append(target.key)
            else:
                report['unchanged'].append(target.key)
        else:
            snippet = src.raw
            if src.key.lower() in source_notes and source_notes[src.key.lower()]:
                snippet_entry = parse_bib(snippet)[0]
                snippet = update_comment(snippet, snippet_entry, source_notes[src.key.lower()], newline_of(incoming_text))
            additions[src.key.lower()] = snippet
            report['added'].append(src.key)
            working.append(src)
    if report['conflicts']:
        return target_text, report
    revised = target_text
    for entry in reversed(targets):
        if entry.key.lower() in changes:
            revised = revised[:entry.start] + changes[entry.key.lower()] + revised[entry.end:]
    if additions:
        nl = newline_of(target_text) if target_text else newline_of(incoming_text)
        sep = '' if not revised else ('' if revised.endswith(nl * 2) else nl if revised.endswith(nl) else nl * 2)
        revised += sep + (nl * 2).join(x.replace('\r\n', '\n').replace('\n', nl) for x in additions.values()) + nl
    parse_bib(revised)
    return revised, report


def _write_atomic(path: Path, output: str, input_text: str, backup: bool):
    if path.exists() and path.read_bytes().decode('utf-8') != input_text:
        raise BibError('target changed since it was read; rerun the preview')
    if output == input_text:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if path.exists() and backup:
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup_path = path.with_name(path.name + '.bak.' + stamp)
        shutil.copy2(path, backup_path)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, tmpname = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=str(path.parent))
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as f:
            f.write(output.encode('utf-8'))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmpname, path)
    finally:
        if os.path.exists(tmpname):
            os.unlink(tmpname)
    return str(backup_path) if backup_path else None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description='Conservative merge for JabRef .bib files (dry run by default)')
    p.add_argument('--version', action='version', version=VERSION)
    sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('validate', help='Parse entries and check duplicate citation keys')
    v.add_argument('file', type=Path)
    m = sub.add_parser('merge', help='Append novel entries, preserve existing JabRef metadata')
    m.add_argument('--target', required=True, type=Path)
    m.add_argument('--incoming', required=True, type=Path)
    m.add_argument('--comment-key', help='Source entry key to annotate, even when existing target uses a different key')
    m.add_argument('--comment-file', type=Path, help='UTF-8 plain text / markdown to add to comment field')
    m.add_argument('--apply', action='store_true', help='Really write (default: dry run)')
    m.add_argument('--create', action='store_true', help='Allow creation of a missing target')
    m.add_argument('--no-backup', action='store_true', help='Disable backup (not recommended)')
    m.add_argument('--diff', action='store_true', help='Show unified diff on dry run')
    args = p.parse_args(argv)
    try:
        if args.command == 'validate':
            entries = parse_bib(args.file.read_text(encoding='utf-8-sig'))
            print(json.dumps({'valid': True, 'entries': len(entries), 'keys': [e.key for e in entries]}, ensure_ascii=False, indent=2))
            return 0
        target = args.target.expanduser().resolve()
        source = args.incoming.expanduser().resolve()
        if target == source:
            raise BibError('incoming and target must be different files')
        if not target.exists() and not args.create:
            raise BibError('target file does not exist; pass --create to create it')
        if not source.exists():
            raise BibError(f'input does not exist: {source}')
        # Decode bytes directly to preserve CRLF and an existing UTF-8 BOM.
        original = target.read_bytes().decode('utf-8') if target.exists() else ''
        incoming = source.read_text(encoding='utf-8-sig')
        comment_text = args.comment_file.read_text(encoding='utf-8-sig') if args.comment_file else ''
        if bool(args.comment_file) != bool(args.comment_key):
            raise BibError('--comment-key and --comment-file must be used together')
        updated, report = merge(original, incoming, args.comment_key, comment_text)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report['conflicts']:
            print('ABORT: conflict(s) found, no modifications written', file=sys.stderr)
            return 2
        if args.diff and not args.apply:
            print(''.join(difflib.unified_diff(original.splitlines(True), updated.splitlines(True), fromfile=str(target), tofile=str(target) + ' (proposed)')))
        if args.apply:
            backup_file = _write_atomic(target, updated, original, backup=not args.no_backup)
            print(f"Applied: {target}; backup: {backup_file or '(none)'}")
        else:
            print('DRY RUN: No files changed. Use --apply to write changes.')
        return 0
    except (BibError, UnicodeError, OSError) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
