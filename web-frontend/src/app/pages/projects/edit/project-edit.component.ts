import { Component, EventEmitter, Inject, Input, Output, TemplateRef } from '@angular/core';
import { Inj, Project, User } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { BehaviorSubject } from "rxjs";
import { SettingsService } from "../../../settings.service";
import { Moment } from "moment/moment";

export interface ProjectEditDialogData {
  project?: Project,
  title: string,
  confirmButtonText?: string,
  cancelButtonText?: string,
  closeOnConfirm?: boolean,
  showDate?: boolean
}

@Component({
  templateUrl: './project-edit.component.html',
  styleUrls: ['./project-edit.component.scss']
})
export class ProjectEditDialogComponent {
  protected projectForm: FormGroup;
  protected errors: Record<string, string> = {};
  protected project?: Project;
  protected createdDate?: Moment;
  private injValues: any[];
  isLoading$ = new BehaviorSubject<boolean>(false);
  @Output() projectConfirmed = new EventEmitter<Project>();
  Object = Object;

  constructor(@Inject(MAT_DIALOG_DATA) public data: ProjectEditDialogData, protected settings: SettingsService,
              private formBuilder: FormBuilder) {
    data.confirmButtonText = data.confirmButtonText || 'Save';
    data.cancelButtonText = data.cancelButtonText || 'Cancel';

    this.project = this.data.project;
    this.injValues = this.project!.injectables.map(inj => inj.value);
    this.projectForm = this.formBuilder.group({
      name: this.project?.name || '',
      description: this.project?.description || '',
      user: this.project?.user || -1,
      code: this.project?.code || '',
      date:  this.project?.date
    })
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }

  setErrors(errors: Record<string, string>) {
    this.errors = errors;
  }

  onConfirmClick() {
    this.errors = {};
    this.projectForm.markAllAsTouched();
    if (this.projectForm.invalid) return;
    const injectables: Inj[] = this.project? this.project.injectables.map((inj, idx) => {
      const clone = Object.assign({}, inj);
      clone.value = this.injValues[idx];
      if (!clone.value)
        this.errors[clone.name] = 'value required';
      return clone;
    }): [];
    if (Object.keys(this.errors).length) return;
    const project: any = {
      id: this.project?.id,
      name: this.projectForm.value.name,
      description: this.projectForm.value.description,
      user: (this.projectForm.value.user !== -1)? this.projectForm.value.user: null,
      code: this.projectForm.value.code,
      init: [],
      injectables: injectables,
      scenario_count: this.project?.scenario_count || 0
    }
    if (this.data.showDate) {
      project.date = this.projectForm.value.date;
    }
    this.projectConfirmed.emit(project);
  }

  injectableChanged(idx: number, value: any): void {
    this.injValues[idx] = value;
  }
}
