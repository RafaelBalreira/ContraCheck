import os
import io
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app


SAMPLE_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "contracheque_exemplo.pdf",
)


@pytest.fixture
def client():
    return TestClient(app)


class TestUploadEndpoint:
    def test_upload_valid_pdf_returns_200(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "totalPages" in data
        assert "totalRecords" in data
        assert "ignoredRecordsCount" in data
        assert "ignoredRecords" in data
        assert data["totalPages"] == 102
        assert data["ignoredRecordsCount"] >= 1

    def test_upload_invalid_extension_returns_400(self, client):
        response = client.post("/api/upload", files={"files": ("file.txt", b"hello", "text/plain")})
        assert response.status_code == 400
        assert "Formato de arquivo inválido" in response.json()["detail"]

    def test_upload_empty_file_returns_400(self, client):
        response = client.post("/api/upload", files={"files": ("empty.pdf", b"", "application/pdf")})
        assert response.status_code == 400
        assert "vazio" in response.json()["detail"].lower()

    def test_upload_no_file_returns_422(self, client):
        response = client.post("/api/upload")
        assert response.status_code == 422

    def test_upload_returns_token(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_upload_records_have_expected_fields(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        data = response.json()
        for r in data["records"]:
            assert "employeeName" in r
            assert "totalVencimentos" in r
            assert "sourceFile" in r

    def test_upload_records_have_source_file(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        data = response.json()
        for r in data["records"]:
            assert r["sourceFile"] == "sample.pdf"

    def test_upload_ignored_records_have_details(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        data = response.json()
        assert len(data["ignoredRecords"]) >= 1
        for ign in data["ignoredRecords"]:
            assert "page" in ign
            assert "reason" in ign
            assert "sourceFile" in ign

    def test_first_record_correct(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            response = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        data = response.json()
        assert len(data["records"]) > 0
        first = data["records"][0]
        assert "FULANO" in first["employeeName"].upper()

    def test_upload_multiple_files(self, client):
        with open(SAMPLE_PDF, "rb") as f1, open(SAMPLE_PDF, "rb") as f2:
            response = client.post("/api/upload", files=[
                ("files", ("file1.pdf", f1, "application/pdf")),
                ("files", ("file2.pdf", f2, "application/pdf")),
            ])
        assert response.status_code == 200
        data = response.json()
        assert data["totalPages"] == 204
        files_seen = {r["sourceFile"] for r in data["records"]}
        assert "file1.pdf" in files_seen
        assert "file2.pdf" in files_seen


class TestExportEndpoint:
    def test_export_csv_returns_file(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/csv?token={token}")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_xlsx_returns_file(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/xlsx?token={token}")
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]

    def test_export_csv_contains_source_file_column(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/csv?token={token}")
        content = response.content.decode("utf-8-sig")
        assert "Arquivo" in content

    def test_export_with_invalid_token_returns_404(self, client):
        response = client.get("/api/export/csv?token=invalidtoken")
        assert response.status_code == 404

    def test_export_without_token_returns_422(self, client):
        response = client.get("/api/export/csv")
        assert response.status_code == 422

    def test_export_pdf_returns_file(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/pdf?token={token}")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    def test_export_pdf_starts_with_pdf_header(self, client):
        with open(SAMPLE_PDF, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("sample.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/pdf?token={token}")
        assert response.content[:5] == b"%PDF-"

    def test_export_pdf_with_invalid_token_returns_404(self, client):
        response = client.get("/api/export/pdf?token=invalidtoken")
        assert response.status_code == 404
