import { Component, EventEmitter, Inject, Output } from '@angular/core';
import { Inj } from "../../../rest-api";
import { BehaviorSubject } from "rxjs";
import { MAT_DIALOG_DATA } from "@angular/material/dialog";
import { UserSettingsService } from "../../../user-settings.service";

@Component({
  selector: 'app-edit',
  templateUrl: './injectable-edit.component.html',
  styleUrls: ['./injectable-edit.component.scss']
})
export class InjectableEditDialogComponent {
  protected value: any;
  protected errors: Record<string, string> = {};
  protected injectable: Inj;
  isLoading$ = new BehaviorSubject<boolean>(false);
  @Output() valueConfirmed = new EventEmitter<any>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: { injectable: Inj }, protected settings: UserSettingsService) {
    this.injectable = data.injectable;
    this.value = data.injectable.value;
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }

  setErrors(errors: Record<string, string>) {
    this.errors = errors;
  }

  onConfirmClick() {
/*    const injectable: Inj = Object.assign({}, this.injectable);
    injectable.value = this.value;*/
    this.valueConfirmed.emit(this.value);
  }

}
