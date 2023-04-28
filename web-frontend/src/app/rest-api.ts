import { environment } from "../environments/environment";
import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

export interface User {
  id: number,
  username: string,
  first_name: string,
  last_name: string
}

export interface Project {
  id?: number,
  name: string,
  description: string,
  user?: number,
  code?: string,
  module?: string,
  archived?: boolean,
  created?: string
}

export interface Scenario {
  id?: number,
  name: string,
  project?: number,
  description: string
}

export interface Inj {
  id: number,
  name: string,
  scenario: number,
  value: any,
  description: string,
  group: string,
  datatype: string,
  parents: number[],
  parentInjectables?: (Inj | undefined)[],
  editable: boolean
}

export interface Module {
  name: string,
  path: string,
  description: string,
  init: string[],
  default: boolean,
  data?: {
    name?: string,
    url?: string,
    href?: string,
    text?: string[]
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
    injectables: `${ environment.apiPath }/scenarios/{scenarioId}/injectables/`,
    users: `${ environment.apiPath }/users/`,
    currentUser: `${ environment.apiPath }/users/current/`,
    login: `${ environment.apiPath }/login/`,
    logout: `${ environment.apiPath }/logout/`,
    token: `${ environment.apiPath }/token/`,
    refreshToken: `${ environment.apiPath }/token/refresh/`,
    modules: `${ environment.apiPath }/modules/`
  }
  constructor(private http: HttpClient) { }

  private post<Type>(url: string, body: any) {
    // const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
    return this.http.post<Type>(url, body);
  }

  getProject(id: number): Observable<Project> {
    return this.http.get<Project>(`${this.URLS.projects}${id}/`);
  }

  createProject(project: Project): Observable<Project>{
    let body: any = {
      name: project.name,
      description: project.description,
      code: project.code,
      user: project.user,
      module: project.module
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

  getProjects(options?: { module: string }): Observable<Project[]> {
    const params: any = options? { module: options.module }: {};
    return this.http.get<Project[]>(this.URLS.projects, { params: params });
  }

  getScenarios(options?: { project?: Project }): Observable<Scenario[]> {
    const params: any = options?.project? { project: options.project.id }: {};
    return this.http.get<Scenario[]>(this.URLS.scenarios, { params: params });
  }

  getModules(): Observable<Module[]> {
    return this.http.get<Module[]>(this.URLS.modules);
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

  getInjectables(scenario: Scenario): Observable<Inj[]> {
    const url = this.URLS.injectables.replace('{scenarioId}', scenario.id!.toString());
    return this.http.get<Inj[]>(url).pipe(map( injectables => {
      injectables.map(inj => {
        inj.parentInjectables = inj.parents.map(parentId => injectables.find(inj => inj.id === parentId));
      })
      console.log(injectables);
      return injectables;
    }));
  }

  resetInjectables(scenario: Scenario): Observable<Inj[]> {
    const injUrl = this.URLS.injectables.replace('{scenarioId}', scenario.id!.toString());
    return this.http.post<Inj[]>(`${injUrl}reset/`, {});
  }

  patchInjectable(injectable: Inj, value: any): Observable<Inj> {
    const injUrl = this.URLS.injectables.replace('{scenarioId}', injectable.scenario.toString());
    return this.http.patch<Inj>(`${injUrl}${injectable.id}/`, {value: value});
  }
}