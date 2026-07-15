import io
import os
import sys
import time
import tempfile
import secrets
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from backend.application.pdf_service import PdfService
from backend.application.report_service import generate_csv, generate_xlsx, generate_pdf
from backend.domain.exceptions import InvalidPDFError, PasswordProtectedError, EmptyFileError


def _resolve_static_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    for candidate in [
        base / "frontend" / "dist" / "frontend" / "browser",
        base / "frontend" / "dist" / "browser",
    ]:
        if candidate.is_dir():
            return candidate
    return None


APP_VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(
    title="ContraCheck",
    version=APP_VERSION,
    description="ContraCheck - Relatório de Contracheques",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = _resolve_static_dir()

pdf_service = PdfService()

_sessions: dict[str, dict] = {}


def _generate_token() -> str:
    return secrets.token_hex(16)


def _safe_unlink(path: str) -> None:
    for _ in range(5):
        try:
            os.unlink(path)
            break
        except PermissionError:
            time.sleep(0.1)


ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@app.post("/api/upload")
async def upload_pdf(files: list[UploadFile] = File(...)):
    if not files:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    all_records = []
    all_ignored = []
    all_warnings = []
    total_pages = 0

    for file in files:
        if not file.filename:  # pragma: no cover
            continue

        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de arquivo inválido: {file.filename}. Selecione apenas arquivos PDF.",
            )

        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail=f"O arquivo está vazio: {file.filename}")
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande ({file.filename}). O tamanho máximo é 100 MB.",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            result = pdf_service.process_pdf(tmp_path, source_file=file.filename)
        except PasswordProtectedError:
            raise HTTPException(status_code=422, detail=f"O PDF está protegido por senha: {file.filename}")
        except (InvalidPDFError, EmptyFileError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            raise HTTPException(
                status_code=500,
                detail=f"Não foi possível ler o arquivo PDF: {file.filename}",
            )
        finally:
            _safe_unlink(tmp_path)

        all_records.extend(result.records)
        all_ignored.extend(result.ignored_details)
        all_warnings.extend(result.warnings)
        total_pages += result.total_pages

    token = _generate_token()
    _sessions[token] = {
        "records": all_records,
        "ignored_count": len(all_ignored),
    }

    return {
        "token": token,
        "records": [
            {
                "employeeName": r.employee_name,
                "totalVencimentos": r.total_vencimentos,
                "sourceFile": r.source_file,
            }
            for r in all_records
        ],
        "ignoredRecords": [
            {
                "page": ign.page,
                "reason": ign.reason,
                "sourceFile": ign.source_file,
            }
            for ign in all_ignored
        ],
        "totalPages": total_pages,
        "totalRecords": len(all_records),
        "ignoredRecordsCount": len(all_ignored),
        "warnings": all_warnings,
    }


@app.get("/api/export/csv")
async def export_csv(token: str = Query(...)):
    session = _sessions.get(token)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada.")

    records = session["records"]
    if not records:
        raise HTTPException(status_code=400, detail="Nenhum dado para exportar.")

    csv_bytes = generate_csv(records)

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": "attachment; filename=relatorio.csv",
        },
    )


@app.get("/api/export/xlsx")
async def export_xlsx(token: str = Query(...)):
    session = _sessions.get(token)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada.")

    records = session["records"]
    if not records:
        raise HTTPException(status_code=400, detail="Nenhum dado para exportar.")

    xlsx_bytes = generate_xlsx(records)

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=relatorio.xlsx",
        },
    )


@app.get("/api/export/pdf")
async def export_pdf(token: str = Query(...)):
    session = _sessions.get(token)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou expirada.")

    records = session["records"]
    if not records:
        raise HTTPException(status_code=400, detail="Nenhum dado para exportar.")

    ignored_count = session.get("ignored_count", 0)
    pdf_bytes = generate_pdf(records, ignored_count=ignored_count)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=relatorio.pdf",
        },
    )


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if _static_dir is None:
        raise HTTPException(status_code=404, detail="Não encontrado")
    file_path = _static_dir / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    index = _static_dir / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="Não encontrado")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    import threading
    import webbrowser

    PORT = 8000
    URL = f"http://localhost:{PORT}"

    def _open_browser():
        time.sleep(1.5)
        webbrowser.open(URL)

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=PORT)
