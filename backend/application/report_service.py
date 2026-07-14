import io
import csv
import os
import platform
import pandas as pd
from fpdf import FPDF
from backend.domain.models import PaySlip


def _find_font(*names: str) -> str:
    system = platform.system()
    if system == "Windows":
        candidates = [f"C:/Windows/Fonts/{n}.ttf" for n in names]
    elif system == "Linux":
        candidates = []
        for n in names:
            candidates += [
                f"/usr/share/fonts/truetype/dejavu/{n}.ttf",
                f"/usr/share/fonts/truetype/liberation/{n}-Regular.ttf",
                f"/usr/share/fonts/truetype/freefont/{n}.ttf",
            ]
    elif system == "Darwin":
        candidates = [f"/Library/Fonts/{n}.ttf" for n in names]
    else:
        candidates = []
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        f"No suitable TTF font found. Searched: {candidates}"
    )


def _sort_key(name: str) -> str:
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", name)
        if unicodedata.category(c) != "Mn"
    ).lower()


def records_to_dataframe(records: list[PaySlip]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=["Nome do Funcionário", "Total de Vencimentos", "Arquivo"])
    sorted_records = sorted(records, key=lambda r: _sort_key(r.employee_name))
    data = [
        {
            "Nome do Funcionário": r.employee_name,
            "Total de Vencimentos": r.total_vencimentos,
            "Arquivo": r.source_file,
        }
        for r in sorted_records
    ]
    return pd.DataFrame(data)


def generate_csv(records: list[PaySlip]) -> bytes:
    df = records_to_dataframe(records)
    output = io.StringIO()
    df.to_csv(
        output,
        index=False,
        sep=",",
        encoding="utf-8",
        quoting=csv.QUOTE_NONNUMERIC,
    )
    return output.getvalue().encode("utf-8-sig")


def generate_xlsx(records: list[PaySlip]) -> bytes:
    df = records_to_dataframe(records)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Relatório")
    return output.getvalue()


class _PdfReport(FPDF):

    def __init__(self, total_records: int, total_ignored: int):
        super().__init__(orientation="L", unit="mm", format="A4")
        self._total_records = total_records
        self._total_ignored = total_ignored
        self.add_font("arial", "", _find_font("arial", "DejaVuSans", "LiberationSans"))
        self.add_font("arial", "B", _find_font("arialbd", "DejaVuSans-Bold", "LiberationSans-Bold"))
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("arial", "B", 14)
        self.cell(0, 10, "Relatório de Contracheques", new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("arial", "", 10)
        self.cell(0, 6,
                  f"Total: {self._total_records} registros | Ignorados: {self._total_ignored}",
                  new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("arial", "", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    def _draw_table_header(self, col_widths: tuple[float, float, float]):
        self.set_font("arial", "B", 9)
        self.set_fill_color(25, 118, 210)
        self.set_text_color(255, 255, 255)
        headers = ["Nome do Funcionário", "Total de Vencimentos", "Arquivo"]
        for header, w in zip(headers, col_widths):
            self.cell(w, 8, header, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)

    def add_records(self, records: list[PaySlip]):
        col_widths = (100, 50, 120)

        self._draw_table_header(col_widths)

        self.set_font("arial", "", 8)
        fill = False
        for record in records:
            if self.get_y() + 7 > self.h - 15:
                self.add_page()
                self._draw_table_header(col_widths)
                self.set_font("arial", "", 8)
                fill = False

            if fill:
                self.set_fill_color(240, 240, 240)
            else:
                self.set_fill_color(255, 255, 255)
            self.cell(col_widths[0], 7, record.employee_name, border=1, fill=True)
            self.cell(col_widths[1], 7, record.total_vencimentos, border=1, fill=True, align="R")
            self.cell(col_widths[2], 7, record.source_file, border=1, fill=True)
            self.ln()
            fill = not fill


def generate_pdf(records: list[PaySlip], ignored_count: int = 0) -> bytes:
    sorted_records = sorted(records, key=lambda r: _sort_key(r.employee_name))
    pdf = _PdfReport(total_records=len(sorted_records), total_ignored=ignored_count)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.add_records(sorted_records)
    return bytes(pdf.output())

