import { TestBed } from '@angular/core/testing'
import { provideHttpClient, withXhr } from '@angular/common/http'
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing'
import { AppComponent } from './app.component'
import { PdfUploadService } from './services/pdf-upload.service'
import { ExportService } from './services/export.service'
import { ProcessResult } from './models/report.models'
import { of, throwError } from 'rxjs'

describe('AppComponent', () => {
  let component: AppComponent
  let uploadService: jasmine.SpyObj<PdfUploadService>
  let exportService: jasmine.SpyObj<ExportService>

  const mockResult: ProcessResult = {
    token: 'test-token-abc',
    records: [{ employeeName: 'João', totalVencimentos: 'R$ 5.000,00', sourceFile: 'file.pdf' }],
    ignoredRecords: [{ page: 1, reason: 'CPF não encontrado', sourceFile: 'file.pdf' }],
    totalPages: 1,
    totalRecords: 1,
    ignoredRecordsCount: 1,
    warnings: [],
  }

  beforeEach(async () => {
    uploadService = jasmine.createSpyObj('PdfUploadService', ['uploadPdfs'])
    exportService = jasmine.createSpyObj('ExportService', ['downloadExport', 'getExportUrl'])

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideHttpClient(withXhr()),
        provideHttpClientTesting(),
        { provide: PdfUploadService, useValue: uploadService },
        { provide: ExportService, useValue: exportService },
      ],
    }).compileComponents()

    const fixture = TestBed.createComponent(AppComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create the app', () => {
    expect(component).toBeTruthy()
  })

  it('should start in idle state', () => {
    expect(component.state()).toBe('idle')
  })

  it('should have empty records initially', () => {
    expect(component.records().length).toBe(0)
  })

  it('should have empty ignored records initially', () => {
    expect(component.ignoredRecords().length).toBe(0)
  })

  describe('onFilesSelected', () => {
    it('should set error state for non-PDF files', () => {
      const files = [new File(['test'], 'doc.txt', { type: 'text/plain' })]
      component.onFilesSelected(files)
      expect(component.state()).toBe('error')
      expect(component.errorMessage()).toContain('Formato inválido')
      expect(component.errorMessage()).toContain('doc.txt')
    })

    it('should set error for mixed valid and invalid files', () => {
      const files = [
        new File(['a'], 'valid.pdf', { type: 'application/pdf' }),
        new File(['b'], 'invalid.txt', { type: 'text/plain' }),
      ]
      component.onFilesSelected(files)
      expect(component.state()).toBe('error')
      expect(component.errorMessage()).toContain('invalid.txt')
    })

    it('should call uploadService.uploadPdfs for valid PDF files', () => {
      uploadService.uploadPdfs.and.returnValue(of(mockResult))
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })]

      component.onFilesSelected(files)

      expect(uploadService.uploadPdfs).toHaveBeenCalledWith(files)
    })

    it('should set state to uploading while request is in progress', () => {
      uploadService.uploadPdfs.and.returnValue(of(mockResult))
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })]

      component.onFilesSelected(files)

      expect(component.state()).toBe('complete')
    })

    it('should populate signals on successful upload', () => {
      uploadService.uploadPdfs.and.returnValue(of(mockResult))
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })]

      component.onFilesSelected(files)

      expect(component.records()).toEqual(mockResult.records)
      expect(component.ignoredRecords()).toEqual(mockResult.ignoredRecords)
      expect(component.token()).toBe('test-token-abc')
      expect(component.totalPages()).toBe(1)
      expect(component.totalRecords()).toBe(1)
      expect(component.ignoredRecordsCount()).toBe(1)
      expect(component.state()).toBe('complete')
    })

    it('should set error state on upload failure', () => {
      uploadService.uploadPdfs.and.returnValue(throwError(() => new Error('Falha no servidor')))
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })]

      component.onFilesSelected(files)

      expect(component.state()).toBe('error')
      expect(component.errorMessage()).toBe('Falha no servidor')
    })

    it('should use default error message when error has no message', () => {
      uploadService.uploadPdfs.and.returnValue(throwError(() => ({})))
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })]

      component.onFilesSelected(files)

      expect(component.state()).toBe('error')
      expect(component.errorMessage()).toBe('Erro ao processar os arquivos.')
    })
  })

  describe('onExportCsv', () => {
    it('should call exportService.downloadExport with csv format and trigger download', () => {
      const blob = new Blob(['csv'], { type: 'text/csv' })
      exportService.downloadExport.and.returnValue(of(blob))
      const clickSpy = jasmine.createSpy('click')
      const mockAnchor = { href: '', download: '', click: clickSpy } as unknown as HTMLAnchorElement
      spyOn(document, 'createElement').and.returnValue(mockAnchor)
      spyOn(window.URL, 'createObjectURL').and.returnValue('blob:http://localhost/fake-url')
      spyOn(window.URL, 'revokeObjectURL')

      component.token.set('test-token')
      component.onExportCsv()

      expect(exportService.downloadExport).toHaveBeenCalledWith('test-token', 'csv')
      expect(window.URL.createObjectURL).toHaveBeenCalledWith(blob)
      expect(mockAnchor.download).toBe('relatorio.csv')
      expect(clickSpy).toHaveBeenCalled()
      expect(window.URL.revokeObjectURL).toHaveBeenCalledWith('blob:http://localhost/fake-url')
    })

    it('should set error on export failure', () => {
      exportService.downloadExport.and.returnValue(throwError(() => new Error('fail')))

      component.token.set('test-token')
      component.onExportCsv()

      expect(component.errorMessage()).toBe('Erro ao exportar CSV.')
    })
  })

  describe('onExportXlsx', () => {
    it('should call exportService.downloadExport with xlsx format and trigger download', () => {
      const blob = new Blob(['xlsx'], { type: 'application/xlsx' })
      exportService.downloadExport.and.returnValue(of(blob))
      const clickSpy = jasmine.createSpy('click')
      const mockAnchor = { href: '', download: '', click: clickSpy } as unknown as HTMLAnchorElement
      spyOn(document, 'createElement').and.returnValue(mockAnchor)
      spyOn(window.URL, 'createObjectURL').and.returnValue('blob:http://localhost/fake-url')
      spyOn(window.URL, 'revokeObjectURL')

      component.token.set('test-token')
      component.onExportXlsx()

      expect(exportService.downloadExport).toHaveBeenCalledWith('test-token', 'xlsx')
      expect(mockAnchor.download).toBe('relatorio.xlsx')
      expect(clickSpy).toHaveBeenCalled()
    })

    it('should set error on export failure', () => {
      exportService.downloadExport.and.returnValue(throwError(() => new Error('fail')))

      component.token.set('test-token')
      component.onExportXlsx()

      expect(component.errorMessage()).toBe('Erro ao exportar Excel.')
    })
  })

  describe('onExportPdf', () => {
    it('should call exportService.downloadExport with pdf format and trigger download', () => {
      const blob = new Blob(['pdf'], { type: 'application/pdf' })
      exportService.downloadExport.and.returnValue(of(blob))
      const clickSpy = jasmine.createSpy('click')
      const mockAnchor = { href: '', download: '', click: clickSpy } as unknown as HTMLAnchorElement
      spyOn(document, 'createElement').and.returnValue(mockAnchor)
      spyOn(window.URL, 'createObjectURL').and.returnValue('blob:http://localhost/fake-url')
      spyOn(window.URL, 'revokeObjectURL')

      component.token.set('test-token')
      component.onExportPdf()

      expect(exportService.downloadExport).toHaveBeenCalledWith('test-token', 'pdf')
      expect(mockAnchor.download).toBe('relatorio.pdf')
      expect(clickSpy).toHaveBeenCalled()
    })

    it('should set error on export failure', () => {
      exportService.downloadExport.and.returnValue(throwError(() => new Error('fail')))

      component.token.set('test-token')
      component.onExportPdf()

      expect(component.errorMessage()).toBe('Erro ao exportar PDF.')
    })
  })

  describe('onNewFile', () => {
    it('should reset all signals to initial state', () => {
      component.state.set('complete')
      component.records.set(mockResult.records)
      component.ignoredRecords.set(mockResult.ignoredRecords)
      component.token.set('abc')
      component.errorMessage.set('error')
      component.totalPages.set(5)
      component.totalRecords.set(10)
      component.ignoredRecordsCount.set(2)
      component.showIgnoredPanel.set(true)

      component.onNewFile()

      expect(component.state()).toBe('idle')
      expect(component.records().length).toBe(0)
      expect(component.ignoredRecords().length).toBe(0)
      expect(component.token()).toBe('')
      expect(component.errorMessage()).toBe('')
      expect(component.totalPages()).toBe(0)
      expect(component.totalRecords()).toBe(0)
      expect(component.ignoredRecordsCount()).toBe(0)
      expect(component.showIgnoredPanel()).toBeFalse()
    })
  })

  describe('onDismissError', () => {
    it('should reset state to idle and clear error message', () => {
      component.state.set('error')
      component.errorMessage.set('Algum erro')

      component.onDismissError()

      expect(component.state()).toBe('idle')
      expect(component.errorMessage()).toBe('')
    })
  })

  describe('onToggleIgnored', () => {
    it('should toggle showIgnoredPanel', () => {
      expect(component.showIgnoredPanel()).toBeFalse()
      component.onToggleIgnored()
      expect(component.showIgnoredPanel()).toBeTrue()
      component.onToggleIgnored()
      expect(component.showIgnoredPanel()).toBeFalse()
    })
  })

  describe('onCloseIgnored', () => {
    it('should set showIgnoredPanel to false', () => {
      component.showIgnoredPanel.set(true)
      component.onCloseIgnored()
      expect(component.showIgnoredPanel()).toBeFalse()
    })
  })
})
