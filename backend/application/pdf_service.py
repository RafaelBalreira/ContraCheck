import os
from backend.domain.models import PaySlip, IgnoredRecord, ProcessResult
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError
from backend.application.extraction_strategy import ExtractionStrategy
from backend.infrastructure.pdf_extractor import PdfExtractor


class PdfService:

    def __init__(self):
        self._extractor = PdfExtractor()
        self._strategy = ExtractionStrategy()

    def process_pdf(self, file_path: str, source_file: str = "") -> ProcessResult:
        if not os.path.exists(file_path):
            raise InvalidPDFError("Arquivo não encontrado.")
        if os.path.getsize(file_path) == 0:
            raise EmptyFileError("O arquivo está vazio.")

        if self._extractor.is_password_protected(file_path):
            raise PasswordProtectedError("O PDF está protegido por senha.")

        total_pages = self._extractor.get_page_count(file_path)
        records: list[PaySlip] = []
        ignored_details: list[IgnoredRecord] = []
        warnings: list[str] = []

        for page_num in range(total_pages):
            try:
                blocks = self._extractor.extract_page_blocks(file_path, page_num)
                page_height = self._extractor.get_page_height(file_path, page_num)

                name = self._strategy.extract_employee_name(blocks, page_height)
                total = self._strategy.extract_total_vencimentos(blocks, page_height)

                if name is None or total is None:
                    reason = "Campos 'Nome do Funcionário' ou 'Total de Vencimentos' não encontrados"
                    ignored_details.append(IgnoredRecord(page=page_num + 1, reason=reason, source_file=source_file))
                    warnings.append(f"Página {page_num + 1}: {reason}")
                    continue

                if self._strategy.is_asterisk_only(total):
                    reason = "Total de Vencimentos contém apenas asteriscos"
                    ignored_details.append(IgnoredRecord(page=page_num + 1, reason=reason, source_file=source_file))
                    continue

                records.append(PaySlip(employee_name=name, total_vencimentos=total, source_file=source_file))

            except Exception as e:
                reason = f"Erro ao processar: {str(e)}"
                ignored_details.append(IgnoredRecord(page=page_num + 1, reason=reason, source_file=source_file))
                warnings.append(f"Página {page_num + 1}: {reason}")

        return ProcessResult(
            records=records,
            ignored_details=ignored_details,
            total_pages=total_pages,
            total_records=len(records),
            ignored_records=len(ignored_details),
            warnings=warnings,
        )
