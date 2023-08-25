import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { RestService, Scenario } from "../../rest-api";
import { MatDialog } from "@angular/material/dialog";
import { SettingsService } from "../../settings.service";
import { ScenarioEditDialogComponent, ScenarioEditDialogData } from "./edit/scenario-edit.component";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";
import { CookieService } from "ngx-cookie-service";
import { PageComponent } from "../../app.component";

@Component({
  selector: 'app-scenarios',
  templateUrl: './scenarios.component.html',
  styleUrls: ['./scenarios.component.scss']
})
export class ScenariosComponent extends PageComponent implements OnInit {
  scenarios: Scenario[] = [];
  viewType: 'list-view' | 'grid-view' = 'grid-view';
  @ViewChild('deleteScenarioTemplate') deleteScenarioTemplate?: TemplateRef<any>;

  constructor(private rest: RestService, private dialog: MatDialog, protected settings: SettingsService,
              private cookies: CookieService) {
    super();
  }

  ngOnInit() {
    const viewType = this.cookies.get('scenario-view-type');
    if (viewType === 'list-view') this.viewType = 'list-view';
    this.subscriptions.push(this.settings.activeProject$.subscribe(project => {
      this.setLoading(true);
      if (!project) {
        this.scenarios = [];
        this.setLoading(false);
      }
      else {
        this.rest.getScenarios({ project: project }).subscribe(scenarios => {
          this.scenarios = scenarios;
          this.setLoading(false);
        });
      }
    }));
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
    const dialogRef = this.dialog.open(ScenarioEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.scenarioConfirmed.subscribe(scenario => {
      dialogRef.componentInstance.setLoading(true);
      scenario.project = this.settings.activeProject$?.value?.id;
      this.rest.createScenario(scenario).subscribe(created => {
        dialogRef.close();
        this.scenarios.push(created);
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
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
      dialogRef.componentInstance.setLoading(true);
      this.rest.deleteScenario(scenario).subscribe(() => {
        dialogRef.close();
        const idx = this.scenarios.indexOf(scenario);
        if (idx > -1) {
          this.scenarios.splice(idx, 1);
        }
        if (scenario.id === this.settings.activeScenario$?.value?.id)
          this.settings.setActiveSenario(undefined)
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
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
      dialogRef.componentInstance.setLoading(true);
      this.rest.patchScenario(scenario, { name: edited.name, description: edited.description }).subscribe(patched => {
        dialogRef.close();
        Object.assign(scenario, patched);
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
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
