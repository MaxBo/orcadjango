import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { Inj, Project, RestService, User } from "../../rest-api";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "./edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { UserSettingsService } from "../../user-settings.service";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";
import { CookieService } from "ngx-cookie-service";
import { PageComponent } from "../../app.component";
import { sortBy } from "../injectables/injectables.component";
import { Moment } from "moment";

@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss']
})
export class ProjectsComponent extends PageComponent implements OnInit{
  protected projects: Project[] = [];
  protected filteredProjects: Project[] = [];
  protected showFilters = false;
  protected viewType: 'list-view' | 'grid-view' = 'grid-view';
  protected sortAscending = true;
  protected sortAttr = 'name'; //'name' | 'code' | 'date';
  protected filterByUsers = false;
  protected filterByCodes = false;
  protected filterByDate = false;
  protected filterUsers: number[] = [];
  protected filterCodes: string[] = [];
  protected filterDate?: Moment;
  protected filterDateOperator: '<' | '>' | '=' = '>'
  @ViewChild('deleteProjectTemplate') deleteProjectTemplate?: TemplateRef<any>;

  constructor(private rest: RestService, private dialog: MatDialog, protected settings: UserSettingsService,
              private cookies: CookieService) {
    super();
  }

  ngOnInit() {
    const viewType = this.cookies.get('project-view-type');
    if (viewType === 'list-view') this.viewType = 'list-view';
    this.settings.module$.subscribe(module => {
      if (!module) {
        this.projects = [];
        this.filteredProjects = [];
        return;
      }
      this.setLoading(true);
      this.rest.getProjects({ module: module?.path || '' }).subscribe(projects => {
        this.projects = projects;
        this.setLoading(false);
        this.filter();
      });
    })
  }

  onCreateProject(): void {
    const user = this.settings.user$.value;
    const initInjectableNames = this.settings.module$.value?.init || [];
    let injectables: Inj[] = initInjectableNames.map(name => this.settings.moduleInjectables.find(inj => inj.name === name)!).filter(i => i !== undefined);
    const data: ProjectEditDialogData = {
      title: 'Create new Project',
      confirmButtonText: 'Create',
      project: {
        name: '',
        description: '',
        user: user?.id,
        injectables: injectables,
        init: []
      }
    }
    const dialogref = this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '1000px',
      disableClose: true,
      data: data
    });
    dialogref.componentInstance.projectConfirmed.subscribe(project => {
      project.module = this.settings.module$.value?.path || '';
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
        dialogRef.close();
        const idx = this.projects.indexOf(project);
        if (idx > -1) {
          this.projects.splice(idx, 1);
        }
        if (project.id === this.settings.activeProject$?.value?.id)
          this.settings.setActiveProject(undefined);
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
      width: '1000px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.projectConfirmed.subscribe((edited) => {
      this.rest.patchProject(project, { name: edited.name, description: edited.description, user: edited.user, code: edited.code, injectables: edited.injectables }).subscribe(patched => {
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

  changeView(viewType: 'list-view' | 'grid-view'): void {
    this.viewType = viewType;
    this.cookies.set('project-view-type', viewType);
  }

  sortProjects(): void {
    this.projects = sortBy(this.projects, this.sortAttr, {reverse: !this.sortAscending})
  }

  filter(): void {
    this.filteredProjects = this.projects;
    if (this.filterByUsers && this.filterUsers.length) {
      this.filteredProjects = this.filteredProjects.filter(p => (p.user !== undefined) && this.filterUsers.includes(p.user)) || [];
    }
    if (this.filterByCodes && this.filterCodes.length) {
      this.filteredProjects = this.filteredProjects.filter(p => p.code && this.filterCodes.includes(p.code)) || [];
    }
    if (this.filterByDate && this.filterDate) {
      const date = this.filterDate.toDate();
      date.setHours(0,0,0,0);
      this.filteredProjects = this.filteredProjects.filter(p =>
        p.date && (
        (this.filterDateOperator === '>')? p.date.valueOf() > date.valueOf():
          (this.filterDateOperator === '<')? p.date.valueOf() < date.valueOf():
            p.date.valueOf() === date.valueOf())
      );
    }
  }

  getUniqueValues(objects: any[], attribute: string): any[] {
    return Array.from(new Set(objects.map(o => o[attribute])));
  }
}
