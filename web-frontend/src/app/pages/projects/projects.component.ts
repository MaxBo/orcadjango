import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { Project, RestService, User } from "../../rest-api";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "./edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { AuthService } from "../../auth.service";
import { UserSettingsService } from "../../user-settings.service";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";

@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss']
})
export class ProjectsComponent implements OnInit{
  projects: Project[] = [];
  users: User[] = [];
  viewType: 'list-view' | 'grid-view' = 'grid-view';
  @ViewChild('deleteProjectTemplate') deleteProjectTemplate?: TemplateRef<any>;

  constructor(private rest: RestService, private dialog: MatDialog, private settings: UserSettingsService) {}

  ngOnInit() {
    this.settings.module$.subscribe(module => {
      this.rest.getProjects({ module: module }).subscribe(projects => {
        this.projects = projects;
      });
    })
    this.rest.getUsers().subscribe(users => {
      this.users = users;
    });
  }

  onCreateProject(): void {
    const user = this.settings.user$.value;
    const data: ProjectEditDialogData = {
      title: 'Create new Project',
      confirmButtonText: 'Create',
      project: {
        name: '',
        description: '',
        user: user?.id
      }
    }
    const dialogref = this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
    dialogref.componentInstance.projectConfirmed.subscribe(project => {
      project.module = this.settings.module$.value;
      this.rest.createProject(project).subscribe(created => {
        dialogref.close();
        this.projects.push(created);
      })
    })
  }

  deleteProject(project: Project): void {
    let dialogRef = this.dialog.open(ConfirmDialogComponent, {
      panelClass: 'absolute',
      width: '300px',
      disableClose: true,
      data: {
        title: 'Remove Project',
        subtitle: project.name,
        template: this.deleteProjectTemplate,
        closeOnConfirm: false
      }
    });
    dialogRef.componentInstance.confirmed.subscribe(() => {
      this.rest.deleteProject(project).subscribe(() => {
        const idx = this.projects.indexOf(project);
        if (idx > -1) {
          this.projects.splice(idx, 1);
        }
      })
    })
  }

  editProject(project: Project): void {
    const data: ProjectEditDialogData = {
      title: 'Edit Project',
      confirmButtonText: 'Save',
      project: project
    }
    const dialogRef = this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.projectConfirmed.subscribe((edited) => {
      this.rest.patchProject(project, { name: edited.name, description: edited.description, user: edited.user }).subscribe(patched => {
        dialogRef.close();
        Object.assign(project, patched);
      });
    })
  }

  archiveProject(project: Project, archive: boolean): void {
    this.rest.patchProject(project, { archived: archive }).subscribe(patched => {
      Object.assign(project, patched);
    });
  }

  selectProject(project: Project): void {
    this.settings.setActiveProject(project);
  }
}
