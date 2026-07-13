import os
import tempfile
import math
import pytest
from backend.infrastructure.pdf_extractor import PdfExtractor
from backend.domain.exceptions import InvalidPDFError, EmptyFileError


SAMPLE_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "contracheque_exemplo.pdf",
)


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
    def test_get_page_count_with_sample_pdf(self, extractor):
        count = extractor.get_page_count(SAMPLE_PDF)
        assert count == 102

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

    def test_sample_pdf_not_password_protected(self, extractor):
        assert extractor.is_password_protected(SAMPLE_PDF) is False


class TestPdfExtractorPageExtraction:
    def test_extract_page_0_returns_blocks(self, extractor):
        blocks = extractor.extract_page_blocks(SAMPLE_PDF, 0)
        assert len(blocks) > 0
        texts = [b["text"] for b in blocks]
        assert any("EMPRESA EXEMPLO" in t for t in texts)
        assert any("Nome do Funcionário" in t for t in texts)
        assert any("Total de Vencimentos" in t for t in texts)

    def test_page_0_contains_expected_employee(self, extractor):
        blocks = extractor.extract_page_blocks(SAMPLE_PDF, 0)
        texts = [b["text"] for b in blocks]
        assert any("NOME DO FUNCIONÁRIO" in t for t in texts)

    def test_page_0_top_half_contains_total_value(self, extractor):
        blocks = extractor.extract_page_blocks(SAMPLE_PDF, 0)
        height = extractor.get_page_height(SAMPLE_PDF, 0)
        assert math.isclose(height, 842, rel_tol=0.01)
        top_blocks = [b for b in blocks if b["y0"] < height / 2]
        top_texts = [b["text"] for b in top_blocks]
        assert any("Total de Vencimentos" in t for t in top_texts)

    def test_page_1_has_different_employee(self, extractor):
        blocks = extractor.extract_page_blocks(SAMPLE_PDF, 1)
        texts = [b["text"] for b in blocks]
        assert any("NOME DO FUNCIONÁRIO" in t for t in texts)
        assert not any("FULANO MARIA" in t for t in texts)

    def test_page_17_has_asterisk_values(self, extractor):
        blocks = extractor.extract_page_blocks(SAMPLE_PDF, 17)
        height = extractor.get_page_height(SAMPLE_PDF, 17)
        top_blocks = [b for b in blocks if b["y0"] < height / 2]
        top_texts = [b["text"] for b in top_blocks]
        asterisk_blocks = [t for t in top_texts if set(t.strip()) == {"*"} or set(t.strip().replace("\n", "")) == {"*"}]
        assert len(asterisk_blocks) > 0

    def test_get_page_height_returns_842(self, extractor):
        height = extractor.get_page_height(SAMPLE_PDF, 0)
        assert math.isclose(height, 842, rel_tol=0.01)

    def test_extract_invalid_page_raises_error(self, extractor):
        with pytest.raises(IndexError):
            extractor.extract_page_blocks(SAMPLE_PDF, 999)
