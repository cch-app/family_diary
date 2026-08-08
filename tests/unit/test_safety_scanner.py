from datetime import date
from pathlib import Path

from diary.models.entry import EntryFrontmatter
from diary.models.family_member import FamilyMember
from diary.models.media import MediaAttachment
from diary.models.review import SafetyFindingSeverity
from diary.safety.scanner import ContentSafetyScanner, scan_all_entries

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_entries"


def codes(findings) -> set[str]:
    return {f.code for f in findings}


class TestScanTextRegexPatterns:
    def setup_method(self):
        self.scanner = ContentSafetyScanner()

    def test_detects_aws_access_key(self):
        findings = self.scanner.scan_text("key: AKIAABCDEFGHIJKLMNOP", "body")
        assert "aws_access_key" in codes(findings)

    def test_detects_generic_secret_assignment(self):
        findings = self.scanner.scan_text('api_key = "sk_live_abcdef1234567890"', "body")
        assert "generic_secret_assignment" in codes(findings)

    def test_detects_private_key_block(self):
        findings = self.scanner.scan_text("-----BEGIN RSA PRIVATE KEY-----", "body")
        assert "private_key_block" in codes(findings)

    def test_detects_slack_token(self):
        findings = self.scanner.scan_text("xoxb-1234567890-abcdefghij", "body")
        assert "slack_token" in codes(findings)

    def test_detects_github_token(self):
        findings = self.scanner.scan_text(
            "ghp_" + "a" * 36, "body"
        )
        assert "github_token" in codes(findings)

    def test_detects_google_api_key(self):
        findings = self.scanner.scan_text("AIza" + "a" * 35, "body")
        assert "google_api_key" in codes(findings)

    def test_detects_credential_embedded_url(self):
        findings = self.scanner.scan_text("https://user:pass@example.com/path", "body")
        assert "url_embedded_credentials" in codes(findings)

    def test_detects_email(self):
        findings = self.scanner.scan_text("Contact us at family@example.com", "body")
        assert "email" in codes(findings)

    def test_detects_phone_number(self):
        findings = self.scanner.scan_text("Call me at 555-123-4567", "body")
        assert "phone" in codes(findings)

    def test_detects_ssn(self):
        findings = self.scanner.scan_text("SSN: 123-45-6789", "body")
        assert "ssn_us" in codes(findings)

    def test_detects_address_hint(self):
        findings = self.scanner.scan_text("We live at 123 Maple Street now.", "body")
        assert "address_hint" in codes(findings)

    def test_detects_birthdate_near_born(self):
        findings = self.scanner.scan_text("She was born in 2024 on a rainy day.", "body")
        assert "birthdate_near_born" in codes(findings)

    def test_high_severity_assigned_to_secrets(self):
        findings = self.scanner.scan_text("AKIAABCDEFGHIJKLMNOP", "body")
        assert findings[0].severity == SafetyFindingSeverity.HIGH

    def test_medium_severity_assigned_to_email(self):
        findings = self.scanner.scan_text("family@example.com", "body")
        assert findings[0].severity == SafetyFindingSeverity.MEDIUM

    def test_clean_text_has_no_findings(self):
        findings = self.scanner.scan_text(
            "We spent the afternoon in the garden watching clouds go by.", "body"
        )
        assert findings == []


class TestDenylists:
    def test_real_name_denylist_hit(self):
        scanner = ContentSafetyScanner(real_name_denylist=["Jane Smith"])
        findings = scanner.scan_text("Today Jane Smith went to the park.", "body")
        assert "real_name_denylist" in codes(findings)
        assert findings[0].severity == SafetyFindingSeverity.MEDIUM

    def test_school_workplace_denylist_hit(self):
        scanner = ContentSafetyScanner(school_workplace_denylist=["Acme Corp"])
        findings = scanner.scan_text("She started at Acme Corp this week.", "body")
        assert "school_workplace_denylist" in codes(findings)

    def test_denylist_case_insensitive(self):
        scanner = ContentSafetyScanner(real_name_denylist=["Jane Smith"])
        findings = scanner.scan_text("jane smith was here", "body")
        assert "real_name_denylist" in codes(findings)

    def test_empty_denylist_no_findings(self):
        scanner = ContentSafetyScanner(real_name_denylist=[])
        findings = scanner.scan_text("Anyone can be named anything here.", "body")
        assert findings == []


class TestFrontmatterScanning:
    def test_unknown_family_member_label_flagged(self):
        scanner = ContentSafetyScanner(known_family_labels={"Mom", "Kid A"})
        fm = EntryFrontmatter(
            title="Test", date=date(2026, 1, 1), family_members=["Mom", "Real Name"]
        )
        findings = scanner.scan_frontmatter(fm)
        assert "unknown_family_member_label" in codes(findings)

    def test_known_family_member_label_not_flagged(self):
        scanner = ContentSafetyScanner(known_family_labels={"Mom", "Kid A"})
        fm = EntryFrontmatter(title="Test", date=date(2026, 1, 1), family_members=["Mom"])
        findings = scanner.scan_frontmatter(fm)
        assert "unknown_family_member_label" not in codes(findings)


