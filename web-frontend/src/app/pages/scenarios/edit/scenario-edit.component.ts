import { Component, EventEmitter, Inject, Output } from '@angular/core';
import { FormBuilder, FormGroup } from "@angular/forms";
import { Scenario } from "../../../rest-api";
import { BehaviorSubject } from "rxjs";
import { MAT_DIALOG_DATA } from "@angular/material/dialog";
import { SettingsService } from "../../../settings.service";

export interface ScenarioEditDialogData {
  scenario?: Scenario,
  title: string,
  confirmButtonText?: string,
  cancelButtonText?: string,
  closeOnConfirm?: boolean,
}

@Component({
  templateUrl: './scenario-edit.component.html',
  styleUrls: ['./scenario-edit.component.scss', '../../projects/edit/project-edit.component.scss']
})
export class ScenarioEditDialogComponent {
  protected scenarioForm: FormGroup;
  protected errors: Record<string, string> = {};
  private scenario?: Scenario;
  isLoading$ = new BehaviorSubject<boolean>(false);
  @Output() scenarioConfirmed = new EventEmitter<Scenario>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: ScenarioEditDialogData, protected settings: SettingsService,
              private formBuilder: FormBuilder) {
    data.confirmButtonText = data.confirmButtonText || 'Save';
    data.cancelButtonText = data.cancelButtonText || 'Cancel';
    this.scenario = this.data.scenario;
    this.scenarioForm = this.formBuilder.group({
      name: this.scenario?.name || '',
      description: this.scenario?.description || '',
    })
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }

  setErrors(errors: Record<string, string>) {
    this.errors = errors;
  }

  onConfirmClick() {
    this.scenarioForm.markAllAsTouched();
    if (this.scenarioForm.invalid) return;
    const scenario: Scenario = {
      id: this.scenario?.id,
      name: this.scenarioForm.value.name,
      description: this.scenarioForm.value.description
    }
    this.scenarioConfirmed.emit(scenario);
  }
}
