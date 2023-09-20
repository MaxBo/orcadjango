import { Component, OnInit } from '@angular/core';
import { ScenarioInjectable, RestService } from "../../rest-api";
import { SettingsService } from "../../settings.service";
import { MatDialog } from "@angular/material/dialog";
import { InjectableEditDialogComponent } from "./edit/injectable-edit.component";
import { DerivedInjectableDialogComponent } from "./derived/derived-injectable.component";
import { PageComponent } from "../../app.component";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";

export function sortBy(array: any[], attr: string, options?: { reverse?: boolean, lowerCase?: boolean }): any[]{
  let sorted = array.sort((a, b) => {
    let left = a[attr]; let right = b[attr];
    if (options?.lowerCase) {
      left = left.toLowerCase(); right = right.toLowerCase();
    }
    return (left > right) ? 1 : (left < right) ? -1 : 0;
  });
  if (options?.reverse)
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

  constructor(protected rest: RestService, protected settings: SettingsService, protected dialog: MatDialog){
    super();
  }

  ngOnInit() {
    this.subscriptions.push(this.settings.activeScenario$.subscribe(scenario => {
      if (!scenario) return;
      this.setLoading(true);
      this.rest.getScenarioInjectables(scenario).subscribe(injectables => {
        this.injectables = injectables;
        // this.groups = [...new Set(injectables.map(injectable => injectable.group))].sort();
        this.groupedInjectables = {};
        injectables.forEach(inj => {
          const group = inj.group || 'general';
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
    }));
  }

  editInjectable(injectable: ScenarioInjectable): void {
    if (injectable.editable) {
      const mInj = this.settings.moduleInjectables.find(inj => inj.name === injectable.name);
      const dialogRef = this.dialog.open(InjectableEditDialogComponent, {
        panelClass: 'absolute',
        minWidth: '400px',
        disableClose: true,
        data: { injectable: injectable, defaultValue: mInj?.value }
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

  reset(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      disableClose: false,
      width: '400px',
      data: {
        title: 'Synchronize Injectables',
        message: '<p>Do you want to reset ALL of the injectable values to the project defaults?</p>',
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe( () => {
      this.isLoading$.next(true);
      if (!this.settings.activeScenario$.value) return;
      this.rest.resetInjectables(this.settings.activeScenario$.value).subscribe(() =>
        window.location.reload());
    });
  }

  synchronize(): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      disableClose: false,
      width: '400px',
      data: {
        title: 'Synchronize Injectables',
        message: '<p>Do you want to synchronize the injectables with the current state of the module? All values you set are being kept.</p>' +
                 '<p>This step might be required if your scenario is out of date due to changes made to the module.</p>',
        closeOnConfirm: true
      }
    });
    dialogRef.componentInstance.confirmed.subscribe( () => {
      this.isLoading$.next(true);
      if (!this.settings.activeScenario$.value) return;
      this.rest.synchronizeInjectables(this.settings.activeScenario$.value).subscribe(() =>
        window.location.reload());
      }
    );
  }
}
