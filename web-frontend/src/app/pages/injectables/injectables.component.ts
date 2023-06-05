import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Inj, RestService } from "../../rest-api";
import { UserSettingsService } from "../../user-settings.service";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "../projects/edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { InjectableEditDialogComponent } from "./edit/injectable-edit.component";
import { DerivedInjectableDialogComponent } from "./derived/derived-injectable.component";

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
export class InjectablesComponent implements OnInit {
  // grouped injectables
  groupedInjectables: Record<string, Inj[]> = {};
  protected injectables: Inj[] = [];

  constructor(protected rest: RestService, protected settings: UserSettingsService, protected dialog: MatDialog){}

  ngOnInit() {
    this.settings.activeScenario$.subscribe(scenario => {
      if (scenario)
        this.rest.getInjectables(scenario).subscribe(injectables => {
          this.injectables = injectables;
          // this.groups = [...new Set(injectables.map(injectable => injectable.group))].sort();
          this.groupedInjectables = {};
          injectables.forEach(inj => {
            if (!this.groupedInjectables[inj.group])
              this.groupedInjectables[inj.group] = [];
            this.groupedInjectables[inj.group].push(inj);
          })
          Object.keys(this.groupedInjectables).forEach(group =>
            this.groupedInjectables[group] = sortBy(this.groupedInjectables[group], 'order')
          );
        })
    })
  }

  editInjectable(injectable: Inj): void {
    if (injectable.editable) {
      const dialogRef = this.dialog.open(InjectableEditDialogComponent, {
        panelClass: 'absolute',
        // width: '1200px',
        disableClose: true,
        data: { injectable: injectable }
      });
      dialogRef.componentInstance.valueConfirmed.subscribe((value) => {
        this.rest.patchInjectable(injectable, value).subscribe(patched => {
          dialogRef.close();
          // workaround to force update of injectable
          setTimeout(() => injectable.value = undefined);
          setTimeout(() => injectable.value = patched.value);
          this.updateChildren(injectable);
        });
      })
    }
    else {
      const parents = injectable.parents.map(pId => this.injectables.find(inj => inj.id === pId ))
      const dialogRef = this.dialog.open(DerivedInjectableDialogComponent, {
        panelClass: 'absolute',
        // width: '700px',
        disableClose: true,
        data: { injectable: injectable, parents: parents }
      });
      dialogRef.componentInstance.injectableClicked.subscribe(injectable => {
        dialogRef.close();
        this.editInjectable((injectable));
      })
    }
  }

  updateChildren(injectable: Inj) {
    const children = this.injectables.filter(inj => inj.parents.indexOf(injectable.id) >= 0);
    const scenario = this.settings.activeScenario$.value;
    if (!scenario) return;
    children.forEach(inj => {
      this.rest.getInjectable(inj.id, scenario).subscribe(updated => {
        setTimeout(() => inj.value = undefined);
        setTimeout(() => inj.value = updated.value);
      });
    })
  }
}