class TestFrontmatterFieldsScanned:
    def test_email_in_tag_flagged(self):
        scanner = ContentSafetyScanner()
        fm = EntryFrontmatter(
            title="Test", date=date(2026, 1, 1), tags=["family@example.com"]
        )
        findings = scanner.scan_frontmatter(fm)
        assert "email" in codes(findings)

    def test_secret_in_reviewed_by_flagged(self):
        scanner = ContentSafetyScanner()
        fm = EntryFrontmatter(
            title="Test", date=date(2026, 1, 1), reviewed_by="AKIAABCDEFGHIJKLMNOP"
        )
        findings = scanner.scan_frontmatter(fm)
        assert "aws_access_key" in codes(findings)

    def test_clean_tags_and_reviewed_by_not_flagged(self):
        scanner = ContentSafetyScanner()
        fm = EntryFrontmatter(
            title="Test", date=date(2026, 1, 1), tags=["milestone"], reviewed_by="Mom"
        )
        findings = scanner.scan_frontmatter(fm)
        assert findings == []


class TestScanFamilyMembers:
    def test_denylisted_label_flagged(self):
        scanner = ContentSafetyScanner(real_name_denylist=["Jane Smith"])
        members = {"Jane Smith": FamilyMember(label="Jane Smith", role="parent")}
        findings = scanner.scan_family_members(members)
        assert "real_name_denylist" in codes(findings)

    def test_anonymized_labels_not_flagged(self):
        scanner = ContentSafetyScanner()
        members = {
            "Mom": FamilyMember(label="Mom", role="parent"),
            "Kid A": FamilyMember(label="Kid A", role="child"),
        }
        findings = scanner.scan_family_members(members)
        assert findings == []


class TestScanMedia:
    def test_pii_in_alt_text_flagged(self):
        scanner = ContentSafetyScanner()
        media = [MediaAttachment(path="a.jpg", alt="Contact family@example.com for prints")]
        findings = scanner.scan_media(media)
        assert "email" in codes(findings)
        assert findings[0].location == "media[0].alt"

    def test_denylisted_name_in_filename_flagged(self):
        scanner = ContentSafetyScanner(real_name_denylist=["janesmith"])
        media = [MediaAttachment(path="photos/janesmith-bday.jpg", alt="Birthday photo")]
        findings = scanner.scan_media(media)
        assert "real_name_denylist" in codes(findings)


class TestScanEntryBlockingRules:
    def setup_method(self):
        self.scanner = ContentSafetyScanner()

    def test_published_with_secret_blocks(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_with_secret.md")
        assert report.blocking is True
        assert "aws_access_key" in codes(report.findings)

    def test_published_clean_entry_does_not_block(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_clean_published.md")
        assert report.blocking is False

    def test_approved_not_reviewed_with_pii_blocks(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_with_pii_not_reviewed.md")
        assert report.blocking is True
        assert "email" in codes(report.findings)

    def test_published_reviewed_with_pii_does_not_block(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_with_pii_reviewed.md")
        assert report.blocking is False
        assert "email" in codes(report.findings)

    def test_draft_with_secret_reported_but_not_blocking(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_draft_with_secret.md")
        assert report.blocking is False
        assert "aws_access_key" in codes(report.findings)

    def test_high_finding_with_matching_override_does_not_block(self):
        report = self.scanner.scan_entry(FIXTURES / "entry_with_override.md")
        assert report.blocking is False
        assert "aws_access_key" in codes(report.findings)


class TestScanAllEntriesIncludesFamilyMembers:
    def test_denylisted_real_name_in_family_members_yaml_blocks(self, tmp_path):
        (tmp_path / "denylists").mkdir()
        (tmp_path / "denylists" / "real_names.yaml").write_text(
            'terms: ["Jane Smith"]\n', encoding="utf-8"
        )
        (tmp_path / "family_members.yaml").write_text(
            'members:\n  - label: "Jane Smith"\n    role: "parent"\n', encoding="utf-8"
        )
        reports = scan_all_entries(tmp_path)
        family_report = next(r for r in reports if r.file_path.name == "family_members.yaml")
        assert family_report.blocking is True
        assert "real_name_denylist" in codes(family_report.findings)

    def test_clean_family_members_yaml_not_blocking(self, tmp_path):
        (tmp_path / "family_members.yaml").write_text(
            'members:\n  - label: "Mom"\n    role: "parent"\n', encoding="utf-8"
        )
        reports = scan_all_entries(tmp_path)
        family_report = next(r for r in reports if r.file_path.name == "family_members.yaml")
        assert family_report.blocking is False
