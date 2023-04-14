import { Component, EventEmitter, Inject, Input, Output, TemplateRef } from '@angular/core';
import { Project, User } from "../../../rest-api";
import { FormBuilder, FormGroup } from "@angular/forms";
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { BehaviorSubject } from "rxjs";
import { UserSettingsService } from "../../../user-settings.service";

export interface ProjectEditDialogData {
  project?: Project,
  title: string,
  confirmButtonText?: string,
  cancelButtonText?: string,
  closeOnConfirm?: boolean,
}

@Component({
  templateUrl: './project-edit.component.html',
  styleUrls: ['./project-edit.component.scss']
})
export class ProjectEditDialogComponent {
  protected projectForm: FormGroup;
  protected errors: Record<string, string> = {};
  private project?: Project;
  isLoading$ = new BehaviorSubject<boolean>(false);
  @Output() projectConfirmed = new EventEmitter<Project>();

  constructor(@Inject(MAT_DIALOG_DATA) public data: ProjectEditDialogData, protected settings: UserSettingsService,
              private formBuilder: FormBuilder) {
    data.confirmButtonText = data.confirmButtonText || 'Save';
    data.cancelButtonText = data.cancelButtonText || 'Cancel';
    this.project = this.data.project;
    this.projectForm = this.formBuilder.group({
      name: this.project?.name || '',
      description: this.project?.description || '',
      user: this.project?.user || -1,
      code: this.project?.code || ''
    })
  }

  setLoading(loading: boolean) {
    this.isLoading$.next(loading);
  }

  setErrors(errors: Record<string, string>) {
    this.errors = errors;
  }

  onConfirmClick() {
    this.projectForm.markAllAsTouched();
    if (this.projectForm.invalid) return;
    const project = {
      id: this.project?.id,
      name: this.projectForm.value.name,
      description: this.projectForm.value.description,
      user: (this.projectForm.value.user !== -1)? this.projectForm.value.user: null,
      code: this.projectForm.value.code
    }
    this.projectConfirmed.emit(project);
  }
}
