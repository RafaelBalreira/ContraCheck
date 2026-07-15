import { ComponentFixture, TestBed } from '@angular/core/testing'
import { ErrorDisplayComponent } from './error-display.component'

describe('ErrorDisplayComponent', () => {
  let component: ErrorDisplayComponent
  let fixture: ComponentFixture<ErrorDisplayComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ErrorDisplayComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(ErrorDisplayComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })

  it('should not render error container when message is empty', () => {
    fixture.detectChanges()
    const container = fixture.nativeElement.querySelector('.error-container')
    expect(container).toBeNull()
  })

  it('should render error container when message is provided', () => {
    fixture.componentRef.setInput('message', 'Erro ao processar')
    fixture.detectChanges()
    const container = fixture.nativeElement.querySelector('.error-container')
    expect(container).not.toBeNull()
  })

  it('should display the error message text', () => {
    fixture.componentRef.setInput('message', 'Formato inválido')
    fixture.detectChanges()
    const text = fixture.nativeElement.querySelector('.error-message')
    expect(text.textContent.trim()).toBe('Formato inválido')
  })

  it('should emit dismiss when close button is clicked', () => {
    spyOn(component.dismiss, 'emit')
    fixture.componentRef.setInput('message', 'Erro')
    fixture.detectChanges()

    const btn = fixture.nativeElement.querySelector('.dismiss-btn')
    btn.click()

    expect(component.dismiss.emit).toHaveBeenCalled()
  })
})
