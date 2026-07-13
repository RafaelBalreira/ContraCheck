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

    def is_top_half(self, block_y: float, page_height: float) -> bool:
        return block_y < page_height / 2

    def is_asterisk_only(self, value: str) -> bool:
        cleaned = value.strip().replace(" ", "").replace("\n", "")
        return len(cleaned) > 0 and all(c == "*" for c in cleaned)

    def extract_employee_name(self, blocks: list[dict], page_height: float) -> str | None:
        top_blocks = [b for b in blocks if self.is_top_half(b["y0"], page_height)]
        name_label_block = None
        for b in top_blocks:
            text = b["text"].strip()
            if self.LABEL_NOME in text:
                name_label_block = b
                break
        if name_label_block is None:
            return None
        label_x0 = name_label_block["x0"]
        label_x1 = name_label_block["x1"]
        label_y0 = name_label_block["y0"]
        label_y1 = name_label_block["y1"]
        name_candidates = []
        for b in top_blocks:
            if b is name_label_block:
                continue
            tx = b["x0"]
            ty = b["y0"]
            txt = b["text"].strip()
            if not txt or txt in ("Código", "Departamento", "Filial", "Admissão:"):
                continue
            if len(txt) < 3:
                continue
            if tx >= label_x0 and tx <= label_x1 + 200:
                if ty >= label_y0 - 5 and ty <= label_y1 + 15:
                    name_candidates.append((tx, txt))
        if not name_candidates:
            return None
        name_candidates.sort(key=lambda x: x[0])
        return name_candidates[0][1]

    def extract_total_vencimentos(self, blocks: list[dict], page_height: float) -> str | None:
        top_blocks = [b for b in blocks if self.is_top_half(b["y0"], page_height)]
        label_block = None
        for b in top_blocks:
            text = b["text"].strip()
            if self.LABEL_TOTAL_VENC in text:
                label_block = b
                break
        if label_block is None:
            return None
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
