import { Component, OnInit } from '@angular/core';
import { ScenarioInjectable, RestService, Step } from "../../rest-api";
import { SettingsService } from "../../settings.service";
import { MatDialog } from "@angular/material/dialog";
import { InjectableEditDialogComponent } from "./edit/injectable-edit.component";
import { DerivedInjectableDialogComponent } from "./derived/derived-injectable.component";
import { PageComponent } from "../../app.component";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";
import { CookieService } from "ngx-cookie-service";

export function sortBy(array: any[], attr: string, options?: { reverse?: boolean, lowerCase?: boolean }): any[]{
  let sorted = array.sort((a, b) => {
    let left = a[attr]; let right = b[attr];
    if (options?.lowerCase) {
      left = left.toLowerCase(); right = right.toLowerCase();
    }
    return (left > right || (left !== undefined && right === undefined)) ? 1 : (left < right || (left === undefined && right !== undefined)) ? -1 : 0;
  });
  if (options?.reverse)
    sorted = sorted.reverse();
  return sorted;
}

interface ScenarioInjectableExt extends ScenarioInjectable {
  steps: Step[];
}

@Component({
  selector: 'app-injectables',
  templateUrl: './injectables.component.html',
  styleUrls: ['./injectables.component.scss']
})
export class InjectablesComponent extends PageComponent implements OnInit {
  // grouped injectables
  protected groupedInjectables?: Record<string, ScenarioInjectableExt[]>;
  protected injectables: ScenarioInjectable[] = [];
  protected injectableMismatch?: { missing?: string[], ahead?: string[] };
  private _steps: Step[] = [];

  constructor(protected rest: RestService, protected settings: SettingsService, protected dialog: MatDialog,
              protected cookies: CookieService){
    super();
  }

  ngOnInit() {
    this.subscriptions.push(this.settings.activeScenario$.subscribe(scenario => {
      if (!scenario || !this.settings.module$.value)
        return;
      this.setLoading(true);
      this.rest.getAvailableSteps(this.settings.module$.value.name).subscribe(steps => {
        this._steps = steps;
        this.rest.getScenarioInjectables(scenario).subscribe(injectables => {
          this.injectables = injectables;
          this.checkInjectableConsistency();
          // this.groups = [...new Set(injectables.map(injectable => injectable.group))].sort();
          this.groupedInjectables = {};
          injectables.forEach(_inj => {
            if (_inj.scope == 'step') return;
            const group = _inj.group || 'general';
            if (!this.groupedInjectables![group])
              this.groupedInjectables![group] = [];
            const inj = Object.assign({ steps: this.getUsage(_inj)}, _inj);
            this.groupedInjectables![group].push(inj);
          })
          Object.keys(this.groupedInjectables).forEach(group => {
              // this.groupedInjectables[group] = sortBy(this.groupedInjectables[group], 'name');
              this.groupedInjectables![group] = sortBy(this.groupedInjectables![group], 'order');
            }
          );
          this.setLoading(false);
        })
      });
    }));
  }

  checkInjectableConsistency(): void {
    const modInjNames = this.settings.moduleInjectables.map(inj => inj.name);
    const injNames = this.injectables.map(inj => inj.name);
    const missingInModule = injNames.filter(n => !modInjNames.includes(n));
    const missingInScenario = modInjNames.filter(n => !injNames.includes(n));
    this.injectableMismatch = (missingInScenario.length || missingInModule.length)? {}: undefined;
    if (missingInScenario.length) {
      this.injectableMismatch!.missing = missingInScenario;
    }
    if (missingInModule.length) {
      this.injectableMismatch!.ahead = missingInModule;
    }
  }

  getUsage(injectable: ScenarioInjectable): Step[] {
    return this._steps.filter(step => step.injectables?.includes(injectable.name));
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
    const scenario = this.settings.activeScenario$.value;
    if (!scenario || !this.groupedInjectables) return;
    const children = Object.values(this.groupedInjectables).flat().filter(inj => (inj.parents || []).indexOf(injectable.id) >= 0);
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
        title: $localize `Reset Injectables`,
        message: $localize `<p>Do you want to reset ALL of the injectable values to the project defaults?</p>`,
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
        title: $localize `Synchronize Injectables`,
        message: $localize `<p>Do you want to synchronize the injectables with the current state of the module? All values you set are being kept.</p>
                            <p>This step might be required if your scenario is out of date due to changes made to the module.</p>`,
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

  removeHTMLTags(html: string): string {
    const parser = new DOMParser();
    return parser.parseFromString(html, "text/html").body.textContent || '';
  }
}
