import { Component, EventEmitter, Inject, Output } from '@angular/core';
import { ScenarioInjectable } from "../../../rest-api";
import { MAT_DIALOG_DATA } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-derived',
  templateUrl: './derived-injectable.component.html',
  styleUrls: ['./derived-injectable.component.scss']
})
export class DerivedInjectableDialogComponent {
  protected injectable: ScenarioInjectable;
  protected parents: ScenarioInjectable[];
  @Output() injectableClicked = new EventEmitter<ScenarioInjectable>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: { injectable: ScenarioInjectable, parents: ScenarioInjectable[] }, protected settings: SettingsService) {
    this.injectable = data.injectable;
    this.parents = data.parents;
  }

}
