import { Component, OnInit } from '@angular/core';
import { ScenarioInjectable, RestService } from "../../rest-api";
import { UserSettingsService } from "../../user-settings.service";
import { MatDialog } from "@angular/material/dialog";
import { InjectableEditDialogComponent } from "./edit/injectable-edit.component";
import { DerivedInjectableDialogComponent } from "./derived/derived-injectable.component";
import { PageComponent } from "../../app.component";

export function sortBy(array: any[], attr: string, options: { reverse: boolean } = { reverse: false }): any[]{
  let sorted = array.sort((a, b) =>
    (a[attr] > b[attr])? 1: (a[attr] < b[attr])? -1: 0);
  if (options.reverse)
    sorted = sorted.reverse();
  return sorted;
}

@Component({
  selector: 'app-injectables',
  templateUrl: './injectables.component.html',
  styleUrls: ['./injectables.component.scss']
})
export class InjectablesComponent extends PageComponent implements OnInit {
  // grouped injectables
  groupedInjectables?: Record<string, ScenarioInjectable[]>;
  protected injectables: ScenarioInjectable[] = [];

  constructor(protected rest: RestService, protected settings: UserSettingsService, protected dialog: MatDialog){
    super();
  }

  ngOnInit() {
    this.settings.activeScenario$.subscribe(scenario => {
      if (!scenario) return;
      this.setLoading(true);
      this.rest.getScenarioInjectables(scenario).subscribe(injectables => {
        this.injectables = injectables;
        // this.groups = [...new Set(injectables.map(injectable => injectable.group))].sort();
        this.groupedInjectables = {};
        injectables.forEach(inj => {
          const group = inj.group || 'general'
          if (!this.groupedInjectables![group])
            this.groupedInjectables![group] = [];
          this.groupedInjectables![group].push(inj);
        })
        Object.keys(this.groupedInjectables).forEach(group => {
            // this.groupedInjectables[group] = sortBy(this.groupedInjectables[group], 'name');
            this.groupedInjectables![group] = sortBy(this.groupedInjectables![group], 'order');
          }
        );
        this.setLoading(false);
      })
    })
  }

  editInjectable(injectable: ScenarioInjectable): void {
    if (injectable.editable) {
      const dialogRef = this.dialog.open(InjectableEditDialogComponent, {
        panelClass: 'absolute',
        minWidth: '400px',
        disableClose: true,
        data: { injectable: injectable }
      });
      dialogRef.componentInstance.valueConfirmed.subscribe((value) => {
        dialogRef.componentInstance.setLoading(true);
        this.rest.patchScenarioInjectable(injectable, value).subscribe(patched => {
          dialogRef.close();
          // workaround to force update of injectable
          setTimeout(() => injectable.value = undefined);
          setTimeout(() => injectable.value = patched.value);
          // update derived injectables
          this.updateChildren(injectable);
        }, error => {
          dialogRef.componentInstance.setErrors(error.error);
          dialogRef.componentInstance.setLoading(false);
        });
      })
    }
    else {
      const parents = (injectable.parents || []).map(pId => this.injectables.find(inj => inj.id === pId ))
      const dialogRef = this.dialog.open(DerivedInjectableDialogComponent, {
        panelClass: 'absolute',
        disableClose: true,
        data: { injectable: injectable, parents: parents }
      });
      dialogRef.componentInstance.injectableClicked.subscribe(injectable => {
        dialogRef.close();
        this.editInjectable((injectable));
      })
    }
  }

  updateChildren(injectable: ScenarioInjectable) {
    const children = this.injectables.filter(inj => (inj.parents || []).indexOf(injectable.id) >= 0);
    const scenario = this.settings.activeScenario$.value;
    if (!scenario) return;
    children.forEach(inj => {
      this.rest.getScenarioInjectable(inj.id, scenario).subscribe(updated => {
        setTimeout(() => inj.value = undefined);
        setTimeout(() => inj.value = updated.value);
      });
    })
  }
}
