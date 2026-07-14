import re
import unicodedata
from dataclasses import dataclass


@dataclass
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


class ExtractionStrategy:

    LABEL_NOME = "Nome do Funcionário"
    LABEL_TOTAL_VENC = "Total de Vencimentos"

    _VALUE_PATTERN = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
    _SKIP_WORDS = frozenset({
        "Código", "Departamento", "Filial", "Admissão:",
        "Folha", "Mensalista", "CC:", "CNPJ",
    })

    def is_top_half(self, block_y: float, page_height: float) -> bool:
        return block_y < page_height / 2

    def is_asterisk_only(self, value: str) -> bool:
        cleaned = value.strip().replace(" ", "").replace("\n", "")
        return len(cleaned) > 0 and all(c == "*" for c in cleaned)

    def _is_likely_value(self, text: str) -> bool:
        return bool(self._VALUE_PATTERN.match(text.strip().replace("\n", "")))

    @staticmethod
    def _normalize(text: str) -> str:
        return "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        ).lower()

    def extract_employee_name(self, blocks: list[dict], page_height: float) -> str | None:
        top_blocks = [b for b in blocks if self.is_top_half(b["y0"], page_height)]

        name_label_block = None
        for b in top_blocks:
            text = b["text"].strip()
            if self.LABEL_NOME in text:
                name_label_block = b
                break

        if name_label_block is not None:
            return self._extract_name_near_label(top_blocks, name_label_block)

        return self._extract_name_by_position(top_blocks, page_height)

    def _extract_name_near_label(self, top_blocks, label_block):
        label_x0 = label_block["x0"]
        label_x1 = label_block["x1"]
        label_y0 = label_block["y0"]
        label_y1 = label_block["y1"]
        name_candidates = []
        for b in top_blocks:
            if b is label_block:
                continue
            tx = b["x0"]
            ty = b["y0"]
            txt = b["text"].strip()
            if not txt or txt in self._SKIP_WORDS or len(txt) < 3:
                continue
            if tx >= label_x0 and tx <= label_x1 + 200:
                if ty >= label_y0 - 5 and ty <= label_y1 + 15:
                    name_candidates.append((tx, txt))
        if not name_candidates:
            return None
        name_candidates.sort(key=lambda x: x[0])
        return name_candidates[0][1]

    def _extract_name_by_position(self, top_blocks, page_height):
        candidates = []
        for b in top_blocks:
            txt = b["text"].strip()
            if not txt or len(txt) < 3:
                continue
            if self._is_likely_value(txt):
                continue
            if self._normalize(txt) in {self._normalize(w) for w in self._SKIP_WORDS}:
                continue
            y_ratio = b["y0"] / page_height
            if 0.05 <= y_ratio <= 0.12:
                candidates.append((b["x0"], txt))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def extract_total_vencimentos(self, blocks: list[dict], page_height: float) -> str | None:
        top_blocks = [b for b in blocks if self.is_top_half(b["y0"], page_height)]

        label_block = None
        for b in top_blocks:
            text = b["text"].strip()
            if self.LABEL_TOTAL_VENC in text:
                label_block = b
                break

        if label_block is not None:
            return self._extract_value_near_label(top_blocks, label_block)

        return self._extract_value_by_position(top_blocks, page_height)

    def _extract_value_near_label(self, top_blocks, label_block):
        label_y0 = label_block["y0"]
        label_y1 = label_block["y1"]
        label_x0 = label_block["x0"]
        label_x1 = label_block["x1"]
        candidates = []
        for b in top_blocks:
            if b is label_block:
                continue
            tx0 = b["x0"]
            ty0 = b["y0"]
            ty1 = b["y1"]
            txt = b["text"].strip().replace("\n", "")
            if not txt:
                continue
            if tx0 >= label_x0 - 20:
                if ty0 >= label_y0 - 5 and ty1 <= label_y1 + 25:
                    candidates.append((tx0, txt))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _extract_value_by_position(self, top_blocks, page_height):
        value_candidates = []
        for b in top_blocks:
            txt = b["text"].strip().replace("\n", "")
            if not txt or not self._is_likely_value(txt):
                continue
            y_ratio = b["y0"] / page_height
            if 0.12 <= y_ratio <= 0.20:
                value_candidates.append((b["y0"], b["x0"], txt))
        if not value_candidates:
            return None
        value_candidates.sort(key=lambda c: (c[0], c[1]))
        return value_candidates[0][2]
