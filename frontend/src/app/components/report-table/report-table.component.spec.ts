import { ComponentFixture, TestBed } from '@angular/core/testing'
import { ReportTableComponent } from './report-table.component'
import { PaySlip, IgnoredRecord } from '../../models/report.models'

describe('ReportTableComponent', () => {
  let component: ReportTableComponent
  let fixture: ComponentFixture<ReportTableComponent>

  const mockRecords: PaySlip[] = [
    { employeeName: 'Carlos Silva', totalVencimentos: 'R$ 5.000,00', sourceFile: 'a.pdf' },
    { employeeName: 'Ana Souza', totalVencimentos: 'R$ 3.500,50', sourceFile: 'b.pdf' },
    { employeeName: 'Bruno Costa', totalVencimentos: 'R$ 7.200,00', sourceFile: 'a.pdf' },
    { employeeName: 'Diana Lima', totalVencimentos: 'R$ 1.234,56', sourceFile: 'c.pdf' },
    { employeeName: 'Eduardo Alves', totalVencimentos: 'R$ 9.800,00', sourceFile: 'b.pdf' },
  ]

  const mockIgnored: IgnoredRecord[] = [
    { page: 1, reason: 'CPF não encontrado', sourceFile: 'a.pdf' },
  ]

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportTableComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(ReportTableComponent)
    component = fixture.componentInstance
    fixture.componentRef.setInput('records', mockRecords)
    fixture.componentRef.setInput('ignoredRecords', mockIgnored)
    fixture.componentRef.setInput('token', 'test-token')
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })

  describe('filteredRecords', () => {
    it('should return all records when search is empty', () => {
      expect(component.filteredRecords().length).toBe(5)
    })

    it('should filter by employee name case-insensitive', () => {
      component.onSearch('ana')
      fixture.detectChanges()
      expect(component.filteredRecords().length).toBe(2)
      const names = component.filteredRecords().map(r => r.employeeName)
      expect(names).toContain('Ana Souza')
      expect(names).toContain('Diana Lima')
    })

    it('should filter by partial name', () => {
      component.onSearch('sil')
      fixture.detectChanges()
      expect(component.filteredRecords().length).toBe(1)
      expect(component.filteredRecords()[0].employeeName).toBe('Carlos Silva')
    })

    it('should return empty when no match', () => {
      component.onSearch('xyz')
      fixture.detectChanges()
      expect(component.filteredRecords().length).toBe(0)
    })
  })

  describe('sortedRecords', () => {
    it('should return unsorted records when no sort is active', () => {
      const names = component.sortedRecords().map(r => r.employeeName)
      expect(names).toEqual(['Carlos Silva', 'Ana Souza', 'Bruno Costa', 'Diana Lima', 'Eduardo Alves'])
    })

    it('should sort by employeeName ascending', () => {
      component.onSortChange({ active: 'employeeName', direction: 'asc' })
      const names = component.sortedRecords().map(r => r.employeeName)
      expect(names).toEqual(['Ana Souza', 'Bruno Costa', 'Carlos Silva', 'Diana Lima', 'Eduardo Alves'])
    })

    it('should sort by employeeName descending', () => {
      component.onSortChange({ active: 'employeeName', direction: 'desc' })
      const names = component.sortedRecords().map(r => r.employeeName)
      expect(names).toEqual(['Eduardo Alves', 'Diana Lima', 'Carlos Silva', 'Bruno Costa', 'Ana Souza'])
    })

    it('should sort by totalVencimentos ascending (parsed values)', () => {
      component.onSortChange({ active: 'totalVencimentos', direction: 'asc' })
      const values = component.sortedRecords().map(r => r.totalVencimentos)
      expect(values[0]).toBe('R$ 1.234,56')
      expect(values[values.length - 1]).toBe('R$ 9.800,00')
    })

    it('should sort by totalVencimentos descending', () => {
      component.onSortChange({ active: 'totalVencimentos', direction: 'desc' })
      const values = component.sortedRecords().map(r => r.totalVencimentos)
      expect(values[0]).toBe('R$ 9.800,00')
      expect(values[values.length - 1]).toBe('R$ 1.234,56')
    })

    it('should sort by sourceFile ascending', () => {
      component.onSortChange({ active: 'sourceFile', direction: 'asc' })
      const sources = component.sortedRecords().map(r => r.sourceFile)
      expect(sources).toEqual(['a.pdf', 'a.pdf', 'b.pdf', 'b.pdf', 'c.pdf'])
    })

    it('should sort by sourceFile descending', () => {
      component.onSortChange({ active: 'sourceFile', direction: 'desc' })
      const sources = component.sortedRecords().map(r => r.sourceFile)
      expect(sources).toEqual(['c.pdf', 'b.pdf', 'b.pdf', 'a.pdf', 'a.pdf'])
    })

    it('should keep equal employeeNames in relative order', () => {
      fixture.componentRef.setInput('records', [
        { employeeName: 'Xpto', totalVencimentos: '1.000,00', sourceFile: 'a.pdf' },
        { employeeName: 'Xpto', totalVencimentos: '2.000,00', sourceFile: 'b.pdf' },
      ])
      component.onSortChange({ active: 'employeeName', direction: 'asc' })
      expect(component.sortedRecords()[0].totalVencimentos).toBe('1.000,00')
      expect(component.sortedRecords()[1].totalVencimentos).toBe('2.000,00')
    })

    it('should keep equal sourceFiles in relative order', () => {
      fixture.componentRef.setInput('records', [
        { employeeName: 'Ana', totalVencimentos: '1.000,00', sourceFile: 'same.pdf' },
        { employeeName: 'Bruno', totalVencimentos: '2.000,00', sourceFile: 'same.pdf' },
      ])
      component.onSortChange({ active: 'sourceFile', direction: 'asc' })
      expect(component.sortedRecords()[0].employeeName).toBe('Ana')
      expect(component.sortedRecords()[1].employeeName).toBe('Bruno')
    })

    it('should return 0 for non-numeric value in _parseValue', () => {
      fixture.componentRef.setInput('records', [
        { employeeName: 'Test', totalVencimentos: 'N/A', sourceFile: 'x.pdf' },
        { employeeName: 'Other', totalVencimentos: 'R$ 2.000,00', sourceFile: 'y.pdf' },
      ])
      component.onSortChange({ active: 'totalVencimentos', direction: 'asc' })
      const values = component.sortedRecords().map(r => r.totalVencimentos)
      expect(values[0]).toBe('N/A')
      expect(values[1]).toBe('R$ 2.000,00')
    })

    it('should return 0 comparison for unknown sort column', () => {
      component.onSortChange({ active: 'unknownColumn', direction: 'asc' })
      const names = component.sortedRecords().map(r => r.employeeName)
      expect(names).toEqual(['Carlos Silva', 'Ana Souza', 'Bruno Costa', 'Diana Lima', 'Eduardo Alves'])
    })
  })

  describe('paginatedRecords', () => {
    it('should paginate with default page size 10', () => {
      expect(component.paginatedRecords().length).toBe(5)
    })

    it('should paginate correctly with smaller page size', () => {
      component.onPageChange({ pageIndex: 0, pageSize: 2, length: 5 })
      expect(component.paginatedRecords().length).toBe(2)

      component.onPageChange({ pageIndex: 1, pageSize: 2, length: 5 })
      expect(component.paginatedRecords().length).toBe(2)
    })

    it('should return empty for out-of-bounds page', () => {
      component.onPageChange({ pageIndex: 10, pageSize: 10, length: 5 })
      expect(component.paginatedRecords().length).toBe(0)
    })
  })

  describe('totalFiltered', () => {
    it('should reflect total sorted records count', () => {
      expect(component.totalFiltered()).toBe(5)
    })

    it('should update after search', () => {
      component.onSearch('ana')
      expect(component.totalFiltered()).toBe(2)
    })
  })

  describe('onSearch', () => {
    it('should reset page to 0', () => {
      component.onPageChange({ pageIndex: 2, pageSize: 10, length: 5 })
      component.onSearch('ana')
      expect(component.pageIndex()).toBe(0)
    })
  })

  describe('output emissions', () => {
    it('should emit exportCsv', () => {
      spyOn(component.exportCsv, 'emit')
      component.onSearch('test')
      component.exportCsv.emit()
      expect(component.exportCsv.emit).toHaveBeenCalled()
    })

    it('should emit exportXlsx', () => {
      spyOn(component.exportXlsx, 'emit')
      component.exportXlsx.emit()
      expect(component.exportXlsx.emit).toHaveBeenCalled()
    })

    it('should emit exportPdf', () => {
      spyOn(component.exportPdf, 'emit')
      component.exportPdf.emit()
      expect(component.exportPdf.emit).toHaveBeenCalled()
    })

    it('should emit newFile', () => {
      spyOn(component.newFile, 'emit')
      component.newFile.emit()
      expect(component.newFile.emit).toHaveBeenCalled()
    })

    it('should emit showIgnored', () => {
      spyOn(component.showIgnored, 'emit')
      component.showIgnored.emit()
      expect(component.showIgnored.emit).toHaveBeenCalled()
    })
  })

  describe('displayedColumns', () => {
    it('should have correct columns', () => {
      expect(component.displayedColumns).toEqual(['employeeName', 'totalVencimentos', 'sourceFile'])
    })
  })
})
