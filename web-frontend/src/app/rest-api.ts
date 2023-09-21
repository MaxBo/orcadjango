import { environment } from "../environments/environment";
import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";
import * as moment from "moment/moment";
import { Moment } from "moment";

export interface Avatar {
  id: number,
  name: string,
  image: string,
  users: number[]
}

interface Profile {
  color: string,
  avatar: number
}

export interface User {
  id: number,
  username: string,
  first_name: string,
  last_name: string,
  is_superuser: boolean,
  profile: Profile
}

export interface SiteSettings {
  title: string,
  contact_mail: string,
  logo: string,
  primary_color: string,
  secondary_color: string,
  favicon: string,
  scenario_running_img: string,
  scenario_running_icon: string,
  scenario_success_img: string,
  scenario_success_icon: string,
  scenario_failed_img: string,
  scenario_failed_icon: string,
  welcome_background_img: string,
  projects_background_img: string,
  scenarios_background_img: string,
  injectables_background_img: string,
  steps_background_img: string,
  welcome_text: string
}

export interface Project {
  id?: number,
  name: string,
  description: string,
  init: string[],
  injectables: Inj[],
  previewInjectable?: Inj;
  user?: number,
  code?: string,
  module?: string,
  archived?: boolean,
  created?: string,
  date?: Moment,
  scenario_count: number
}

interface ScenarioRun {
  success?: boolean,
  started?: string,
  finished?: string
}

export interface Scenario {
  id?: number,
  name: string,
  is_running?: boolean,
  project?: number,
  description: string,
  last_run?: ScenarioRun
}

export interface Inj {
  name: string,
  value: any,
  description?: string,
  group?: string,
  datatype: 'str' | 'int' | 'list' | 'float' | 'bool' | 'dict' | 'geometry',
  multi?: boolean,
  choices?: any[] | Record<string, string>
}

export interface ScenarioInjectable extends Inj {
  id: number,
  scenario: number,
  parents?: number[],
  parentInjectables?: (ScenarioInjectable | undefined)[],
  editable?: boolean
}

export interface Module {
  name: string,
  title: string,
  path: string,
  description: string,
  init_injectables: string[],
  default: boolean,
  preview_injectable?: string,
  info_html: string
}

export interface Step {
  name: string,
  order: number,
  title?: string,
  description?: string,
  group?: string,
  required?: string[],
  injectables?: string[]
}

export interface ScenarioStep extends Step {
  id: number,
  scenario: number,
  success: boolean,
  active?: boolean,
  started?: string,
  finished?: string
}

export interface  ScenarioLogEntry {
  level: 'ERROR' | 'INFO' | 'DEBUG' | 'INTER',
  timestamp?: string,
  message: string,
  scenario?: { success?: boolean, finished?: boolean }
}

export function formatProject(project: Project, options?: { previewInjName?: string}) {
  if (options?.previewInjName)
    project.previewInjectable = project.injectables.find(inj => inj.name === options.previewInjName);
  if (project.created) {
    project.date = moment(project.created, 'YYYY-MM-DD');
    project.created = moment(project.date).format('DD.MM.YYYY');
  }
}

@Injectable({
  providedIn: 'root'
})
/**
 * service for querying the backend API for specific resources (POST and GET)
 *
 */
export class RestService {
  public readonly URLS = {
    projects: `${ environment.apiPath }/projects/`,
    scenarios: `${ environment.apiPath }/scenarios/`,
    scenarioInjectables: `${ environment.apiPath }/scenarios/{scenarioId}/injectables/`,
    scenarioSteps: `${ environment.apiPath }/scenarios/{scenarioId}/steps/`,
    scenarioLogs: `${ environment.apiPath }/scenarios/{scenarioId}/logs/`,
    sitesettings: `${ environment.apiPath }/settings/`,
    users: `${ environment.apiPath }/users/`,
    avatars: `${ environment.apiPath }/avatars/`,
    currentUser: `${ environment.apiPath }/users/current/`,
    login: `${ environment.apiPath }/login/`,
    logout: `${ environment.apiPath }/logout/`,
    token: `${ environment.apiPath }/token/`,
    refreshToken: `${ environment.apiPath }/token/refresh/`,
    modules: `${ environment.apiPath }/modules/`,
    injectables: `${ environment.apiPath }/modules/{module}/injectables/`,
    availableSteps: `${ environment.apiPath }/modules/{module}/steps/`,
  }
  constructor(private http: HttpClient) { }

  private post<Type>(url: string, body: any) {
    // const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
    return this.http.post<Type>(url, body);
  }

  getProject(id: number, options?: { module?: Module }): Observable<Project> {
    return this.http.get<Project>(`${this.URLS.projects}${id}/`).pipe(map(project => {
      formatProject(project, { previewInjName: options?.module?.preview_injectable });
      return project;
    }))
  }

  createProject(project: Project): Observable<Project>{
    let body: any = {
      name: project.name,
      description: project.description,
      code: project.code,
      user: project.user,
      module: project.module,
      injectables: project.injectables
    }
    return this.http.post<Project>(this.URLS.projects, body);
  }

  deleteProject(project: Project): Observable<Project> {
    return this.http.delete<Project>(`${this.URLS.projects}${project.id}/`);
  }

  patchProject(project: Project, data: any): Observable<Project> {
    return this.http.patch<Project>(`${this.URLS.projects}${project.id}/`, data);
  }

  getScenario(id: number): Observable<Scenario> {
    return this.http.get<Scenario>(`${this.URLS.scenarios}${id}/`);
  }

