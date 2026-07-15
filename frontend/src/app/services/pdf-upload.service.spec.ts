import { TestBed } from '@angular/core/testing'
import { provideHttpClient, withXhr } from '@angular/common/http'
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing'
import { PdfUploadService } from './pdf-upload.service'
import { ProcessResult } from '../models/report.models'

describe('PdfUploadService', () => {
  let service: PdfUploadService
  let httpMock: HttpTestingController

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [PdfUploadService, provideHttpClient(withXhr()), provideHttpClientTesting()],
    })
    service = TestBed.inject(PdfUploadService)
    httpMock = TestBed.inject(HttpTestingController)
  })

  afterEach(() => {
    httpMock.verify()
  })

  it('should be created', () => {
    expect(service).toBeTruthy()
  })

  it('should upload PDFs and return ProcessResult', () => {
    const mockResult: ProcessResult = {
      token: 'abc-123',
      records: [{ employeeName: 'João', totalVencimentos: 'R$ 5.000,00', sourceFile: 'file.pdf' }],
      ignoredRecords: [],
      totalPages: 1,
      totalRecords: 1,
      ignoredRecordsCount: 0,
      warnings: [],
    }

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })

    service.uploadPdfs([file]).subscribe((result) => {
      expect(result).toEqual(mockResult)
      expect(result.token).toBe('abc-123')
      expect(result.records.length).toBe(1)
    })

    const req = httpMock.expectOne('http://localhost:8000/api/upload')
    expect(req.request.method).toBe('POST')
    expect(req.request.body.has('files')).toBeTrue()
    req.flush(mockResult)
  })

  it('should send multiple files in FormData', () => {
    const file1 = new File(['a'], 'a.pdf', { type: 'application/pdf' })
    const file2 = new File(['b'], 'b.pdf', { type: 'application/pdf' })

    service.uploadPdfs([file1, file2]).subscribe()

    const req = httpMock.expectOne('http://localhost:8000/api/upload')
    const formData = req.request.body as FormData
    expect(formData.getAll('files').length).toBe(2)
    req.flush({ token: '', records: [], ignoredRecords: [], totalPages: 0, totalRecords: 0, ignoredRecordsCount: 0, warnings: [] })
  })

  it('should handle HTTP error with detail message', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })

    service.uploadPdfs([file]).subscribe({
      next: () => fail('expected an error'),
      error: (err: Error) => {
        expect(err.message).toBe('Arquivo vazio ou inválido.')
      },
    })

    const req = httpMock.expectOne('http://localhost:8000/api/upload')
    req.flush({ detail: 'Arquivo vazio ou inválido.' }, { status: 400, statusText: 'Bad Request' })
  })

  it('should handle HTTP error with default message', () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })

    service.uploadPdfs([file]).subscribe({
      next: () => fail('expected an error'),
      error: (err: Error) => {
        expect(err.message).toBe('Erro ao processar os arquivos.')
      },
    })

    const req = httpMock.expectOne('http://localhost:8000/api/upload')
    req.flush({}, { status: 500, statusText: 'Internal Server Error' })
  })
})
