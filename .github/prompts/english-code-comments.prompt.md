---
name: English Code And Comments
description: "Update code text, comments, docstrings, and developer-facing strings to English while preserving behavior and APIs. Use when standardizing mixed-language codebases."
argument-hint: "Target files/scope and any terms to keep unchanged"
agent: agent
---

Standardize the selected codebase scope so all code-adjacent language is English.

Task:
Convert non-English code text to clear English while preserving runtime behavior, public APIs, and file structure.

Input assumptions:

- User may provide selected files, folders, or symbols.
- If no scope is provided, ask for exact scope before editing.
- User may provide glossary terms that must remain unchanged.

Convert to English:

- Inline comments and block comments
- Docstrings and documentation comments
- Readme/developer docs inside the selected scope
- User-facing and log strings by default

Strict preserve policy (always apply):

- Function/class/module names used as public APIs
- Database schema, config keys, protocol field names
- Error codes and machine-readable identifiers

Output format:

1. Scope and assumptions
2. Files updated
3. Terminology decisions (old -> new)
4. Risk notes (if any)
5. Validation performed

Quality rules:

- Keep meaning accurate; do not simplify away domain intent.
- Keep technical tone concise and consistent.
- Avoid introducing behavior changes.
- If translation uncertainty is high, note the ambiguity and propose 1-2 alternatives.
