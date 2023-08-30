import { Component, EventEmitter, Inject, Output } from '@angular/core';
import { ScenarioInjectable } from "../../../rest-api";
import { BehaviorSubject } from "rxjs";
import { MAT_DIALOG_DATA } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-injectable-edit',
  templateUrl: './injectable-edit.component.html',
  styleUrls: ['./injectable-edit.component.scss']
})
export class InjectableEditDialogComponent {
  protected value: any;
  protected errors: Record<string, string> = {};
  protected injectable: ScenarioInjectable;
  protected defaultValue: any;
  isLoading$ = new BehaviorSubject<boolean>(false);
  @Output() valueConfirmed = new EventEmitter<any>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: { injectable: ScenarioInjectable, defaultValue: any }, protected settings: SettingsService) {
    this.injectable = data.injectable;
    this.defaultValue = data.defaultValue;
    this.value = data.injectable.value;
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }

  setErrors(errors: Record<string, string>) {
    this.errors = errors;
  }

  onConfirmClick() {
    this.valueConfirmed.emit(this.value);
  }

  resetToDefault(): void {
    this.value = this.defaultValue;
    const clone = Object.assign({}, this.injectable);
    clone.value = this.defaultValue;
    this.injectable = clone;
  }
}
