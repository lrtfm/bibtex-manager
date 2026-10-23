---
name: bibtex-manager
description: Deduplicate and incrementally merge BibTeX references into JabRef databases, or append reading notes while preserving existing entries and metadata. Use for bibliography imports, DOI-based matching, and entry annotations.
license: MIT
---

# BibTeX / JabRef bibliography manager

Use `scripts/bibtex_manager.py` for imports and comment additions. See [README.md](README.md) for commands and implementation limits; it does not reconcile arbitrary field edits or manage PDFs.

## Execution

- Identify the target and incoming references. If the target is unavailable, prepare a separate import file rather than guess a path. Verify newly gathered bibliographic facts with authoritative sources, reuse valid evidence, and leave unsupported fields unknown.
- Inspect the merge preview and diff, which validate the inputs. If the target and operation are authorized, continue through application and verification without another confirmation. Preview-only requests remain read-only.
- Preserve keys, groups, attachments, user notes and other fields outside the authorized changes. The CLI aborts the whole write on reported conflicts: resolve them using evidence and existing decisions, asking only for missing information or choices that cannot otherwise be resolved. Use a suitable editor if needed and preview the revised inputs; do not silently discard entries or bypass checks.
- Keep the default backup unless a verified recovery copy covers the current target. Avoid concurrent editing; atomic replacement is not a file lock. Check the applied changes and briefly report results, unresolved issues and the recovery location.

## Notes and boundaries

- Entry-level `comment` holds reading notes and lasting bibliographic context; keep operation logs and temporary status elsewhere. Preserve existing notes and append distinct material. Top-level `@comment{jabref-meta: ...}` is metadata, not an annotation. The [reading-plan template](references/reading-plan.md) is optional for reading-plan tasks.
- Matching and comment deduplication are textual, not semantic. Review uncertain identities and version relationships without silently combining them. A conflict-free merge does not establish that every bibliographic field agrees.
- The validator is not a full BibTeX/BibLaTeX compiler or JabRef parser. Incoming top-level metadata is not imported; expand macros or use a compatible tool when needed. Check application-specific compatibility only where the input or changes warrant it.
