export interface PaySlip {
  employeeName: string
  totalVencimentos: string
  sourceFile: string
}

export interface IgnoredRecord {
  page: number
  reason: string
  sourceFile: string
}

export interface ProcessResult {
  token: string
  records: PaySlip[]
  ignoredRecords: IgnoredRecord[]
  totalPages: number
  totalRecords: number
  ignoredRecordsCount: number
  warnings: string[]
}

export interface ProcessError {
  detail: string
}
