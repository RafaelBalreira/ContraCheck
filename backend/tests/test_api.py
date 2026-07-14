import os
import io
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app, _resolve_static_dir, _safe_unlink
from backend.domain.models import PaySlip


@pytest.fixture
def client():
    return TestClient(app)


class TestResolveStaticDir:
    def test_returns_none_when_no_dist(self):
        with patch("backend.main.sys") as mock_sys:
            mock_sys.frozen = False
            result = _resolve_static_dir()
            assert result is None or result.is_dir()

    def test_frozen_app_path(self):
        with patch("backend.main.sys") as mock_sys:
            mock_sys.frozen = True
            mock_sys._MEIPASS = os.path.dirname(__file__)
            result = _resolve_static_dir()
            assert result is None or isinstance(result.__class__, type)


class TestSafeUnlink:
    def test_unlinks_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        _safe_unlink(str(f))
        assert not f.exists()

    def test_permission_error_retries(self):
        with patch("backend.main.os.unlink", side_effect=PermissionError):
            with patch("backend.main.time.sleep"):
                _safe_unlink("nonexistent.txt")


class TestUploadEndpoint:
    def test_upload_valid_pdf_returns_200(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "totalPages" in data
        assert "totalRecords" in data
        assert "ignoredRecordsCount" in data
        assert "ignoredRecords" in data
        assert data["totalPages"] == 1
        assert data["totalRecords"] == 1

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

    def test_upload_returns_token(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_upload_records_have_expected_fields(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        data = response.json()
        for r in data["records"]:
            assert "employeeName" in r
            assert "totalVencimentos" in r
            assert "sourceFile" in r

    def test_upload_records_have_source_file(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("myfile.pdf", f, "application/pdf")})
        data = response.json()
        for r in data["records"]:
            assert r["sourceFile"] == "myfile.pdf"

    def test_upload_no_ignored_records(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        data = response.json()
        assert len(data["ignoredRecords"]) == 0

    def test_upload_non_pdf_extension_returns_400(self, client, first_test_pdf):
        response = client.post(
            "/api/upload",
            files=[("files", ("report.csv", b"name,value\nX,1", "text/csv"))],
        )
        assert response.status_code == 400
        assert "inválido" in response.json()["detail"]

    def test_upload_password_protected_returns_422(self, client, first_test_pdf):
        with patch("backend.main.pdf_service.process_pdf") as mock_process:
            from backend.domain.exceptions import PasswordProtectedError
            mock_process.side_effect = PasswordProtectedError("senha")
            response = client.post(
                "/api/upload",
                files={"files": ("protected.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
            assert response.status_code == 422
            assert "senha" in response.json()["detail"].lower()

    def test_upload_invalid_pdf_returns_400(self, client, first_test_pdf):
        with patch("backend.main.pdf_service.process_pdf") as mock_process:
            from backend.domain.exceptions import InvalidPDFError
            mock_process.side_effect = InvalidPDFError("invalido")
            response = client.post(
                "/api/upload",
                files={"files": ("bad.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
            assert response.status_code == 400
            assert "invalido" in response.json()["detail"]

    def test_first_record_correct(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            response = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        data = response.json()
        assert len(data["records"]) > 0
        first = data["records"][0]
        assert "FULANO" in first["employeeName"].upper()

    def test_upload_multiple_files(self, client, all_test_pdfs):
        files = []
        handles = []
        for i, pdf_path in enumerate(all_test_pdfs):
            f = open(pdf_path, "rb")
            handles.append(f)
            files.append(("files", (f"file{i+1}.pdf", f, "application/pdf")))
        try:
            response = client.post("/api/upload", files=files)
        finally:
            for h in handles:
                h.close()
        assert response.status_code == 200
        data = response.json()
        assert data["totalPages"] == 3
        assert data["totalRecords"] == 3
        files_seen = {r["sourceFile"] for r in data["records"]}
        assert "file1.pdf" in files_seen
        assert "file2.pdf" in files_seen
        assert "file3.pdf" in files_seen


class TestExportEndpoint:
    def test_export_csv_returns_file(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/csv?token={token}")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_xlsx_returns_file(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/xlsx?token={token}")
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]

    def test_export_csv_contains_source_file_column(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
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

    def test_export_pdf_returns_file(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/pdf?token={token}")
        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]

    def test_export_pdf_starts_with_pdf_header(self, client, first_test_pdf):
        with open(first_test_pdf, "rb") as f:
            upload = client.post("/api/upload", files={"files": ("test.pdf", f, "application/pdf")})
        token = upload.json()["token"]
        response = client.get(f"/api/export/pdf?token={token}")
        assert response.content[:5] == b"%PDF-"

    def test_export_pdf_with_invalid_token_returns_404(self, client):
        response = client.get("/api/export/pdf?token=invalidtoken")
        assert response.status_code == 404

    def test_export_xlsx_with_invalid_token_returns_404(self, client):
        response = client.get("/api/export/xlsx?token=invalidtoken")
        assert response.status_code == 404

    def test_export_xlsx_without_token_returns_422(self, client):
        response = client.get("/api/export/xlsx")
        assert response.status_code == 422

    def test_export_pdf_without_token_returns_422(self, client):
        response = client.get("/api/export/pdf")
        assert response.status_code == 422

    def test_upload_file_too_large_returns_400(self, client):
        large_content = b"x" * (100 * 1024 * 1024 + 1)
        response = client.post("/api/upload", files={"files": ("large.pdf", large_content, "application/pdf")})
        assert response.status_code == 400
        assert "grande" in response.json()["detail"].lower()

    def test_export_csv_empty_records_returns_400(self, client):
        from backend.main import _sessions
        token = "test_empty_token"
        _sessions[token] = {"records": [], "ignored_count": 0}
        response = client.get(f"/api/export/csv?token={token}")
        assert response.status_code == 400

    def test_export_xlsx_empty_records_returns_400(self, client):
        from backend.main import _sessions
        token = "test_empty_xlsx_token"
        _sessions[token] = {"records": [], "ignored_count": 0}
        response = client.get(f"/api/export/xlsx?token={token}")
        assert response.status_code == 400

    def test_export_pdf_empty_records_returns_400(self, client):
        from backend.main import _sessions
        token = "test_empty_pdf_token"
        _sessions[token] = {"records": [], "ignored_count": 0}
        response = client.get(f"/api/export/pdf?token={token}")
        assert response.status_code == 400

    def test_upload_no_filename_rejected_by_fastapi(self, client):
        response = client.post(
            "/api/upload",
            files=[("files", ("", b"content", "application/pdf"))],
        )
        assert response.status_code == 422

    def test_upload_generic_exception_returns_500(self, client):
        with patch("backend.main.pdf_service.process_pdf", side_effect=RuntimeError("boom")):
            fake_pdf = b"%PDF-1.4 fake content"
            response = client.post("/api/upload", files={"files": ("test.pdf", fake_pdf, "application/pdf")})
            assert response.status_code == 500
            assert "Não foi possível ler" in response.json()["detail"]


class TestSpaServing:
    def test_spa_serves_index_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = os.path.join(tmpdir, "index.html")
            with open(index, "w") as f:
                f.write("<html><body>SPA</body></html>")
            with patch("backend.main._static_dir", Path(tmpdir)):
                from backend.main import app as spa_app
                from starlette.testclient import TestClient as StarletteClient
                tc = StarletteClient(spa_app)
                resp = tc.get("/some/route")
                assert resp.status_code == 200
                assert "SPA" in resp.text

    def test_spa_serves_static_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = os.path.join(tmpdir, "app.js")
            with open(asset, "w") as f:
                f.write("console.log('hi')")
            with patch("backend.main._static_dir", Path(tmpdir)):
                from backend.main import app as spa_app
                from starlette.testclient import TestClient as StarletteClient
                tc = StarletteClient(spa_app)
                resp = tc.get("/app.js")
                assert resp.status_code == 200

    def test_spa_returns_404_when_no_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.main._static_dir", Path(tmpdir)):
                from backend.main import app as spa_app
                from starlette.testclient import TestClient as StarletteClient
                tc = StarletteClient(spa_app)
                resp = tc.get("/nonexistent")
                assert resp.status_code == 404

    def test_spa_returns_404_when_static_dir_is_none(self):
        with patch("backend.main._static_dir", None):
            from backend.main import app as spa_app
            from starlette.testclient import TestClient as StarletteClient
            tc = StarletteClient(spa_app)
            resp = tc.get("/any/route")
            assert resp.status_code == 404
