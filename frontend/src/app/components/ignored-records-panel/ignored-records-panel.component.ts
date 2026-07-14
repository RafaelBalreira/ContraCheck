import { Component, input, output, signal, computed, ChangeDetectionStrategy } from '@angular/core'

import { MatTableModule } from '@angular/material/table'
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator'
import { MatButtonModule } from '@angular/material/button'
import { MatIconModule } from '@angular/material/icon'
import { IgnoredRecord } from '../../models/report.models'

@Component({
  selector: 'app-ignored-records-panel',
  imports: [MatTableModule, MatPaginatorModule, MatButtonModule, MatIconModule],
  templateUrl: './ignored-records-panel.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrls: ['./ignored-records-panel.component.scss'],
})
export class IgnoredRecordsPanelComponent {
  ignoredRecords = input<IgnoredRecord[]>([])
  close = output<void>()

  pageSize = signal(10)
  pageIndex = signal(0)

  displayedColumns = ['page', 'sourceFile', 'reason']

  paginatedRecords = computed(() => {
    const start = this.pageIndex() * this.pageSize()
    return this.ignoredRecords().slice(start, start + this.pageSize())
  })

  onPageChange(event: PageEvent) {
    this.pageSize.set(event.pageSize)
    this.pageIndex.set(event.pageIndex)
  }
}
