import { Component, OnInit } from '@angular/core';
import { RestService, Scenario } from "../../rest-api";
import { MatDialog } from "@angular/material/dialog";
import { UserSettingsService } from "../../user-settings.service";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "../projects/edit/project-edit.component";
import { ScenarioEditDialogComponent, ScenarioEditDialogData } from "./edit/scenario-edit.component";

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.scss']
})
export class ScenariosComponent implements OnInit {
  scenarios: Scenario[] = [];
  viewType: 'list-view' | 'grid-view' = 'grid-view';

  constructor(private rest: RestService, private dialog: MatDialog, private settings: UserSettingsService) {}

  ngOnInit() {
    this.settings.activeProject$.subscribe(project => {
      this.rest.getScenarios({ project: project }).subscribe(scenarios => {
        this.scenarios = scenarios;
      });
    })
  }

  onCreateScenario(): void {
    const data: ScenarioEditDialogData = {
      title: 'Create new Scenario',
      confirmButtonText: 'Create',
      scenario: {
        name: '',
        description: ''
      }
    }
    const dialogref = this.dialog.open(ScenarioEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
    dialogref.componentInstance.scenarioConfirmed.subscribe(scenario => {
      scenario.project = this.settings.activeProject$?.value?.id;
      this.rest.createScenario(scenario).subscribe(created => {
        dialogref.close();
        this.scenarios.push(created);
      })
    })

  }

  deleteScenario(scenario: Scenario): void {

  }

  editScenario(scenario: Scenario): void {

  }

  selectScenario(scenario: Scenario): void {
    this.settings.setActiveSenario(scenario);
  }
}
