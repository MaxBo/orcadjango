import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Project, User } from "../../../rest-api";
import { UserSettingsService } from "../../../user-settings.service";

@Component({
  selector: 'app-grid-view',
  templateUrl: './grid-view.component.html',
  styleUrls: ['./grid-view.component.scss']
})
export class GridViewComponent {
  @Input() projects: Project[] = [];
  @Input() users: User[] = [];
  @Output() projectSelected = new EventEmitter<Project>();
  @Output() onEditProject = new EventEmitter<Project>();
  @Output() onCreateProject = new EventEmitter<boolean>();

  constructor(protected settings: UserSettingsService) {
  }
}
