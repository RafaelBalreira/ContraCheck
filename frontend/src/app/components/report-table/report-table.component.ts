import { Component, input, output, signal, computed, ChangeDetectionStrategy } from '@angular/core'
import { MatTableModule } from '@angular/material/table'
import { MatSortModule, Sort } from '@angular/material/sort'
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator'
import { MatFormFieldModule } from '@angular/material/form-field'
import { MatInputModule } from '@angular/material/input'
import { MatButtonModule } from '@angular/material/button'
import { MatIconModule } from '@angular/material/icon'
import { FormsModule } from '@angular/forms'
import { PaySlip, IgnoredRecord } from '../../models/report.models'

@Component({
  selector: 'app-report-table',
  imports: [
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    FormsModule,
  ],
  templateUrl: './report-table.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrls: ['./report-table.component.scss'],
})
export class ReportTableComponent {
  records = input<PaySlip[]>([])
  ignoredRecords = input<IgnoredRecord[]>([])
  token = input('')
  exportCsv = output<void>()
  exportXlsx = output<void>()
  exportPdf = output<void>()
  newFile = output<void>()
  showIgnored = output<void>()

  searchTerm = signal('')
  pageSize = signal(10)
  pageIndex = signal(0)
  sortState = signal<Sort>({ active: '', direction: '' })

  displayedColumns = ['employeeName', 'totalVencimentos', 'sourceFile']

  filteredRecords = computed(() => {
    const term = this.searchTerm().toLowerCase().trim()
    let list = this.records()
    if (term) {
      list = list.filter((r) => r.employeeName.toLowerCase().includes(term))
    }
    return list
  })

  sortedRecords = computed(() => {
    let list = this.filteredRecords()
    const s = this.sortState()
    if (!s.active || s.direction === '') return list
    const sorted = [...list]
    const isAsc = s.direction === 'asc'
    sorted.sort((a, b) => {
      switch (s.active) {
        case 'employeeName':
          return (a.employeeName < b.employeeName ? -1 : a.employeeName > b.employeeName ? 1 : 0) * (isAsc ? 1 : -1)
        case 'totalVencimentos':
          return (this._parseValue(a.totalVencimentos) - this._parseValue(b.totalVencimentos)) * (isAsc ? 1 : -1)
        case 'sourceFile':
          return (a.sourceFile < b.sourceFile ? -1 : a.sourceFile > b.sourceFile ? 1 : 0) * (isAsc ? 1 : -1)
        default:
          return 0
      }
    })
    return sorted
  })

  paginatedRecords = computed(() => {
    const start = this.pageIndex() * this.pageSize()
    return this.sortedRecords().slice(start, start + this.pageSize())
  })

  totalFiltered = computed(() => this.sortedRecords().length)

  onSearch(value: string) {
    this.searchTerm.set(value)
    this.pageIndex.set(0)
  }

  onSortChange(sort: Sort) {
    this.sortState.set(sort)
  }

  onPageChange(event: PageEvent) {
    this.pageSize.set(event.pageSize)
    this.pageIndex.set(event.pageIndex)
  }

  private _parseValue(value: string): number {
    const cleaned = value.replace('R$', '').replace(/\./g, '').replace(',', '.').trim()
    return parseFloat(cleaned) || 0
  }
}
