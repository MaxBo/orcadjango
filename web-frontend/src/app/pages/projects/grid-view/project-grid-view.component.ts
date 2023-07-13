import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Project, User } from "../../../rest-api";
import { UserSettingsService } from "../../../user-settings.service";

@Component({
  selector: 'app-project-grid-view',
  templateUrl: './project-grid-view.component.html',
  styleUrls: ['./project-grid-view.component.scss']
})
export class ProjectGridViewComponent {
  @Input() projects: Project[] = [];
  @Output() onProjectSelected = new EventEmitter<Project>();
  @Output() onEditProject = new EventEmitter<Project>();
  @Output() onDeleteProject = new EventEmitter<Project>();
  @Output() onArchiveProject = new EventEmitter<{ project: Project, archive: boolean }>();
  @Output() onCreateProject = new EventEmitter<boolean>();

  constructor(protected settings: UserSettingsService) {}

}
