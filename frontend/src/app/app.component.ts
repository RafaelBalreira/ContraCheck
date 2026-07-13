import { Component, signal } from '@angular/core'
import { CommonModule } from '@angular/common'
import { UploadAreaComponent } from './components/upload-area/upload-area.component'
import { ProgressIndicatorComponent } from './components/progress-indicator/progress-indicator.component'
import { ReportTableComponent } from './components/report-table/report-table.component'
import { ErrorDisplayComponent } from './components/error-display/error-display.component'
import { IgnoredRecordsPanelComponent } from './components/ignored-records-panel/ignored-records-panel.component'
import { PdfUploadService } from './services/pdf-upload.service'
import { ExportService } from './services/export.service'
import { PaySlip, IgnoredRecord } from './models/report.models'

type AppState = 'idle' | 'uploading' | 'processing' | 'complete' | 'error'

@Component({
  selector: 'app-root',
  imports: [
    CommonModule,
    UploadAreaComponent,
    ProgressIndicatorComponent,
    ReportTableComponent,
    ErrorDisplayComponent,
    IgnoredRecordsPanelComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  state = signal<AppState>('idle')
  records = signal<PaySlip[]>([])
  ignoredRecords = signal<IgnoredRecord[]>([])
  token = signal('')
  totalPages = signal(0)
  totalRecords = signal(0)
  ignoredRecordsCount = signal(0)
  errorMessage = signal('')
  showIgnoredPanel = signal(false)

  constructor(
    private uploadService: PdfUploadService,
    private exportService: ExportService,
  ) {}

  onFilesSelected(files: File[]) {
    const invalidFiles = files.filter(f => !f.name.toLowerCase().endsWith('.pdf'))
    if (invalidFiles.length > 0) {
      this.errorMessage.set(`Formato inválido: ${invalidFiles.map(f => f.name).join(', ')}. Selecione apenas arquivos PDF.`)
      this.state.set('error')
      return
    }

    this.state.set('uploading')
    this.errorMessage.set('')

    this.uploadService.uploadPdfs(files).subscribe({
      next: (result) => {
        this.records.set(result.records)
        this.ignoredRecords.set(result.ignoredRecords)
        this.token.set(result.token)
        this.totalPages.set(result.totalPages)
        this.totalRecords.set(result.totalRecords)
        this.ignoredRecordsCount.set(result.ignoredRecordsCount)
        this.state.set('complete')
      },
      error: (err) => {
        this.errorMessage.set(err.message || 'Erro ao processar os arquivos.')
        this.state.set('error')
      },
    })
  }

  onExportCsv() {
    this.exportService.downloadExport(this.token(), 'csv').subscribe({
      next: (blob) => this._downloadBlob(blob, 'relatorio.csv'),
      error: () => this.errorMessage.set('Erro ao exportar CSV.'),
    })
  }

  onExportXlsx() {
    this.exportService.downloadExport(this.token(), 'xlsx').subscribe({
      next: (blob) => this._downloadBlob(blob, 'relatorio.xlsx'),
      error: () => this.errorMessage.set('Erro ao exportar Excel.'),
    })
  }

  onExportPdf() {
    this.exportService.downloadExport(this.token(), 'pdf').subscribe({
      next: (blob) => this._downloadBlob(blob, 'relatorio.pdf'),
      error: () => this.errorMessage.set('Erro ao exportar PDF.'),
    })
  }

  onNewFile() {
    this.state.set('idle')
    this.records.set([])
    this.ignoredRecords.set([])
    this.token.set('')
    this.errorMessage.set('')
    this.totalPages.set(0)
    this.totalRecords.set(0)
    this.ignoredRecordsCount.set(0)
    this.showIgnoredPanel.set(false)
  }

  onDismissError() {
    this.state.set('idle')
    this.errorMessage.set('')
  }

  onToggleIgnored() {
    this.showIgnoredPanel.update(v => !v)
  }

  onCloseIgnored() {
    this.showIgnoredPanel.set(false)
  }

  private _downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    window.URL.revokeObjectURL(url)
  }
}
