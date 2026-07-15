import { TestBed } from '@angular/core/testing'
import { provideHttpClient, withXhr } from '@angular/common/http'
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing'
import { ExportService } from './export.service'

describe('ExportService', () => {
  let service: ExportService
  let httpMock: HttpTestingController

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ExportService, provideHttpClient(withXhr()), provideHttpClientTesting()],
    })
    service = TestBed.inject(ExportService)
    httpMock = TestBed.inject(HttpTestingController)
  })

  afterEach(() => {
    httpMock.verify()
  })

  it('should be created', () => {
    expect(service).toBeTruthy()
  })

  describe('getExportUrl', () => {
    it('should return correct CSV URL', () => {
      const url = service.getExportUrl('token-abc', 'csv')
      expect(url).toBe('http://localhost:8000/api/export/csv?token=token-abc')
    })

    it('should return correct XLSX URL', () => {
      const url = service.getExportUrl('token-xyz', 'xlsx')
      expect(url).toBe('http://localhost:8000/api/export/xlsx?token=token-xyz')
    })

    it('should return correct PDF URL', () => {
      const url = service.getExportUrl('token-123', 'pdf')
      expect(url).toBe('http://localhost:8000/api/export/pdf?token=token-123')
    })
  })

  describe('downloadExport', () => {
    it('should download blob for CSV format', () => {
      const mockBlob = new Blob(['csv-content'], { type: 'text/csv' })

      service.downloadExport('token-abc', 'csv').subscribe((blob) => {
        expect(blob).toEqual(mockBlob)
      })

      const req = httpMock.expectOne('http://localhost:8000/api/export/csv?token=token-abc')
      expect(req.request.method).toBe('GET')
      expect(req.request.responseType).toBe('blob')
      req.flush(mockBlob)
    })

    it('should download blob for XLSX format', () => {
      const mockBlob = new Blob(['xlsx-content'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })

      service.downloadExport('token-abc', 'xlsx').subscribe((blob) => {
        expect(blob).toEqual(mockBlob)
      })

      const req = httpMock.expectOne('http://localhost:8000/api/export/xlsx?token=token-abc')
      expect(req.request.method).toBe('GET')
      expect(req.request.responseType).toBe('blob')
      req.flush(mockBlob)
    })

    it('should download blob for PDF format', () => {
      const mockBlob = new Blob(['pdf-content'], { type: 'application/pdf' })

      service.downloadExport('token-abc', 'pdf').subscribe((blob) => {
        expect(blob).toEqual(mockBlob)
      })

      const req = httpMock.expectOne('http://localhost:8000/api/export/pdf?token=token-abc')
      expect(req.request.method).toBe('GET')
      expect(req.request.responseType).toBe('blob')
      req.flush(mockBlob)
    })
  })
})
