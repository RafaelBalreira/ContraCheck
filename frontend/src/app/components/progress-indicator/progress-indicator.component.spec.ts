import { ComponentFixture, TestBed } from '@angular/core/testing'
import { ProgressIndicatorComponent } from './progress-indicator.component'

describe('ProgressIndicatorComponent', () => {
  let component: ProgressIndicatorComponent
  let fixture: ComponentFixture<ProgressIndicatorComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProgressIndicatorComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(ProgressIndicatorComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })

  it('should show spinner when processing is true', () => {
    fixture.componentRef.setInput('processing', true)
    fixture.detectChanges()
    const spinner = fixture.nativeElement.querySelector('mat-spinner')
    expect(spinner).not.toBeNull()
  })

  it('should not show spinner when processing is false', () => {
    fixture.componentRef.setInput('processing', false)
    fixture.detectChanges()
    const spinner = fixture.nativeElement.querySelector('mat-spinner')
    expect(spinner).toBeNull()
  })

  it('should show summary when not processing and totalRecords > 0', () => {
    fixture.componentRef.setInput('processing', false)
    fixture.componentRef.setInput('totalRecords', 5)
    fixture.componentRef.setInput('totalPages', 2)
    fixture.componentRef.setInput('ignoredRecords', 1)
    fixture.detectChanges()

    const summary = fixture.nativeElement.querySelector('.summary')
    expect(summary).not.toBeNull()
  })

  it('should not show summary when processing', () => {
    fixture.componentRef.setInput('processing', true)
    fixture.componentRef.setInput('totalRecords', 5)
    fixture.detectChanges()

    const summary = fixture.nativeElement.querySelector('.summary')
    expect(summary).toBeNull()
  })

  it('should not show summary when totalRecords is 0', () => {
    fixture.componentRef.setInput('processing', false)
    fixture.componentRef.setInput('totalRecords', 0)
    fixture.detectChanges()

    const summary = fixture.nativeElement.querySelector('.summary')
    expect(summary).toBeNull()
  })

  it('should display correct values in summary', () => {
    fixture.componentRef.setInput('processing', false)
    fixture.componentRef.setInput('totalRecords', 10)
    fixture.componentRef.setInput('totalPages', 3)
    fixture.componentRef.setInput('ignoredRecords', 2)
    fixture.detectChanges()

    const values = fixture.nativeElement.querySelectorAll('.summary-value')
    expect(values[0].textContent.trim()).toBe('3')
    expect(values[1].textContent.trim()).toBe('10')
    expect(values[2].textContent.trim()).toBe('2')
  })
})
