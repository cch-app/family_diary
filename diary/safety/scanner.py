"""Content safety scanner: the publication gate for secrets and PII.

Gate rule:
- Entries with status draft/pending_review are scanned but never blocking
  (they aren't being published).
- For status approved/published: HIGH findings always block unless the
  exact finding code is listed in frontmatter.safety_scan.overrides.
  MEDIUM/LOW findings block unless the entry is reviewed (or the exact
  code is overridden).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel

from diary.content.loader import parse_entry_file
from diary.models.entry import EntryFrontmatter
from diary.models.family_member import FamilyMember
from diary.models.media import MediaAttachment
from diary.models.review import PublicationStatus, SafetyFindingSeverity
from diary.safety import patterns as P

_REDACT_WINDOW = 20


class SafetyFinding(BaseModel):
    code: str
    severity: SafetyFindingSeverity
    location: str
    excerpt: str
    message: str


@dataclass
class ScanReport:
    file_path: Path
    findings: list[SafetyFinding] = field(default_factory=list)
    blocking: bool = False


def _redact(text: str, start: int, end: int) -> str:
    lo = max(0, start - _REDACT_WINDOW)
    hi = min(len(text), end + _REDACT_WINDOW)
    prefix = ("..." if lo > 0 else "") + text[lo:start]
    suffix = text[end:hi] + ("..." if hi < len(text) else "")
    return f"{prefix}[REDACTED]{suffix}".replace("\n", " ")


_REGEX_FINDINGS: list[tuple[str, re.Pattern[str], SafetyFindingSeverity, str]] = [
    ("aws_access_key", P.AWS_ACCESS_KEY_ID, SafetyFindingSeverity.HIGH, "AWS access key ID"),
    (
        "generic_secret_assignment",
        P.GENERIC_SECRET_ASSIGNMENT,
        SafetyFindingSeverity.HIGH,
        "credential-like assignment (api key/secret/token/password)",
    ),
    ("private_key_block", P.PRIVATE_KEY_BLOCK, SafetyFindingSeverity.HIGH, "private key block"),
    ("slack_token", P.SLACK_TOKEN, SafetyFindingSeverity.HIGH, "Slack token"),
    ("github_token", P.GITHUB_TOKEN, SafetyFindingSeverity.HIGH, "GitHub token"),
    ("google_api_key", P.GOOGLE_API_KEY, SafetyFindingSeverity.HIGH, "Google API key"),
    ("jwt_lookalike", P.JWT_LOOKALIKE, SafetyFindingSeverity.HIGH, "JWT-like token"),
    (
        "url_embedded_credentials",
        P.URL_WITH_EMBEDDED_CREDENTIALS,
        SafetyFindingSeverity.HIGH,
        "URL with embedded credentials",
    ),
    ("email", P.EMAIL, SafetyFindingSeverity.MEDIUM, "email address"),
    ("phone", P.PHONE, SafetyFindingSeverity.MEDIUM, "phone number"),
    ("ssn_us", P.SSN_US, SafetyFindingSeverity.HIGH, "US Social Security Number"),
    ("address_hint", P.ADDRESS_HINT, SafetyFindingSeverity.MEDIUM, "street address"),
    (
        "birthdate_near_born",
        P.BIRTHDATE_NEAR_BORN,
        SafetyFindingSeverity.MEDIUM,
        "exact birth year near 'born'",
    ),
]


class ContentSafetyScanner:
    def __init__(
        self,
        real_name_denylist: list[str] | None = None,
        school_workplace_denylist: list[str] | None = None,
        known_family_labels: set[str] | None = None,
        check_entropy: bool = False,
    ) -> None:
        self.real_name_denylist = real_name_denylist or []
        self.school_workplace_denylist = school_workplace_denylist or []
        self.known_family_labels = known_family_labels or set()
        self.check_entropy = check_entropy

    def scan_text(self, text: str, location: str) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        for code, pattern, severity, message in _REGEX_FINDINGS:
            for match in pattern.finditer(text):
                findings.append(
                    SafetyFinding(
                        code=code,
                        severity=severity,
                        location=location,
                        excerpt=_redact(text, match.start(), match.end()),
                        message=message,
                    )
                )
        findings.extend(
            self._scan_denylist(text, location, self.real_name_denylist, "real_name_denylist")
        )
        findings.extend(
            self._scan_denylist(
                text, location, self.school_workplace_denylist, "school_workplace_denylist"
            )
        )
        if self.check_entropy:
            findings.extend(self._scan_entropy(text, location))
        return findings

    @staticmethod
    def _scan_denylist(
        text: str, location: str, terms: list[str], code: str
    ) -> list[SafetyFinding]:
        findings = []
        for term in terms:
            if not term.strip():
                continue
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(text):
                findings.append(
                    SafetyFinding(
                        code=code,
                        severity=SafetyFindingSeverity.MEDIUM,
                        location=location,
                        excerpt=_redact(text, match.start(), match.end()),
                        message=f"denylisted term matched: {term!r}",
                    )
                )
        return findings

    @staticmethod
    def _scan_entropy(text: str, location: str) -> list[SafetyFinding]:
        findings = []
        for match in P.HIGH_ENTROPY_TOKEN_CANDIDATE.finditer(text):
            token = match.group(0)
            if P.shannon_entropy(token) >= 4.0:
                findings.append(
                    SafetyFinding(
                        code="high_entropy_token",
                        severity=SafetyFindingSeverity.LOW,
                        location=location,
                        excerpt=_redact(text, match.start(), match.end()),
                        message="unlabeled high-entropy token (possible secret)",
                    )
                )
        return findings

    def scan_frontmatter(self, fm: EntryFrontmatter) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        findings.extend(self.scan_text(fm.title, "frontmatter.title"))
        if fm.excerpt:
            findings.extend(self.scan_text(fm.excerpt, "frontmatter.excerpt"))
        if (
            fm.author_label
            and self.known_family_labels
            and fm.author_label not in self.known_family_labels
        ):
            findings.append(
                SafetyFinding(
                    code="unknown_family_member_label",
                    severity=SafetyFindingSeverity.MEDIUM,
                    location="frontmatter.author_label",
                    excerpt=fm.author_label,
                    message="author_label is not a known anonymized family member label",
                )
            )
        if self.known_family_labels:
            for i, member in enumerate(fm.family_members):
                if member not in self.known_family_labels:
                    findings.append(
                        SafetyFinding(
                            code="unknown_family_member_label",
                            severity=SafetyFindingSeverity.MEDIUM,
                            location=f"frontmatter.family_members[{i}]",
                            excerpt=member,
                            message="family member label is not a known anonymized label"
                            " (possible real name)",
                        )
                    )
        for i, tag in enumerate(fm.tags):
            findings.extend(self.scan_text(tag, f"frontmatter.tags[{i}]"))
        if fm.reviewed_by:
            findings.extend(self.scan_text(fm.reviewed_by, "frontmatter.reviewed_by"))
        return findings

    def scan_media(self, media: list[MediaAttachment]) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        for i, m in enumerate(media):
            findings.extend(self.scan_text(m.alt, f"media[{i}].alt"))
            findings.extend(self.scan_text(m.path, f"media[{i}].path"))
            if m.caption:
                findings.extend(self.scan_text(m.caption, f"media[{i}].caption"))
        return findings

    def scan_entry(self, entry_path: Path) -> ScanReport:
        entry = parse_entry_file(entry_path)
        fm = entry.frontmatter
        findings: list[SafetyFinding] = []
        findings.extend(self.scan_frontmatter(fm))
        findings.extend(self.scan_text(entry.slug, "slug"))
        findings.extend(self.scan_text(entry.body_markdown, "body"))
        findings.extend(self.scan_media(fm.media))

        blocking = self._is_blocking(findings, fm)
        return ScanReport(file_path=entry_path, findings=findings, blocking=blocking)

    def scan_family_members(self, members: dict[str, FamilyMember]) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        for label in members:
            findings.extend(self.scan_text(label, f"family_members[{label}].label"))
        return findings

    @staticmethod
    def _is_blocking(findings: list[SafetyFinding], fm: EntryFrontmatter) -> bool:
        if fm.status not in (PublicationStatus.APPROVED, PublicationStatus.PUBLISHED):
            return False

        overrides = set(fm.safety_scan.overrides)

        high_findings = [
            f
            for f in findings
            if f.severity == SafetyFindingSeverity.HIGH and f.code not in overrides
        ]
        if high_findings:
            return True

        if not fm.reviewed:
            medium_low_findings = [
                f
                for f in findings
                if f.severity in (SafetyFindingSeverity.MEDIUM, SafetyFindingSeverity.LOW)
                and f.code not in overrides
            ]
            if medium_low_findings:
                return True

        return False


def load_denylist(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return list(data.get("terms", []))


def build_scanner_from_content_dir(content_dir: Path) -> ContentSafetyScanner:
    from diary.content.loader import load_family_members

    denylist_dir = content_dir / "denylists"
    real_names = load_denylist(denylist_dir / "real_names.yaml")
    school_workplace = load_denylist(denylist_dir / "school_workplace.yaml")
    known_labels = set(load_family_members(content_dir / "family_members.yaml"))
    return ContentSafetyScanner(
        real_name_denylist=real_names,
        school_workplace_denylist=school_workplace,
        known_family_labels=known_labels,
    )


def scan_all_entries(content_dir: Path) -> list[ScanReport]:
    from diary.content.loader import load_family_members

    entries_dir = content_dir / "entries"
    scanner = build_scanner_from_content_dir(content_dir)
    reports: list[ScanReport] = []

    family_members_path = content_dir / "family_members.yaml"
    if family_members_path.exists():
        members = load_family_members(family_members_path)
        findings = scanner.scan_family_members(members)
        reports.append(
            ScanReport(file_path=family_members_path, findings=findings, blocking=bool(findings))
        )

    if entries_dir.exists():
        reports.extend(scanner.scan_entry(path) for path in sorted(entries_dir.glob("**/*.md")))

    return reports
