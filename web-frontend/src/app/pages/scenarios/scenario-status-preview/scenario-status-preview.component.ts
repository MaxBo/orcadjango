import { Component, Input } from '@angular/core';
import { Scenario } from "../../../rest-api";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-scenario-status-preview',
  templateUrl: './scenario-status-preview.component.html',
  styleUrls: ['./scenario-status-preview.component.scss']
})
export class ScenarioStatusPreviewComponent {
  @Input() scenario!: Scenario;

  constructor(protected settings: SettingsService) {}
}
