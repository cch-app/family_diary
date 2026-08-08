# 0004: Publication safety gate independent of the scan CLI

## Status

Accepted

## Context

`BUSINESS_REQUIREMENTS.md` requires that the release process fail or block
publication when likely personal information or credentials are detected, and that
draft content must never render to public visitors. Relying solely on a CI step or
a maintainer remembering to run a scanner CLI before deploying would be a single
point of failure — a forgotten step could publish unsafe content.

## Decision

Make the publication check a property evaluated at render/route time, not just a
pre-deploy CLI step:

```python
@property
def is_public(self) -> bool:
    return (self.frontmatter.status == PublicationStatus.PUBLISHED
            and self.frontmatter.reviewed is True
            and self.frontmatter.safety_scan.passed is True)
```

Every public route checks `is_public` (or filters through `repo.published_entries`,
which applies the same rule) before showing an entry, its media, or including it in
an export. Separately, `scripts/scan_content.py` provides a CLI that scans text,
frontmatter, links, and media alt text/captions for credentials and PII patterns
(plus optional local, gitignored denylists for real names and
school/workplace names — see `content/denylists/README.md`), and an integration
test (`tests/integration/test_safety_gate_e2e.py`) runs that scan against the real
`content/` directory as part of `pytest`, so a green test run is itself a pre-deploy
gate.

## Consequences

- A mis-set frontmatter field (e.g. forgetting `reviewed: true`) can never leak
  content publicly, regardless of whether anyone ran the scanner — `is_public` is
  the single source of truth, checked defense-in-depth at every route.
- HIGH-severity findings (credentials/secrets) always block publication unless
  explicitly overridden per finding code; MEDIUM/LOW findings (PII heuristics,
  denylist hits) are allowed only once an entry is marked `reviewed: true`, keeping
  a human in the loop for judgment calls.
- The real-name/school/workplace denylists are local-only and gitignored, so this
  layer of detection only exists where a maintainer has populated them; the
  `reviewed: true` human sign-off remains the backstop.
