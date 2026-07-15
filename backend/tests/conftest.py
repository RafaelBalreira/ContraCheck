import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

TEST_PDF_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "docs", "for_testing",
)

TEST_PDF_NAMES = [
    "holerite_test_1.pdf",
    "holerite_test_2.pdf",
    "holerite_test_3.pdf",
]


@pytest.fixture
def test_pdf_dir():
    return os.path.abspath(TEST_PDF_DIR)


@pytest.fixture
def all_test_pdfs(test_pdf_dir):
    return [os.path.join(test_pdf_dir, name) for name in TEST_PDF_NAMES]


@pytest.fixture
def first_test_pdf(test_pdf_dir):
    return os.path.join(test_pdf_dir, TEST_PDF_NAMES[0])
