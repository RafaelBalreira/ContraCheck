import os
import tempfile
import pytest
from backend.application.pdf_service import PdfService
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError


SAMPLE_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "contracheque_exemplo.pdf",
)


@pytest.fixture
def service():
    return PdfService()


class TestPdfServiceValidation:
    def test_nonexistent_file_raises_error(self, service):
        with pytest.raises(InvalidPDFError):
            service.process_pdf("nonexistent.pdf")

    def test_empty_file_raises_error(self, service):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            with pytest.raises(EmptyFileError):
                service.process_pdf(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestPdfServiceWithSample:
    def test_process_sample_pdf_returns_result(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        assert result is not None
        assert result.total_pages == 102

    def test_process_sample_has_records(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        assert result.total_records > 0

    def test_only_top_half_records_extracted(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        for r in result.records:
            assert "BOTTOM" not in r.employee_name

    def test_all_records_have_name_and_value(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        for r in result.records:
            assert r.employee_name, "Employee name should not be empty"
            assert r.total_vencimentos, "Total vencimentos should not be empty"

    def test_ignored_records_counted(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        assert result.ignored_records >= 1

    def test_ignored_records_have_details(self, service):
        result = service.process_pdf(SAMPLE_PDF, source_file="test.pdf")
        assert len(result.ignored_details) >= 1
        for ign in result.ignored_details:
            assert ign.page > 0
            assert ign.reason
            assert ign.source_file == "test.pdf"

    def test_records_have_source_file(self, service):
        result = service.process_pdf(SAMPLE_PDF, source_file="sample.pdf")
        for r in result.records:
            assert r.source_file == "sample.pdf"


class TestPdfServiceSpecificPages:
    def test_page_1_employee_name(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        first = result.records[0]
        assert "FULANO" in first.employee_name.upper()

    def test_page_2_different_employee(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        if len(result.records) > 1:
            second = result.records[1]
            assert "CICLANO" in second.employee_name.upper()

    def test_records_have_formatted_values(self, service):
        result = service.process_pdf(SAMPLE_PDF)
        for r in result.records[:5]:
            assert r.total_vencimentos.replace(",", "").replace(".", "").replace("R$", "").strip().replace(" ", ""), (
                f"Value should be present: {r.total_vencimentos!r}"
            )
