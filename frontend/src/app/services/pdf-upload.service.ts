import { Injectable } from '@angular/core'
import { HttpClient, HttpErrorResponse } from '@angular/common/http'
import { Observable, throwError, catchError } from 'rxjs'
import { ProcessResult } from '../models/report.models'

@Injectable({ providedIn: 'root' })
export class PdfUploadService {
  private apiUrl = 'http://localhost:8000'

  constructor(private http: HttpClient) {}

  uploadPdfs(files: File[]): Observable<ProcessResult> {
    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }
    return this.http.post<ProcessResult>(`${this.apiUrl}/api/upload`, formData).pipe(
      catchError((err: HttpErrorResponse) => {
        const detail = err.error?.detail || 'Erro ao processar os arquivos.'
        return throwError(() => new Error(detail))
      }),
    )
  }
}