  createScenario(scenario: Scenario): Observable<Project>{
    let body: any = {
      name: scenario.name,
      description: scenario.description,
      project: scenario.project
    }
    return this.http.post<Project>(this.URLS.scenarios, body);
  }

  deleteScenario(scenario: Scenario): Observable<Project> {
    return this.http.delete<Project>(`${this.URLS.scenarios}${scenario.id}/`);
  }

  patchScenario(scenario: Scenario, data: any): Observable<Project> {
    return this.http.patch<Project>(`${this.URLS.scenarios}${scenario.id}/`, data);
  }

  synchronizeInjectables(scenario: Scenario): Observable<ScenarioInjectable[]> {
    return this.http.post<ScenarioInjectable[]>(`${this.URLS.scenarios}${scenario.id}/synch/`, {});
  }

  resetInjectables(scenario: Scenario): Observable<ScenarioInjectable[]> {
    return this.http.post<ScenarioInjectable[]>(`${this.URLS.scenarios}${scenario.id}/reset/`, {});
  }

  getProjects(options?: { module: Module }): Observable<Project[]> {
    const params: any = options? { module: options.module.path }: {};
    return this.http.get<Project[]>(this.URLS.projects, { params: params }).pipe(map(projects => {
      // ToDo: determine which injectables serve as previews via API somehow
      projects.forEach(project => formatProject(project, { previewInjName: options?.module.preview_injectable }));
      return projects;
    }));
  }

  getScenarios(options?: { project?: Project }): Observable<Scenario[]> {
    const params: any = options?.project? { project: options.project.id }: {};
    return this.http.get<Scenario[]>(this.URLS.scenarios, { params: params });
  }

  getModules(): Observable<Module[]> {
    return this.http.get<Module[]>(this.URLS.modules);
  }

  getInjectables(module: string): Observable<Inj[]> {
    const url = this.URLS.injectables.replace('{module}', module);
    return this.http.get<Inj[]>(url);
  }

  login(username: string, password: string): Observable<User> {
    return this.post<User>(this.URLS.login, { username: username, password: password });
  }

  getCurrentUser(): Observable<User>{
    return this.http.get<User>(this.URLS.currentUser);
  }

  getUsers(): Observable<User[]>{
    return this.http.get<User[]>(this.URLS.users);
  }

  getAvatars(): Observable<Avatar[]>{
    return this.http.get<Avatar[]>(this.URLS.avatars);
  }

  getSiteSettings(): Observable<SiteSettings>{
    return this.http.get<SiteSettings[]>(this.URLS.sitesettings).pipe(map(settings => settings[0]));
  }

  getScenarioInjectables(scenario: Scenario): Observable<ScenarioInjectable[]> {
    const url = this.URLS.scenarioInjectables.replace('{scenarioId}', scenario.id!.toString());
    return this.http.get<ScenarioInjectable[]>(url).pipe(map(injectables => {
      injectables.map(inj => {
        inj.parentInjectables = (inj.parents || []).map(parentId => injectables.find(inj => inj.id === parentId));
      })
      return injectables;
    }));
  }

  getScenarioInjectable(id: number, scenario: Scenario): Observable<ScenarioInjectable> {
    const injUrl = this.URLS.scenarioInjectables.replace('{scenarioId}', scenario.id!.toString());
    return this.http.get<ScenarioInjectable>(`${injUrl}${id}/`);
  }

  patchUser(id: number, data: any): Observable<User> {
    return this.http.patch<User>(`${this.URLS.users}${id}/`, data);
  }

  patchScenarioInjectable(injectable: ScenarioInjectable, value: any): Observable<ScenarioInjectable> {
    const injUrl = this.URLS.scenarioInjectables.replace('{scenarioId}', injectable.scenario.toString());
    return this.http.patch<ScenarioInjectable>(`${injUrl}${injectable.id}/`, {value: value});
  }

  getAvailableSteps(module: string): Observable<Step[]> {
    const url = this.URLS.availableSteps.replace('{module}', module);
    return this.http.get<Step[]>(url);
  }

  getScenarioSteps(scenario: Scenario): Observable<ScenarioStep[]> {
    const url = this.URLS.scenarioSteps.replace('{scenarioId}', scenario.id!.toString());
    return this.http.get<ScenarioStep[]>(url);
  }

  addScenarioStep(stepName: string, order: number, scenario: Scenario): Observable<ScenarioStep> {
    const url = this.URLS.scenarioSteps.replace('{scenarioId}', scenario.id!.toString());
    return this.http.post<ScenarioStep>(url, { name: stepName, order: order });
  }

  deleteScenarioStep(step: ScenarioStep): Observable<Project> {
    const url = this.URLS.scenarioSteps.replace('{scenarioId}', step.scenario.toString());
    return this.http.delete<Project>(`${url}${step.id}/`);
  }

  patchScenarioStep(step: ScenarioStep, options?:{ active?: boolean, order?: number }): Observable<ScenarioStep>{
    const url = this.URLS.scenarioSteps.replace('{scenarioId}', step.scenario.toString());
    return this.http.patch<ScenarioStep>(`${url}${step.id}/`, options);
  }

  getScenarioLogs(scenario: Scenario): Observable<ScenarioLogEntry[]> {
    const url = this.URLS.scenarioLogs.replace('{scenarioId}', scenario.id!.toString());
    return this.http.get<ScenarioLogEntry[]>(url);
  }

  startRun(scenario: Scenario) {
    const url = this.URLS.scenarios;
    return this.http.post(`${url}${scenario.id}/run/`,{});
  }

  abortRun(scenario: Scenario) {
    const url = this.URLS.scenarios;
    return this.http.post(`${url}${scenario.id}/abort/`,{});
  }
}
