import pytest
from backend.application.extraction_strategy import ExtractionStrategy


@pytest.fixture
def strategy():
    return ExtractionStrategy()


class TestIsTopHalf:
    def test_top_half_returns_true(self, strategy):
        assert strategy.is_top_half(100, 842) is True

    def test_bottom_half_returns_false(self, strategy):
        assert strategy.is_top_half(500, 842) is False

    def test_exact_midpoint_returns_false(self, strategy):
        assert strategy.is_top_half(421, 842) is False

    def test_zero_y_returns_true(self, strategy):
        assert strategy.is_top_half(0, 842) is True

    def test_y_just_below_mid_returns_true(self, strategy):
        assert strategy.is_top_half(420, 842) is True


class TestIsAsteriskOnly:
    def test_asterisk_sequence_returns_true(self, strategy):
        assert strategy.is_asterisk_only("******") is True

    def test_asterisk_with_spaces_returns_true(self, strategy):
        assert strategy.is_asterisk_only("* * * *") is True

    def test_asterisk_with_newline_returns_true(self, strategy):
        assert strategy.is_asterisk_only("*****\n*****") is True

    def test_numeric_value_returns_false(self, strategy):
        assert strategy.is_asterisk_only("0.000,00") is False

    def test_mixed_content_returns_false(self, strategy):
        assert strategy.is_asterisk_only("***1***") is False

    def test_empty_string_returns_false(self, strategy):
        assert strategy.is_asterisk_only("") is False

    def test_blank_string_returns_false(self, strategy):
        assert strategy.is_asterisk_only("   ") is False


class TestExtractEmployeeName:
    PAGE_HEIGHT = 842

    def _make_block(self, x0, y0, x1, y1, text):
        return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": text}

    def _make_page(self, *, name_label_x0=71, name_label_y0=73, name_label_y1=89,
                   name_x0=71, name_y0=80, name_y1=89, name="JOÃO SILVA",
                   extra_blocks=None):
        blocks = [
            self._make_block(29, 39, 210, 49, "EMPRESA EXEMPLO"),
            self._make_block(name_label_x0, name_label_y0, 398, name_label_y1,
                             f"Nome do Funcionário | CBO | 142205"),
            self._make_block(name_x0, name_y0, name_x0 + 150, name_y1, name),
            self._make_block(373, 299, 412, 304, "Total de Vencimentos"),
            self._make_block(379, 312, 425, 321, "0.000,00"),
        ]
        if extra_blocks:
            blocks.extend(extra_blocks)
        return blocks

    def test_extracts_name_from_top_half(self, strategy):
        blocks = self._make_page(name="JOÃO SILVA")
        result = strategy.extract_employee_name(blocks, self.PAGE_HEIGHT)
        assert result == "JOÃO SILVA"

    def test_extracts_name_with_accents(self, strategy):
        blocks = self._make_page(name="MARIA SOUZA")
        result = strategy.extract_employee_name(blocks, self.PAGE_HEIGHT)
        assert result == "MARIA SOUZA"

    def test_returns_none_when_label_missing(self, strategy):
        blocks = [
            self._make_block(29, 39, 210, 49, "EMPRESA EXEMPLO"),
            self._make_block(373, 299, 412, 304, "Total de Vencimentos"),
        ]
        result = strategy.extract_employee_name(blocks, self.PAGE_HEIGHT)
        assert result is None

    def test_ignores_blocks_from_bottom_half(self, strategy):
        blocks = [
            self._make_block(71, 73, 398, 89, "Nome do Funcionário | CBO"),
            self._make_block(71, 80, 217, 89, "JOÃO SILVA"),
            self._make_block(71, 461, 398, 478, "Nome do Funcionário | CBO"),
            self._make_block(71, 468, 217, 478, "JOÃO SILVA BOTTOM"),
            self._make_block(373, 299, 412, 304, "Total de Vencimentos"),
            self._make_block(379, 312, 425, 321, "0.000,00"),
        ]
        result = strategy.extract_employee_name(blocks, self.PAGE_HEIGHT)
        assert result == "JOÃO SILVA"
        assert result != "JOÃO SILVA BOTTOM"

    def test_returns_none_when_name_block_not_found(self, strategy):
        blocks = [
            self._make_block(71, 73, 398, 89, "Nome do Funcionário | CBO"),
            self._make_block(373, 299, 412, 304, "Total de Vencimentos"),
        ]
        result = strategy.extract_employee_name(blocks, self.PAGE_HEIGHT)
        assert result is None


class TestExtractTotalVencimentos:
    PAGE_HEIGHT = 842

    def _make_block(self, x0, y0, x1, y1, text):
        return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "text": text}

    def _make_page(self, *, total_label_x0=373, total_label_y0=299, total_label_y1=304,
                   value_x0=379, value_y0=312, value_y1=321, value="0.000,00"):
        blocks = [
            self._make_block(29, 39, 210, 49, "EMPRESA EXEMPLO"),
            self._make_block(71, 73, 398, 89, "Nome do Funcionário | CBO"),
            self._make_block(71, 80, 217, 89, "JOÃO SILVA"),
            self._make_block(total_label_x0, total_label_y0, total_label_x0 + 40, total_label_y1,
                             "Total de Vencimentos"),
            self._make_block(value_x0, value_y0, value_x0 + 60, value_y1, value),
        ]
        return blocks

    def test_extracts_total_from_top_half(self, strategy):
        blocks = self._make_page(value="0.000,00")
        result = strategy.extract_total_vencimentos(blocks, self.PAGE_HEIGHT)
        assert result == "0.000,00"

    def test_extracts_value_right_of_label(self, strategy):
        blocks = self._make_page(value="13.678,88")
        result = strategy.extract_total_vencimentos(blocks, self.PAGE_HEIGHT)
        assert result == "13.678,88"

    def test_returns_none_when_label_missing(self, strategy):
        blocks = [
            self._make_block(29, 39, 210, 49, "EMPRESA EXEMPLO"),
        ]
        result = strategy.extract_total_vencimentos(blocks, self.PAGE_HEIGHT)
        assert result is None

    def test_ignores_bottom_half_values(self, strategy):
        blocks = [
            self._make_block(373, 299, 412, 304, "Total de Vencimentos"),
            self._make_block(379, 312, 425, 321, "0.000,00"),
            self._make_block(373, 687, 412, 692, "Total de Vencimentos"),
            self._make_block(379, 700, 425, 710, "999,99"),
        ]
        result = strategy.extract_total_vencimentos(blocks, self.PAGE_HEIGHT)
        assert result == "0.000,00"
