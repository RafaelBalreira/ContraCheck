import { Injectable } from '@angular/core'
import { HttpClient } from '@angular/common/http'
import { Observable } from 'rxjs'

@Injectable({ providedIn: 'root' })
export class ExportService {
  private apiUrl = 'http://localhost:8000'

  constructor(private http: HttpClient) {}

  getExportUrl(token: string, format: 'csv' | 'xlsx' | 'pdf'): string {
    return `${this.apiUrl}/api/export/${format}?token=${token}`
  }

  downloadExport(token: string, format: 'csv' | 'xlsx' | 'pdf'): Observable<Blob> {
    const url = this.getExportUrl(token, format)
    return this.http.get(url, { responseType: 'blob' })
  }
}
