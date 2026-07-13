import { Component, input } from '@angular/core'
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner'

@Component({
  selector: 'app-progress-indicator',
  imports: [MatProgressSpinnerModule],
  templateUrl: './progress-indicator.component.html',
  styleUrls: ['./progress-indicator.component.scss'],
})
export class ProgressIndicatorComponent {
  totalPages = input(0)
  totalRecords = input(0)
  ignoredRecords = input(0)
  processing = input(false)
}
