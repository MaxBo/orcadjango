import { Component, OnInit } from '@angular/core';
import { Inj, RestService } from "../../rest-api";
import { UserSettingsService } from "../../user-settings.service";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "../projects/edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { InjectableEditDialogComponent } from "./edit/injectable-edit.component";

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
  injectables: Record<string, Inj[]> = {};

  constructor(private rest: RestService, private settings: UserSettingsService, private dialog: MatDialog){}

  ngOnInit() {
    this.settings.activeScenario$.subscribe(scenario => {
      if (scenario)
        this.rest.getInjectables(scenario).subscribe(injectables => {
          // this.groups = [...new Set(injectables.map(injectable => injectable.group))].sort();
          this.injectables = {};
          injectables.forEach(inj => {
            if (!this.injectables[inj.group])
              this.injectables[inj.group] = [];
            this.injectables[inj.group].push(inj);
          })
          Object.keys(this.injectables).forEach(group =>
            this.injectables[group] = sortBy(this.injectables[group], 'order')
          );
        })
    })
  }

  editInjectable(injectable: Inj): void {
    const dialogRef = this.dialog.open(InjectableEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: { injectable: injectable }
    });
    dialogRef.componentInstance.valueConfirmed.subscribe((value) => {
      this.rest.patchInjectable(injectable, value).subscribe(patched => {
        dialogRef.close();
        Object.assign(injectable, patched);
      });
    })
  }
}
