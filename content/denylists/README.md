# Local denylists (not committed)

This directory holds two YAML files, populated locally by a maintainer and
**never committed to git** (see `.gitignore`), that the content safety
scanner (`diary/safety/scanner.py`) uses to catch real names, school names,
and workplace names that generic regex patterns can't recognize.

## `real_names.yaml`

```yaml
terms:
  - "Jane Smith"
  - "Robert Smith"
```

## `school_workplace.yaml`

```yaml
terms:
  - "Lincoln Elementary"
  - "Acme Corp"
```

Each entry in `terms` is matched case-insensitively as a whole phrase against
entry text, frontmatter fields, and media alt text/captions. A match is
reported as a `MEDIUM`-severity finding (see `ContentSafetyScanner._is_blocking`
for the exact blocking rule).

If these files are absent, the scanner runs with empty denylists rather than
failing — real-name/school/workplace detection is then limited to whatever a
human reviewer catches during the `reviewed: true` sign-off step.
