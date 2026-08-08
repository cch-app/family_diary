from datetime import date
from pathlib import Path

import pytest

from diary.content.repository import ContentRepository

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_content"


@pytest.fixture
def repo() -> ContentRepository:
    return ContentRepository(FIXTURES)


class TestPublishedEntries:
    def test_excludes_draft(self, repo):
        titles = [e.frontmatter.title for e in repo.published_entries]
        assert "Draft Thoughts" not in titles

    def test_reverse_chronological_order(self, repo):
        dates = [e.frontmatter.date for e in repo.published_entries]
        assert dates == sorted(dates, reverse=True)

    def test_only_public_entries_included(self, repo):
        assert all(e.is_public for e in repo.published_entries)
        assert len(repo.published_entries) == 2


class TestGetBySlug:
    def test_finds_published_entry(self, repo):
        entry = repo.get_by_slug("first-steps")
        assert entry is not None
        assert entry.frontmatter.title == "First Steps"

    def test_draft_slug_returns_none(self, repo):
        assert repo.get_by_slug("draft-thoughts") is None

    def test_unknown_slug_returns_none(self, repo):
        assert repo.get_by_slug("does-not-exist") is None


class TestMilestones:
    def test_returns_only_milestone_entries(self, repo):
        milestones = repo.milestones()
        assert len(milestones) == 1
        assert milestones[0].frontmatter.title == "First Steps"


class TestByYearMonthDay:
    def test_filters_by_year(self, repo):
        assert len(repo.by_year_month_day(2026)) == 2

    def test_filters_by_year_and_month(self, repo):
        assert len(repo.by_year_month_day(2026, 5)) == 2

    def test_filters_by_full_date(self, repo):
        results = repo.by_year_month_day(2026, 5, 1)
        assert len(results) == 1
        assert results[0].slug == "first-steps"


class TestFilter:
    def test_filter_by_family_member(self, repo):
        results = repo.filter(family_member="Dad")
        assert len(results) == 1
        assert results[0].slug == "picnic-day"

    def test_filter_by_tag(self, repo):
        results = repo.filter(tag="walking")
        assert len(results) == 1
        assert results[0].slug == "first-steps"

    def test_filter_by_milestone_true(self, repo):
        results = repo.filter(milestone=True)
        assert len(results) == 1

    def test_filter_by_milestone_false(self, repo):
        results = repo.filter(milestone=False)
        assert len(results) == 1
        assert results[0].slug == "picnic-day"

    def test_filter_by_date_range(self, repo):
        results = repo.filter(date_from=date(2026, 5, 5), date_to=date(2026, 5, 31))
        assert len(results) == 1
        assert results[0].slug == "picnic-day"

    def test_filter_combined(self, repo):
        results = repo.filter(family_member="Kid A", milestone=True)
        assert len(results) == 1
        assert results[0].slug == "first-steps"

    def test_filter_with_query(self, repo):
        results = repo.filter(query="bubbles")
        assert len(results) == 1
        assert results[0].slug == "picnic-day"


class TestSearch:
    def test_search_matches_title(self, repo):
        results = repo.search("Picnic")
        assert len(results) == 1

    def test_search_matches_body(self, repo):
        results = repo.search("living room")
        assert len(results) == 1
        assert results[0].slug == "first-steps"

    def test_search_is_case_insensitive(self, repo):
        results = repo.search("PICNIC")
        assert len(results) == 1

    def test_search_never_returns_drafts(self, repo):
        results = repo.search("unfinished draft")
        assert results == []

    def test_search_no_match_returns_empty(self, repo):
        assert repo.search("nonexistent-keyword-xyz") == []


class TestAllTags:
    def test_returns_sorted_unique_tags_from_published_only(self, repo):
        assert repo.all_tags() == ["fun", "milestone", "outdoors", "walking"]


class TestMediaReviewedAndPublic:
    def test_reviewed_media_on_public_entry_is_visible(self, repo):
        assert repo.is_media_reviewed_and_public("2026/05/first-steps.jpg") is True

    def test_unknown_media_path_not_visible(self, repo):
        assert repo.is_media_reviewed_and_public("2026/05/nonexistent.jpg") is False


class TestFamilyMembers:
    def test_loads_family_members_from_yaml(self, repo):
        assert set(repo.family_members) == {"Mom", "Dad", "Kid A"}
