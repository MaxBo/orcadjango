import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { formatProject, Inj, Project, RestService, User } from "../../rest-api";
import { ProjectEditDialogComponent, ProjectEditDialogData } from "./edit/project-edit.component";
import { MatDialog } from "@angular/material/dialog";
import { SettingsService } from "../../settings.service";
import { ConfirmDialogComponent } from "../../elements/confirm-dialog/confirm-dialog.component";
import { CookieService } from "ngx-cookie-service";
import { PageComponent } from "../../app.component";
import { sortBy } from "../injectables/injectables.component";
import { Moment } from "moment";
import * as moment from "moment";

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
  protected sortDescending = false;
  protected sortAttr = 'name'; //'name' | 'code' | 'date';
  protected filterByUsers = false;
  protected filterByCodes = false;
  protected filterByDate = false;
  protected filterArchive = false;
  protected filterUsers: number[] = [];
  protected filterCodes: string[] = [];
  protected filterDate?: Moment;
  protected filterDateOperator: '<' | '>' | '=' = '>';
  @ViewChild('deleteProjectTemplate') deleteProjectTemplate?: TemplateRef<any>;

  constructor(private rest: RestService, private dialog: MatDialog, protected settings: SettingsService,
              private cookies: CookieService) {
    super();
  }

  ngOnInit() {
    const viewType = this.cookies.get('project-view-type');
    if (viewType === 'list-view')
      this.viewType = 'list-view';
    this.sortAttr = this.cookies.get('project-sortAttr') || 'name';
    this.sortDescending = this.cookies.get('project-sortDescending') === 'true';
    this.showFilters = this.cookies.get('project-showFilters') === 'true';
    this.filterByUsers = this.cookies.get('project-filterByUsers') === 'true';
    this.filterByDate = this.cookies.get('project-filterByDate') === 'true';
    this.filterByCodes = this.cookies.get('project-filterByCodes') === 'true';
    this.filterArchive = this.cookies.get('project-filterArchive') === 'true';
    // @ts-ignore
    this.filterDateOperator = this.cookies.get('project-filterDateOperator') || '>';
    const cookieUsers = this.cookies.get('project-filterUsers');
    this.filterUsers = cookieUsers? cookieUsers.split(',').map(u => Number(u)): [];
    const cookieCodes = this.cookies.get('project-filterCodes');
    this.filterCodes = cookieCodes? cookieCodes.split(','): [];
    const cookiesDate = this.cookies.get('project-filterDate');
    if (cookiesDate) this.filterDate = moment(cookiesDate, 'YYYY-MM-DD');
    this.subscriptions.push(this.settings.module$.subscribe(module => {
      if (!module) {
        this.projects = [];
        this.filteredProjects = [];
        return;
      }
      this.setLoading(true);
      this.rest.getProjects({ module: module }).subscribe(projects => {
        this.projects = projects;
        this.setLoading(false);
        this.filter();
      });
    }));
  }

  onCreateProject(): void {
    const user = this.settings.user$.value;
    const initInjectableNames = this.settings.module$.value?.init_injectables || [];
    let injectables: Inj[] = initInjectableNames.map(name => this.settings.moduleInjectables.find(inj => inj.name === name)!).filter(i => i !== undefined);
    const data: ProjectEditDialogData = {
      title: 'Create new Project',
      confirmButtonText: 'Create',
      project: {
        name: '',
        description: '',
        user: user?.id,
        injectables: injectables,
        init: [],
        scenario_count: 0
      }
    }
    const dialogRef = this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '1000px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.projectConfirmed.subscribe(project => {
      dialogRef.componentInstance.setLoading(true);
      project.module = this.settings.module$.value?.path || '';
      this.rest.createProject(project).subscribe(created => {
        dialogRef.close();
        formatProject(created, { previewInjName: this.settings.module$.value?.preview_injectable });
        this.projects.push(created);
        this.settings.setActiveProject(created);
        this.filter();
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
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
      dialogRef.componentInstance.setLoading(true);
      this.rest.deleteProject(project).subscribe(() => {
        dialogRef.close();
        const idx = this.projects.indexOf(project);
        if (idx > -1) {
          this.projects.splice(idx, 1);
        }
        if (project.id === this.settings.activeProject$?.value?.id)
          this.settings.setActiveProject(undefined);
        this.filter();
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
      })
    })
  }

  editProject(project: Project): void {
    const data: ProjectEditDialogData = {
      title: 'Edit Project',
      confirmButtonText: 'Save',
      project: project,
      showDate: true
    }
    const dialogRef = this.dialog.open(ProjectEditDialogComponent, {
      panelClass: 'absolute',
      width: '1000px',
      disableClose: true,
      data: data
    });
    dialogRef.componentInstance.projectConfirmed.subscribe((edited) => {
      dialogRef.componentInstance.setLoading(true);
      let data: any = {
        name: edited.name,
        description: edited.description,
        user: edited.user,
        code: edited.code,
        injectables: edited.injectables,
        created: edited.created
      };
      if (edited.date)
        data.created = moment(edited.date).format('YYYY-MM-DD');
      this.rest.patchProject(project, data).subscribe(patched => {
        dialogRef.close();
        Object.assign(project, patched);
        formatProject(project, { previewInjName: this.settings.module$.value?.preview_injectable });
        this.filter();
      }, error => {
        dialogRef.componentInstance.setErrors(error.error);
        dialogRef.componentInstance.setLoading(false);
      });
    })
  }

  archiveProject(project: Project, archive: boolean): void {
    this.rest.patchProject(project, { archived: archive }).subscribe(patched => {
      project.archived = archive;
      this.filter();
    });
  }

  selectProject(project: Project): void {
    this.settings.setActiveProject(project);
  }

  changeView(viewType: 'list-view' | 'grid-view'): void {
    this.viewType = viewType;
    this.cookies.set('project-view-type', viewType);
  }

  setSortAttr(attr: string): void {
    this.sortAttr = attr;
    this.cookies.set('project-sortAttr', this.sortAttr);
    this.sortProjects();
  }

  setSortDescending(descending: boolean): void {
    this.sortDescending = descending;
    this.cookies.set('project-sortDescending', descending.toString());
    this.sortProjects();
  }

  setShowFilters(showFilters: boolean): void {
    this.showFilters = showFilters;
    this.cookies.set('project-showFilters', showFilters.toString());
  }

  setFilterByUsers(filterByUsers: boolean): void {
    this.filterByUsers = filterByUsers;
    this.cookies.set('project-filterByUsers', filterByUsers.toString());
    this.filter();
  }

  setFilterByDate(filterByDate: boolean): void {
    this.filterByDate = filterByDate;
    this.cookies.set('project-filterByDate', filterByDate.toString());
    this.filter();
  }

  setFilterByCodes(filterByCodes: boolean): void {
    this.filterByCodes = filterByCodes;
    this.cookies.set('project-filterByCodes', filterByCodes.toString());
    this.filter();
  }

  setFilterArchive(filterArchive: boolean): void {
    this.filterArchive = filterArchive;
    this.cookies.set('project-filterArchive', filterArchive.toString());
    this.filter();
  }

  setNextFilterOperator(): void {
    this.filterDateOperator = (this.filterDateOperator === '=')? '>' : (this.filterDateOperator === '>')? '<': '=';
    this.cookies.set('project-filterDateOperator', this.filterDateOperator.toString());
    this.filter();
  }

  setFilterUsers(users: number[]): void {
    this.filterUsers = users;
    this.cookies.set('project-filterUsers', users.join(','));
    this.filter();
  }

  setFilterCodes(codes: string[]): void {
    this.filterCodes = codes;
    this.cookies.set('project-filterCodes', codes.join(','));
    this.filter();
  }

  setFilterDate(): void {
    const dateString = this.filterDate?.format('YYYY-MM-DD');
    this.cookies.set('project-filterDate', dateString || '');
    this.filter();
  }

  sortProjects(): void {
    this.isLoading$.next(true);
    this.filteredProjects = sortBy(this.filteredProjects, this.sortAttr, { reverse: this.sortDescending, lowerCase: this.sortAttr === 'name' });
    this.isLoading$.next(false);
  }

  filter(): void {
    this.isLoading$.next(true);
    this.filteredProjects = this.projects.filter(p => p.archived === this.filterArchive);
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
        (p.date === undefined && this.filterDateOperator === '<') || ( // assume undefined dates to be older as any date
          p.date && (
          (this.filterDateOperator === '<')? (p.date.valueOf() < date.valueOf()):
            (this.filterDateOperator === '>')? p.date.valueOf() > date.valueOf():
            p.date.valueOf() === date.valueOf()
          )
      ));
    }
    this.sortProjects();
  }

  getUniqueValues(objects: any[], attribute: string): any[] {
    return Array.from(new Set(objects.filter(o => !!o[attribute]).map(o => o[attribute])));
  }
}
