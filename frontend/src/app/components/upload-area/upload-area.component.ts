import { Component, output, signal, ChangeDetectionStrategy } from '@angular/core'

import { MatIconModule } from '@angular/material/icon'
import { MatButtonModule } from '@angular/material/button'
import { MatChipsModule } from '@angular/material/chips'

@Component({
  selector: 'app-upload-area',
  imports: [MatIconModule, MatButtonModule, MatChipsModule],
  templateUrl: './upload-area.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrls: ['./upload-area.component.scss'],
})
export class UploadAreaComponent {
  processFiles = output<File[]>()
  files = signal<File[]>([])
  dragOver = false

  onDragOver(event: DragEvent) {
    event.preventDefault()
    this.dragOver = true
  }

  onDragLeave() {
    this.dragOver = false
  }

  onDrop(event: DragEvent) {
    event.preventDefault()
    this.dragOver = false
    const dropped = event.dataTransfer?.files
    if (dropped) {
      this.addFiles(dropped)
    }
  }

  onFileInput(event: Event) {
    const input = event.target as HTMLInputElement
    if (input.files) {
      this.addFiles(input.files)
    }
    input.value = ''
  }

  private addFiles(fileList: FileList) {
    const current = this.files()
    const existingNames = new Set(current.map(f => f.name))
    const newFiles: File[] = []
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i]
      if (!existingNames.has(file.name)) {
        newFiles.push(file)
      }
    }
    if (newFiles.length > 0) {
      this.files.set([...current, ...newFiles])
    }
  }

  removeFile(index: number) {
    const current = [...this.files()]
    current.splice(index, 1)
    this.files.set(current)
  }

  onProcess() {
    if (this.files().length > 0) {
      this.processFiles.emit(this.files())
    }
  }
}
