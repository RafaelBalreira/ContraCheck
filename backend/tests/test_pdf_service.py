import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from backend.application.pdf_service import PdfService
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError


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

    def test_password_protected_raises_error(self, service, first_test_pdf):
        with patch.object(service._extractor, "is_password_protected", return_value=True):
            with pytest.raises(PasswordProtectedError):
                service.process_pdf(first_test_pdf)


class TestPdfServiceIgnoredRecords:
    def test_ignored_when_name_is_none(self, service, first_test_pdf):
        with patch.object(service._strategy, "extract_employee_name", return_value=None):
            result = service.process_pdf(first_test_pdf)
            assert result.total_records == 0
            assert result.ignored_records == 1
            assert "não encontrados" in result.ignored_details[0].reason

    def test_ignored_when_total_is_none(self, service, first_test_pdf):
        with patch.object(service._strategy, "extract_total_vencimentos", return_value=None):
            result = service.process_pdf(first_test_pdf)
            assert result.total_records == 0
            assert result.ignored_records == 1
            assert "não encontrados" in result.ignored_details[0].reason

    def test_ignored_when_total_is_asterisk_only(self, service, first_test_pdf):
        with patch.object(service._strategy, "extract_total_vencimentos", return_value="*****"):
            result = service.process_pdf(first_test_pdf)
            assert result.total_records == 0
            assert result.ignored_records == 1
            assert "asteriscos" in result.ignored_details[0].reason

    def test_ignored_when_extraction_raises_exception(self, service, first_test_pdf):
        with patch.object(service._extractor, "extract_page_blocks", side_effect=RuntimeError("boom")):
            result = service.process_pdf(first_test_pdf)
            assert result.total_records == 0
            assert result.ignored_records == 1
            assert "Erro ao processar" in result.ignored_details[0].reason
            assert len(result.warnings) == 1


class TestPdfServiceWithTestPdfs:
    def test_process_each_pdf_returns_result(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            result = service.process_pdf(pdf_path)
            assert result is not None
            assert result.total_pages == 1

    def test_each_pdf_has_one_record(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            result = service.process_pdf(pdf_path)
            assert result.total_records == 1
            assert result.ignored_records == 0

    def test_all_records_have_name_and_value(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            result = service.process_pdf(pdf_path)
            for r in result.records:
                assert r.employee_name, "Employee name should not be empty"
                assert r.total_vencimentos, "Total vencimentos should not be empty"

    def test_records_have_source_file(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            fname = os.path.basename(pdf_path)
            result = service.process_pdf(pdf_path, source_file=fname)
            for r in result.records:
                assert r.source_file == fname


class TestPdfServiceSpecificPages:
    def test_first_pdf_employee_name(self, service, first_test_pdf):
        result = service.process_pdf(first_test_pdf)
        first = result.records[0]
        assert "FULANO DE TAL" in first.employee_name.upper()

    def test_second_pdf_employee_name(self, service, all_test_pdfs):
        result = service.process_pdf(all_test_pdfs[1])
        assert "CICLANO DE TAL" in result.records[0].employee_name.upper()

    def test_third_pdf_employee_name(self, service, all_test_pdfs):
        result = service.process_pdf(all_test_pdfs[2])
        assert "BICLANO DE TAL" in result.records[0].employee_name.upper()

    def test_all_records_have_formatted_values(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            result = service.process_pdf(pdf_path)
            for r in result.records:
                assert r.total_vencimentos.replace(",", "").replace(".", "").strip(), (
                    f"Value should be present: {r.total_vencimentos!r}"
                )

    def test_no_ignored_records(self, service, all_test_pdfs):
        for pdf_path in all_test_pdfs:
            result = service.process_pdf(pdf_path)
            assert result.ignored_records == 0
            assert len(result.ignored_details) == 0
