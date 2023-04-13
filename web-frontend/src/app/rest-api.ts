import { environment } from "../environments/environment";
import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";

export interface Project {
  id?: number,
  name: string,
  description: string,
  user?: User,
  code?: string,
  module?: string
}

export interface Scenario {
  id?: number,
  name: string,
  project: number
}

export interface User {
  id: number,
  username: string,
  first_name: string,
  last_name: string
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

  getScenario(id: number): Observable<Scenario> {
    return this.http.get<Scenario>(`${this.URLS.scenarios}${id}/`);
  }

  getProjects(options?: { module: string }): Observable<Project[]> {
    const params: any = options? { module: options.module }: {};
    return this.http.get<Project[]>(this.URLS.projects, { params: params });
  }

  getScenarios(options?: { project: Project }): Observable<Scenario[]> {
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

  createProject(project: Project): Observable<Project>{
    let body: any = {
      name: project.name,
      description: project.description,
      code: project.code,
      user: project.user?.id
    }
    return this.http.post<Project>(this.URLS.projects, body);
  }
}
