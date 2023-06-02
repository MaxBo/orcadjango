import { Component, EventEmitter, Inject, Output } from '@angular/core';
import { Inj } from "../../../rest-api";
import { MAT_DIALOG_DATA } from "@angular/material/dialog";
import { UserSettingsService } from "../../../user-settings.service";

@Component({
  selector: 'app-derived',
  templateUrl: './derived-injectable.component.html',
  styleUrls: ['./derived-injectable.component.scss']
})
export class DerivedInjectableDialogComponent {
  protected injectable: Inj;
  protected parents: Inj[];
  @Output() injectableClicked = new EventEmitter<Inj>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: { injectable: Inj, parents: Inj[] }, protected settings: UserSettingsService) {
    this.injectable = data.injectable;
    this.parents = data.parents;
  }

}
