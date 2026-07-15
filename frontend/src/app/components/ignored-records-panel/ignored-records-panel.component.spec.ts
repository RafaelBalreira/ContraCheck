import { ComponentFixture, TestBed } from '@angular/core/testing'
import { IgnoredRecordsPanelComponent } from './ignored-records-panel.component'
import { IgnoredRecord } from '../../models/report.models'

describe('IgnoredRecordsPanelComponent', () => {
  let component: IgnoredRecordsPanelComponent
  let fixture: ComponentFixture<IgnoredRecordsPanelComponent>

  const mockRecords: IgnoredRecord[] = Array.from({ length: 25 }, (_, i) => ({
    page: i + 1,
    reason: `Motivo ${i + 1}`,
    sourceFile: `file_${i + 1}.pdf`,
  }))

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IgnoredRecordsPanelComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(IgnoredRecordsPanelComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })

  it('should show empty state when no records', () => {
    fixture.componentRef.setInput('ignoredRecords', [])
    fixture.detectChanges()
    const empty = fixture.nativeElement.querySelector('.empty-state')
    expect(empty).not.toBeNull()
  })

  it('should show table when records exist', () => {
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()
    const table = fixture.nativeElement.querySelector('table')
    expect(table).not.toBeNull()
  })

  it('should paginate records with default page size of 10', () => {
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()
    expect(component.paginatedRecords().length).toBe(10)
  })

  it('should show first page records', () => {
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()
    const paginated = component.paginatedRecords()
    expect(paginated[0].page).toBe(1)
    expect(paginated[9].page).toBe(10)
  })

  it('should update page on onPageChange', () => {
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()

    component.onPageChange({ pageIndex: 1, pageSize: 10, length: 25 })
    fixture.detectChanges()

    expect(component.pageIndex()).toBe(1)
    expect(component.paginatedRecords()[0].page).toBe(11)
  })

  it('should update page size', () => {
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()

    component.onPageChange({ pageIndex: 0, pageSize: 25, length: 25 })
    fixture.detectChanges()

    expect(component.pageSize()).toBe(25)
    expect(component.paginatedRecords().length).toBe(25)
  })

  it('should emit close when close button is clicked', () => {
    spyOn(component.close, 'emit')
    fixture.componentRef.setInput('ignoredRecords', mockRecords)
    fixture.detectChanges()

    const btn = fixture.nativeElement.querySelector('.panel-header button')
    btn.click()

    expect(component.close.emit).toHaveBeenCalled()
  })
})
