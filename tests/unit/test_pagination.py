from diary.pagination import ALLOWED_PAGE_SIZES, DEFAULT_PAGE_SIZE, paginate, resolve_page_size


class TestResolvePageSize:
    def test_none_falls_back_to_default(self):
        assert resolve_page_size(None) == DEFAULT_PAGE_SIZE

    def test_allowed_values_pass_through(self):
        for size in ALLOWED_PAGE_SIZES:
            assert resolve_page_size(size) == size

    def test_disallowed_value_falls_back_to_default(self):
        assert resolve_page_size(7) == DEFAULT_PAGE_SIZE
        assert resolve_page_size(0) == DEFAULT_PAGE_SIZE
        assert resolve_page_size(-5) == DEFAULT_PAGE_SIZE
        assert resolve_page_size(999) == DEFAULT_PAGE_SIZE

    def test_default_is_five(self):
        assert DEFAULT_PAGE_SIZE == 5

    def test_allowed_sizes_are_5_10_20(self):
        assert ALLOWED_PAGE_SIZES == (5, 10, 20)


class TestPaginate:
    def test_default_page_size_five_splits_into_expected_chunks(self):
        items = list(range(12))
        page = paginate(items, page=1, page_size=resolve_page_size(None))
        assert page.items == [0, 1, 2, 3, 4]
        assert page.total_pages == 3
        assert page.has_next is True
        assert page.has_prev is False

    def test_second_page_with_size_ten(self):
        items = list(range(25))
        page = paginate(items, page=2, page_size=10)
        assert page.items == list(range(10, 20))
        assert page.total_pages == 3

    def test_page_size_twenty_fits_all_in_one_page(self):
        items = list(range(15))
        page = paginate(items, page=1, page_size=20)
        assert page.items == items
        assert page.total_pages == 1
        assert page.has_next is False


class TestPageNumbers:
    def test_single_page_returns_just_one(self):
        page = paginate(list(range(3)), page=1, page_size=20)
        assert page.page_numbers() == [1]

    def test_few_pages_shows_all_no_ellipsis(self):
        page = paginate(list(range(15)), page=2, page_size=5)
        assert page.total_pages == 3
        assert page.page_numbers() == [1, 2, 3]

    def test_current_page_in_middle_shows_ellipsis_on_both_sides(self):
        page = paginate(list(range(100)), page=6, page_size=5)
        assert page.total_pages == 20
        assert page.page_numbers() == [1, None, 5, 6, 7, None, 20]

    def test_current_page_near_start_has_no_leading_ellipsis(self):
        page = paginate(list(range(100)), page=1, page_size=5)
        assert page.page_numbers() == [1, 2, None, 20]

    def test_current_page_near_end_has_no_trailing_ellipsis(self):
        page = paginate(list(range(100)), page=20, page_size=5)
        assert page.page_numbers() == [1, None, 19, 20]
