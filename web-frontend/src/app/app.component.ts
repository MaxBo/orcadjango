import { Component } from '@angular/core';
import { UserSettingsService } from "./user-settings.service";
import { Module, RestService } from "./rest-api";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'web-frontend';

  constructor(protected settings: UserSettingsService, private rest: RestService) {}
}
