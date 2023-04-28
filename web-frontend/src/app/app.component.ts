import { Component } from '@angular/core';
import { UserSettingsService } from "./user-settings.service";
import { AuthService } from "./auth.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'web-frontend';

  constructor(protected settings: UserSettingsService, protected auth: AuthService) {}
}
