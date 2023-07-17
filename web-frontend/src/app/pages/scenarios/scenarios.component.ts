import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { RestService, Scenario } from "../../rest-api";
import { MatDialog } from "@angular/material/dialog";
import { UserSettingsService } from "../../user-settings.service";
import { ScenarioEditDialogComponent, ScenarioEditDialogData } from "./edit/scenario-edit.component";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";
import { CookieService } from "ngx-cookie-service";

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.scss']
})
export class ScenariosComponent implements OnInit {
  scenarios: Scenario[] = [];
  viewType: 'list-view' | 'grid-view' = 'grid-view';
  @ViewChild('deleteScenarioTemplate') deleteScenarioTemplate?: TemplateRef<any>;

  constructor(private rest: RestService, private dialog: MatDialog, protected settings: UserSettingsService,
              private cookies: CookieService) {}

  ngOnInit() {
    const viewType = this.cookies.get('scenario-view-type');
    if (viewType === 'list-view') this.viewType = 'list-view';
    this.settings.activeProject$.subscribe(project => {
      this.settings.setLoading(true);
      this.rest.getScenarios({ project: project }).subscribe(scenarios => {
        this.scenarios = scenarios;
        this.settings.setLoading(false);
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
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Remove Project',
        subtitle: scenario.name,
        template: this.deleteScenarioTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.rest.deleteScenario(scenario).subscribe(() => {
        dialogRef.close();
        const idx = this.scenarios.indexOf(scenario);
        if (idx > -1) {
          this.scenarios.splice(idx, 1);
        }
        if (scenario.id === this.settings.activeScenario$?.value?.id)
          this.settings.setActiveSenario(undefined)
      })
    })
  }

  editScenario(scenario: Scenario): void {
    const data: ScenarioEditDialogData = {
      title: 'Edit Scenario',
      confirmButtonText: 'Save',
      scenario: scenario
    }
    const dialogRef = this.dialog.open(ScenarioEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.scenarioConfirmed.subscribe((edited) => {
      this.rest.patchScenario(scenario, { name: edited.name, description: edited.description }).subscribe(patched => {
        dialogRef.close();
        Object.assign(scenario, patched);
      });
    })
  }

  selectScenario(scenario: Scenario): void {
    this.settings.setActiveSenario(scenario);
  }

  changeView(viewType: 'list-view' | 'grid-view'): void {
    this.viewType = viewType;
    this.cookies.set('scenario-view-type', viewType);
  }
}
