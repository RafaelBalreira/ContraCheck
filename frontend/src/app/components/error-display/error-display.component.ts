import { Component, input, output, ChangeDetectionStrategy } from '@angular/core'
import { MatButtonModule } from '@angular/material/button'
import { MatIconModule } from '@angular/material/icon'

@Component({
  selector: 'app-error-display',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './error-display.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrls: ['./error-display.component.scss'],
})
export class ErrorDisplayComponent {
  message = input('')
  dismiss = output<void>()
}
