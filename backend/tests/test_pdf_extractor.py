import os
import tempfile
import math
import pytest
from unittest.mock import patch
from backend.infrastructure.pdf_extractor import PdfExtractor
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError


@pytest.fixture
def extractor():
    return PdfExtractor()


def _make_empty_pdf(path):
    with open(path, "wb") as f:
        f.write(b"")


def _make_invalid_pdf(path):
    with open(path, "wb") as f:
        f.write(b"not a pdf content")


class TestPdfExtractorFileValidation:
    def test_get_page_count_with_test_pdf(self, extractor, first_test_pdf):
        count = extractor.get_page_count(first_test_pdf)
        assert count == 1

    def test_get_page_count_all_test_pdfs(self, extractor, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            count = extractor.get_page_count(pdf_path)
            assert count == 1

    def test_empty_file_raises_error(self, extractor):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            _make_empty_pdf(tmp_path)
            with pytest.raises(EmptyFileError):
                extractor.get_page_count(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_error(self, extractor):
        with pytest.raises(InvalidPDFError):
            extractor.get_page_count("nonexistent.pdf")

    def test_non_pdf_extension_raises_error(self, extractor):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with open(tmp_path, "w") as f:
                f.write("hello")
            with pytest.raises(InvalidPDFError):
                extractor.get_page_count(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_test_pdf_not_password_protected(self, extractor, first_test_pdf):
        assert extractor.is_password_protected(first_test_pdf) is False


class TestPdfExtractorPageExtraction:
    def test_extract_page_0_returns_blocks(self, extractor, first_test_pdf):
        blocks = extractor.extract_page_blocks(first_test_pdf, 0)
        assert len(blocks) > 0

    def test_extract_page_blocks_raises_for_password_protected(self, extractor, first_test_pdf):
        with patch.object(extractor, "is_password_protected", return_value=True):
            with pytest.raises(PasswordProtectedError):
                extractor.extract_page_blocks(first_test_pdf, 0)

    def test_page_0_contains_company_name(self, extractor, first_test_pdf):
        blocks = extractor.extract_page_blocks(first_test_pdf, 0)
        texts = [b["text"] for b in blocks]
        assert any("EMPRESA FULANO DE TAL" in t for t in texts)

    def test_page_0_contains_employee_name(self, extractor, first_test_pdf):
        blocks = extractor.extract_page_blocks(first_test_pdf, 0)
        texts = [b["text"] for b in blocks]
        assert any("FULANO DE TAL" in t for t in texts)

    def test_page_0_top_half_has_value(self, extractor, first_test_pdf):
        blocks = extractor.extract_page_blocks(first_test_pdf, 0)
        height = extractor.get_page_height(first_test_pdf, 0)
        top_blocks = [b for b in blocks if b["y0"] < height / 2]
        top_texts = [b["text"] for b in top_blocks]
        assert any("3.500,00" in t for t in top_texts)

    def test_all_test_pdfs_have_blocks(self, extractor, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            blocks = extractor.extract_page_blocks(pdf_path, 0)
            assert len(blocks) > 0

    def test_each_test_pdf_has_unique_employee(self, extractor, all_test_pdfs):
        expected_names = ["FULANO DE TAL", "CICLANO DE TAL", "BICLANO DE TAL"]
        for pdf_path, expected in zip(all_test_pdfs, expected_names):
            blocks = extractor.extract_page_blocks(pdf_path, 0)
            texts = [b["text"] for b in blocks]
            assert any(expected in t for t in texts)

    def test_bottom_half_is_empty(self, extractor, first_test_pdf):
        blocks = extractor.extract_page_blocks(first_test_pdf, 0)
        height = extractor.get_page_height(first_test_pdf, 0)
        bottom_blocks = [b for b in blocks if b["y0"] >= height / 2]
        assert len(bottom_blocks) == 0

    def test_get_page_height_returns_a4(self, extractor, first_test_pdf):
        height = extractor.get_page_height(first_test_pdf, 0)
        assert math.isclose(height, 842, rel_tol=0.01)

    def test_extract_invalid_page_raises_error(self, extractor, first_test_pdf):
        with pytest.raises(IndexError):
            extractor.extract_page_blocks(first_test_pdf, 999)

    def test_extract_negative_page_raises_error(self, extractor, first_test_pdf):
        with pytest.raises(IndexError):
            extractor.extract_page_blocks(first_test_pdf, -1)


class TestPdfExtractorPrivateMethods:
    def test_is_horizontal_with_default_matrix(self):
        char = {"matrix": (1, 0, 0, 1), "text": "A"}
        assert PdfExtractor._is_horizontal(char) is True

    def test_is_horizontal_with_rotated_matrix(self):
        char = {"matrix": (0, 1, -1, 0), "text": "A"}
        assert PdfExtractor._is_horizontal(char) is False

    def test_is_horizontal_with_no_matrix(self):
        char = {"text": "A"}
        assert PdfExtractor._is_horizontal(char) is True

    def test_chars_to_words_empty(self):
        assert PdfExtractor._chars_to_words([]) == []

    def test_chars_to_words_single_char(self):
        chars = [{"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "A"}]
        words = PdfExtractor._chars_to_words(chars)
        assert len(words) == 1
        assert words[0]["text"] == "A"

    def test_chars_to_words_merges_adjacent(self):
        chars = [
            {"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "H"},
            {"top": 10, "x0": 10, "x1": 15, "bottom": 15, "text": "i"},
        ]
        words = PdfExtractor._chars_to_words(chars)
        assert len(words) == 1
        assert words[0]["text"] == "Hi"

    def test_chars_to_words_splits_on_gap(self):
        chars = [
            {"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "H"},
            {"top": 10, "x0": 50, "x1": 55, "bottom": 15, "text": "i"},
        ]
        words = PdfExtractor._chars_to_words(chars)
        assert len(words) == 2

    def test_chars_to_words_splits_on_different_line(self):
        chars = [
            {"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "A"},
            {"top": 30, "x0": 5, "x1": 10, "bottom": 35, "text": "B"},
        ]
        words = PdfExtractor._chars_to_words(chars)
        assert len(words) == 2

    def test_merge_chars_single(self):
        chars = [{"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "X"}]
        result = PdfExtractor._merge_chars(chars)
        assert result["text"] == "X"
        assert result["x0"] == 5
        assert result["top"] == 10
        assert result["bottom"] == 15
        assert result["x1"] == 10

    def test_merge_chars_multiple(self):
        chars = [
            {"top": 10, "x0": 5, "x1": 10, "bottom": 15, "text": "A"},
            {"top": 11, "x0": 10, "x1": 15, "bottom": 16, "text": "B"},
        ]
        result = PdfExtractor._merge_chars(chars)
        assert result["text"] == "AB"
        assert result["x0"] == 5
        assert result["top"] == 10
        assert result["bottom"] == 16
        assert result["x1"] == 15

    def test_group_words_into_lines_empty(self, extractor):
        assert extractor._group_words_into_lines([]) == []

    def test_group_words_into_lines_single(self, extractor):
        words = [{"top": 10, "x0": 5, "x1": 50, "bottom": 15, "text": "hello"}]
        lines = extractor._group_words_into_lines(words)
        assert len(lines) == 1
        assert lines[0]["text"] == "hello"

    def test_group_words_into_lines_same_line(self, extractor):
        words = [
            {"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "hello"},
            {"top": 10, "x0": 22, "x1": 40, "bottom": 15, "text": "world"},
        ]
        lines = extractor._group_words_into_lines(words)
        assert len(lines) == 1
        assert "hello" in lines[0]["text"]
        assert "world" in lines[0]["text"]

    def test_group_words_into_lines_different_lines(self, extractor):
        words = [
            {"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "line1"},
            {"top": 30, "x0": 5, "x1": 20, "bottom": 35, "text": "line2"},
        ]
        lines = extractor._group_words_into_lines(words)
        assert len(lines) == 2

    def test_group_words_into_lines_large_gap(self, extractor):
        words = [
            {"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "left"},
            {"top": 10, "x0": 100, "x1": 120, "bottom": 15, "text": "right"},
        ]
        lines = extractor._group_words_into_lines(words)
        assert len(lines) == 2

    def test_group_words_into_lines_backward(self, extractor):
        words = [
            {"top": 10, "x0": 50, "x1": 70, "bottom": 15, "text": "second"},
            {"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "first"},
        ]
        lines = extractor._group_words_into_lines(words)
        assert len(lines) == 2

    def test_merge_words_single(self):
        words = [{"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "hello"}]
        result = PdfExtractor._merge_words(words)
        assert result["text"] == "hello"
        assert result["y0"] == 10
        assert result["y1"] == 15

    def test_merge_words_multiple(self):
        words = [
            {"top": 10, "x0": 5, "x1": 20, "bottom": 15, "text": "hello"},
            {"top": 10, "x0": 22, "x1": 40, "bottom": 15, "text": "world"},
        ]
        result = PdfExtractor._merge_words(words)
        assert result["text"] == "hello world"
        assert result["y0"] == 10
        assert result["y1"] == 15
        assert result["x0"] == 5
        assert result["x1"] == 40
