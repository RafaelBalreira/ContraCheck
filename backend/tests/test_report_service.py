import io
import csv
import pandas as pd
import pytest
from backend.domain.models import PaySlip
from backend.application.report_service import (
    records_to_dataframe,
    generate_csv,
    generate_xlsx,
    generate_pdf,
    _sort_key,
)


@pytest.fixture
def records():
    return [
        PaySlip(employee_name="MARIA SOUZA", total_vencimentos="5.000,00", source_file="a.pdf"),
        PaySlip(employee_name="ALBERTO SILVA", total_vencimentos="3.000,00", source_file="b.pdf"),
        PaySlip(employee_name="ana costa", total_vencimentos="4.000,00", source_file="a.pdf"),
    ]


@pytest.fixture
def empty_records():
    return []


class TestSortKey:
    def test_strips_accents(self):
        assert _sort_key("João") == "joao"

    def test_lowercases(self):
        assert _sort_key("MARIA") == "maria"

    def test_plain_ascii(self):
        assert _sort_key("silva") == "silva"


class TestRecordsToDataframe:
    def test_returns_dataframe(self, records):
        df = records_to_dataframe(records)
        assert isinstance(df, pd.DataFrame)

    def test_has_expected_columns(self, records):
        df = records_to_dataframe(records)
        assert list(df.columns) == ["Nome do Funcionário", "Total de Vencimentos", "Arquivo"]

    def test_sorts_by_name_alphabetically(self, records):
        df = records_to_dataframe(records)
        names = df["Nome do Funcionário"].tolist()
        assert names == ["ALBERTO SILVA", "ana costa", "MARIA SOUZA"]

    def test_empty_records_returns_empty_dataframe(self, empty_records):
        df = records_to_dataframe(empty_records)
        assert len(df) == 0
        assert list(df.columns) == ["Nome do Funcionário", "Total de Vencimentos", "Arquivo"]


class TestGenerateCsv:
    def test_returns_bytes(self, records):
        result = generate_csv(records)
        assert isinstance(result, bytes)

    def test_contains_headers(self, records):
        result = generate_csv(records).decode("utf-8-sig")
        assert "Nome do Funcionário" in result
        assert "Total de Vencimentos" in result
        assert "Arquivo" in result

    def test_rows_sorted_alphabetically(self, records):
        content = generate_csv(records).decode("utf-8-sig")
        lines = content.strip().split("\n")
        data_lines = lines[1:]
        assert len(data_lines) == 3
        assert "ALBERTO SILVA" in data_lines[0]
        assert "ana costa" in data_lines[1]
        assert "MARIA SOUZA" in data_lines[2]

    def test_empty_records(self, empty_records):
        result = generate_csv(empty_records).decode("utf-8-sig")
        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_utf8_bom(self, records):
        result = generate_csv(records)
        assert result[:3] == b"\xef\xbb\xbf"


class TestGenerateXlsx:
    def test_returns_bytes(self, records):
        result = generate_xlsx(records)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_is_valid_xlsx(self, records):
        result = generate_xlsx(records)
        assert result[:2] == b"PK"

    def test_empty_records(self, empty_records):
        result = generate_xlsx(empty_records)
        assert isinstance(result, bytes)


class TestGeneratePdf:
    def test_returns_bytes(self, records):
        result = generate_pdf(records)
        assert isinstance(result, bytes)

    def test_starts_with_pdf_header(self, records):
        result = generate_pdf(records)
        assert result[:5] == b"%PDF-"

    def test_with_ignored_count(self, records):
        result = generate_pdf(records, ignored_count=5)
        assert result[:5] == b"%PDF-"

    def test_empty_records(self, empty_records):
        result = generate_pdf(empty_records)
        assert result[:5] == b"%PDF-"

    def test_rows_sorted_alphabetically(self, records):
        result = generate_pdf(records)
        assert isinstance(result, bytes)
        assert len(result) > 100

    def test_page_break_with_many_records(self):
        many_records = [
            PaySlip(employee_name=f"FUNCIONARIO {i:03d}", total_vencimentos="3.000,00", source_file="a.pdf")
            for i in range(50)
        ]
        result = generate_pdf(many_records, ignored_count=2)
        assert result[:5] == b"%PDF-"
        assert len(result) > 1000
