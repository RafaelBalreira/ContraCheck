import { ComponentFixture, TestBed } from '@angular/core/testing'
import { UploadAreaComponent } from './upload-area.component'

describe('UploadAreaComponent', () => {
  let component: UploadAreaComponent
  let fixture: ComponentFixture<UploadAreaComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UploadAreaComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(UploadAreaComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })

  it('should start with empty files', () => {
    expect(component.files().length).toBe(0)
  })

  it('should start with dragOver false', () => {
    expect(component.dragOver).toBeFalse()
  })

  describe('drag and drop', () => {
    it('should set dragOver to true on dragover', () => {
      const event = new DragEvent('dragover', { bubbles: true })
      spyOn(event, 'preventDefault')
      component.onDragOver(event)
      expect(event.preventDefault).toHaveBeenCalled()
      expect(component.dragOver).toBeTrue()
    })

    it('should set dragOver to false on dragleave', () => {
      component.dragOver = true
      component.onDragLeave()
      expect(component.dragOver).toBeFalse()
    })

    it('should add dropped files', () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)

      const event = new DragEvent('drop', { bubbles: true, dataTransfer })
      spyOn(event, 'preventDefault')
      component.onDrop(event)

      expect(event.preventDefault).toHaveBeenCalled()
      expect(component.files().length).toBe(1)
      expect(component.files()[0].name).toBe('test.pdf')
    })
  })

  describe('file input', () => {
    it('should add files from input', () => {
      const file = new File(['test'], 'doc.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)

      const input = document.createElement('input')
      input.type = 'file'
      input.files = dataTransfer.files

      const event = { target: input } as unknown as Event
      component.onFileInput(event)

      expect(component.files().length).toBe(1)
    })

    it('should reset input value after selection', () => {
      const file = new File(['test'], 'doc.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)

      const input = document.createElement('input')
      input.type = 'file'
      input.files = dataTransfer.files

      const event = { target: input } as unknown as Event
      component.onFileInput(event)

      expect(input.value).toBe('')
    })
  })

  describe('deduplication', () => {
    it('should not add duplicate files by name', () => {
      const file1 = new File(['a'], 'same.pdf', { type: 'application/pdf' })
      const file2 = new File(['b'], 'same.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file1)

      const input = document.createElement('input')
      input.type = 'file'
      input.files = dataTransfer.files

      component.onFileInput({ target: input } as unknown as Event)
      expect(component.files().length).toBe(1)

      const dataTransfer2 = new DataTransfer()
      dataTransfer2.items.add(file2)
      const input2 = document.createElement('input')
      input2.type = 'file'
      input2.files = dataTransfer2.files

      component.onFileInput({ target: input2 } as unknown as Event)
      expect(component.files().length).toBe(1)
    })
  })

  describe('removeFile', () => {
    it('should remove file at given index', () => {
      const file1 = new File(['a'], 'a.pdf', { type: 'application/pdf' })
      const file2 = new File(['b'], 'b.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file1)
      dataTransfer.items.add(file2)

      const input = document.createElement('input')
      input.type = 'file'
      input.files = dataTransfer.files

      component.onFileInput({ target: input } as unknown as Event)
      expect(component.files().length).toBe(2)

      component.removeFile(0)
      expect(component.files().length).toBe(1)
      expect(component.files()[0].name).toBe('b.pdf')
    })
  })

  describe('onProcess', () => {
    it('should emit processFiles when files exist', () => {
      spyOn(component.processFiles, 'emit')
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      const dataTransfer = new DataTransfer()
      dataTransfer.items.add(file)

      const input = document.createElement('input')
      input.type = 'file'
      input.files = dataTransfer.files

      component.onFileInput({ target: input } as unknown as Event)
      component.onProcess()

      expect(component.processFiles.emit).toHaveBeenCalledWith(component.files())
    })

    it('should not emit processFiles when no files', () => {
      spyOn(component.processFiles, 'emit')
      component.onProcess()
      expect(component.processFiles.emit).not.toHaveBeenCalled()
    })
  })
})
