import { Component } from '@angular/core';
import { UserSettingsService } from "../../user-settings.service";

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.component.html',
  styleUrls: ['./welcome.component.scss']
})
export class WelcomeComponent {
  constructor(protected settings: UserSettingsService) {
  }
}
