---
name: bibtex-manager
description: Deduplicate, annotate, and incrementally merge scientific references into existing JabRef .bib databases. Use when users request BibTeX entry creation, import into JabRef, DOI-based deduplication, updating a bibliography, or writing reading plans to the comment field.
license: MIT
---

# BibTeX / JabRef bibliography manager

## Scope

Safely merge **user-approved or already verified** BibTeX references into a JabRef-managed `.bib` file, preserving original entries and JabRef metadata. Use the bundled stdlib-only script at `scripts/bibtex_manager.py`. This skill does **not** itself fetch or validate DOI metadata, and does **not** access the user's local filesystem without actual file access.

## Workflow

1. Identify exact target `.bib` file and incoming references. If target is unavailable, create a **separate importable** `.bib` file and ask for the target before modifying an existing library. Never invent paths, overwrite unknown files, or claim a library was updated if it wasn't.
2. When references are gathered from titles/DOIs, verify bibliographic fields using publishers, Crossref, DOI landing pages, or other authoritative sources. Distinguish verified from unverified metadata. Do not invent missing fields. Give original reference URLs when relevant.
3. Keep original citation keys, `@comment{jabref-meta: ...}` blocks, groups, `file`, `keywords`, `comment`, `abstract`, `timestamp` and any unknown fields unchanged by default. On duplicates: match DOI, or title+year with no conflicting DOI; never silently replace conflicting data.
4. Add human reading notes into entry-level `comment = {...}`. If comment exists, append distinct material rather than replace it. `@comment{...}` at top level stores BibTeX/JabRef metadata and is **not** interchangeable with the `comment` field.
5. Validate both `.bib` files, run a dry run and inspect the report. Resolve any conflicts before applying. If the user already authorized the exact target and merge, no additional confirmation is required. Do not silently rename citation keys; doing so may invalidate JabRef groups and LaTeX citations.
6. Apply only with an explicit user-approved target. The script makes a timestamped backup unless disabled and performs an atomic replacement. Validate again afterwards; report counts of additions, matches, comment updates, unchanged entries and conflicts.

## CLI

From the skill folder:

```bash
python3 scripts/bibtex_manager.py validate examples/strang_splitting_references.bib
python3 scripts/bibtex_manager.py merge \
  --target /path/to/existing_library.bib \
  --incoming examples/strang_splitting_references.bib \
  --diff
# Only after previewing and confirming target:
python3 scripts/bibtex_manager.py merge \
  --target /path/to/existing_library.bib \
  --incoming examples/strang_splitting_references.bib \
  --apply
```

Optional: `--comment-key Strang1968 --comment-file references/reading-plan.md` appends extra UTF-8 text to the chosen incoming entry, including if the target has an existing version under a different key. If the incoming entry already has identical text, no duplicate note is appended. `--create` permits writing a new database when the target does not exist. Default is **dry-run**; `--apply` is required to write.

## Constraints and limitations

- The script deliberately preserves entire existing entries except necessary `comment` updates. It does **not** automatically merge conflicting `file`, group, URL or DOI values; use JabRef's native merge UI to resolve conflicts. Non-identity bibliographic fields are retained without automatic reconciliation; inspect them separately.
- Keep the entire installed folder, including `VERSION`. Use `--version` to inspect the release.
- Incoming top-level metadata is not imported; expand macros or use JabRef when importing `@string` / `@preamble` data. Close other editors while applying changes; atomic replacement does not provide a file lock.
- Duplicate detection is deterministic (normalized DOI; normalized title and year), not fuzzy semantic matching. Similar titles and preprints/published versions require human review in JabRef.
- This is a conservative BibTeX structural validator, **not** a full BibTeX/BibLaTeX compiler or JabRef parser. Macro expansion (`@string`), crossrefs, unusual entries, and quoted/concatenated fields should be checked in JabRef. Do not claim full JabRef compatibility has been independently tested.
- Plain UTF-8 `comment` is readable in JabRef. LaTeX engines or some exports may need separate Unicode handling; the script does not change bibliography rendering settings.
- The included example references and reading plan are demonstration data, not universal evidence of metadata verification. Recheck if used in a publication.

## Reading notes

Use the template in `references/reading-plan.md`. Include: reading objective, ranked reading order, what to verify in each proof, unresolved research questions, and sources. Avoid claiming novel results without a literature review.

## Deliverable checklist

- Verify target/source location and integrity.
- Show dry-run results, including conflicts.
- Confirm a backup exists after editing an existing target.
- Validate output and count entries.
- Explain what was updated versus untouched.
