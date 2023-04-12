import { Component, OnInit } from '@angular/core';
import { Project, RestService, User } from "../../rest-api";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "./edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { AuthService } from "../../auth.service";

@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss']
})
export class ProjectsComponent implements OnInit{
  projects: Project[] = [];
  users: User[] = [];
  viewType: 'list-view' | 'grid-view' = 'grid-view';

  constructor(private rest: RestService, private dialog: MatDialog, private auth: AuthService) {}

  ngOnInit() {
    this.rest.getProjects().subscribe(projects => {
      this.projects = projects;
    });
    this.rest.getUsers().subscribe(users => {
      this.users = users;
    });
  }

  onCreateProject(): void {
    this.auth.getCurrentUser().subscribe(user => {
      const data: ProjectEditDialogData = {
        title: 'Create new Project',
        confirmButtonText: 'Create',
        users: this.users,
        project: {
          name: '',
          description: '',
          user: user
        }
      }
      const dialogref = this.dialog.open(ProjectEditDialogComponent, {
        panelClass: 'absolute',
        width: '700px',
        disableClose: true,
        data: data
      });
      dialogref.componentInstance.projectConfirmed.subscribe(project => {
        this.rest.createProject(project).subscribe(created => {
          dialogref.close();
          this.projects.push(created);
        })
      })
    })
  }

  editProject(project: Project): void {
    const data: ProjectEditDialogData = {
      title: 'Edit Project',
      confirmButtonText: 'Save',
      project: project,
      users: this.users
    }
    this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '700px',
      disableClose: true,
      data: data
    });
  }

  selectProject(project: Project): void {
    console.log(project);
  }
}
