import pdfplumber
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError


class PdfExtractor:
    _MAX_LINE_GAP = 15

    def get_page_count(self, file_path: str) -> int:
        self._validate_file(file_path)
        pdf = pdfplumber.open(file_path)
        try:
            return len(pdf.pages)
        finally:
            pdf.close()

    def is_password_protected(self, file_path: str) -> bool:
        with open(file_path, "rb") as f:
            parser = PDFParser(f)
            try:
                doc = PDFDocument(parser)
                return doc.is_encrypted
            except Exception:
                return False

    def extract_page_blocks(self, file_path: str, page_num: int) -> list[dict]:
        self._validate_file(file_path)
        if self.is_password_protected(file_path):
            raise PasswordProtectedError("O PDF está protegido por senha.")
        pdf = pdfplumber.open(file_path)
        try:
            if page_num < 0 or page_num >= len(pdf.pages):
                raise IndexError(f"Page {page_num} out of range (0-{len(pdf.pages) - 1})")
            page = pdf.pages[page_num]
            h_chars = [c for c in page.chars if self._is_horizontal(c)]
            words = self._chars_to_words(h_chars)
            return self._group_words_into_lines(words)
        finally:
            pdf.close()

    def get_page_height(self, file_path: str, page_num: int) -> float:
        pdf = pdfplumber.open(file_path)
        try:
            return pdf.pages[page_num].height
        finally:
            pdf.close()

    @staticmethod
    def _is_horizontal(char: dict) -> bool:
        a, b, c, d = char.get("matrix", (1, 0, 0, 1))[:4]
        return abs(b) < 0.1 and abs(c) < 0.1

    @staticmethod
    def _chars_to_words(chars: list[dict]) -> list[dict]:
        if not chars:
            return []
        sorted_chars = sorted(chars, key=lambda c: (c["top"], c["x0"]))
        words = []
        current = [sorted_chars[0]]
        for char in sorted_chars[1:]:
            prev = current[-1]
            same_line = abs(char["top"] - prev["top"]) < 3
            gap = char["x0"] - prev["x1"]
            if same_line and -10 < gap < 5:
                current.append(char)
            else:
                words.append(PdfExtractor._merge_chars(current))
                current = [char]
        words.append(PdfExtractor._merge_chars(current))
        return words

    @staticmethod
    def _merge_chars(chars: list[dict]) -> dict:
        return {
            "x0": min(c["x0"] for c in chars),
            "top": min(c["top"] for c in chars),
            "bottom": max(c["bottom"] for c in chars),
            "x1": max(c["x1"] for c in chars),
            "text": "".join(c["text"] for c in chars),
        }

    def _group_words_into_lines(self, words: list[dict]) -> list[dict]:
        if not words:
            return []
        sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
        lines = []
        current_words = [sorted_words[0]]
        line_y = sorted_words[0]["top"]
        for word in sorted_words[1:]:
            same_y = abs(word["top"] - line_y) < 3
            gap = word["x0"] - current_words[-1]["x1"]
            x_backward = word["x0"] < current_words[0]["x0"] - 5
            if same_y and not x_backward and gap <= self._MAX_LINE_GAP:
                current_words.append(word)
            else:
                lines.append(self._merge_words(current_words))
                current_words = [word]
                line_y = word["top"]
        lines.append(self._merge_words(current_words))
        return lines

    @staticmethod
    def _merge_words(words: list[dict]) -> dict:
        return {
            "x0": min(w["x0"] for w in words),
            "y0": min(w["top"] for w in words),
            "x1": max(w["x1"] for w in words),
            "y1": max(w.get("bottom", w["top"]) for w in words),
            "text": " ".join(w["text"] for w in words),
        }

    def _validate_file(self, file_path: str) -> None:
        import os
        if not os.path.exists(file_path):
            raise InvalidPDFError("Arquivo não encontrado.")
        if os.path.getsize(file_path) == 0:
            raise EmptyFileError("O arquivo está vazio.")
        if not file_path.lower().endswith(".pdf"):
            raise InvalidPDFError("Formato de arquivo inválido. Selecione um arquivo PDF.")
