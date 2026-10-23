---
name: bibtex-manager
description: Deduplicate and incrementally merge BibTeX references into JabRef databases, or append reading notes while preserving existing entries and metadata. Use for bibliography imports, DOI-based matching, and entry annotations.
license: MIT
---

# BibTeX / JabRef bibliography manager

Use `scripts/bibtex_manager.py` for conservative imports and comment additions. It does not fetch metadata, manage PDF files, or reconcile arbitrary field edits. Commands and installation details are in [README.md](README.md).

## Execution

- Identify the actual target and incoming references. If the target is unavailable, prepare a separate import file instead of guessing a path. For newly gathered references, verify bibliographic facts with authoritative sources; retain uncertainty rather than invent missing fields. Examples are demonstration data, not verified inputs for every task.
- Validate the inputs and inspect a dry run and diff before writing. When the target and operation are already authorized and conflicts are resolved, continue through application and verification without another confirmation. A request for a preview alone does not authorize writing.
- Preserve existing citation keys, groups, attachments, annotations and unknown fields outside the authorized changes. Do not silently rename keys or replace conflicting information.
- The CLI aborts the entire write on a reported conflict. Review the evidence and existing user decisions; ask only for unresolved choices that affect the result. Use an appropriate editor or JabRef when needed, then rerun the preview. Do not bypass conflict checks or silently omit entries to obtain a successful import.
- Keep the default pre-write backup unless a verified recovery copy covers the current target. Avoid concurrent editing: the changed-target check and atomic replacement are not a file lock. After applying, check the resulting changes and report what was applied, any remaining issues and the recovery location. No-change runs do not write or create backups.

## Notes

Entry-level `comment` is for reading notes and lasting bibliographic context. Keep import logs, validation details and temporary status outside the bibliography. Preserve existing user notes and append only distinct material; the script's text-containment check is not semantic deduplication.

Top-level `@comment{jabref-meta: ...}` stores JabRef metadata and is not an entry annotation. Use [references/reading-plan.md](references/reading-plan.md) only when a reading plan is requested; ordinary imports do not need one.

## Limits

- Matching uses normalized DOI or title/year, not semantic similarity. Preprints, editions and similar titles need evidence-based review. Existing matched entries retain fields other than necessary `comment` updates; unreported author, URL or attachment differences are not automatically reconciled.
- Incoming top-level metadata is not imported. Expand macros or use a compatible editor for `@string` / `@preamble` inputs. The validator is not a full BibTeX/BibLaTeX compiler or JabRef parser; check unusual syntax and cross-references with the relevant application when needed.
- Keep the complete installed folder, including `VERSION`. UTF-8 notes may need separate handling in LaTeX exports; this tool does not configure bibliography rendering.
