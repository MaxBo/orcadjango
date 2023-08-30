import { Component } from '@angular/core';
import { SettingsService } from "../../settings.service";

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent {
  constructor(protected settings: SettingsService) {
  }
}
