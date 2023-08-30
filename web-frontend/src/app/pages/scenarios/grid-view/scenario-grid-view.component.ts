import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Scenario } from "../../../rest-api";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-scenario-grid-view',
  templateUrl: './scenario-grid-view.component.html',
  styleUrls: ['./scenario-grid-view.component.scss', '../../projects/grid-view/project-grid-view.component.scss']
})
export class ScenarioGridViewComponent {
  @Input() scenarios: Scenario[] = [];
  @Output() onScenarioSelected = new EventEmitter<Scenario>();
  @Output() onEditScenario = new EventEmitter<Scenario>();
  @Output() onDeleteScenario = new EventEmitter<Scenario>();
  @Output() onCreateScenario = new EventEmitter<boolean>();

  constructor(protected settings: SettingsService) {}

}
