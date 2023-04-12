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

export interface User {
  id: number,
  username: string,
  first_name: string,
  last_name: string
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
    users: `${ environment.apiPath }/users/`,
    currentUser: `${ environment.apiPath }/users/current/`,
    login: `${ environment.apiPath }/login/`,
    logout: `${ environment.apiPath }/logout/`,
    token: `${ environment.apiPath }/token/`,
    refreshToken: `${ environment.apiPath }/token/refresh/`,
  }
  constructor(private http: HttpClient) { }

  private post<Type>(url: string, body: any) {
    // const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
    return this.http.post<Type>(url, body);
  }

  getProjects(): Observable<Project[]> {
    return this.http.get<Project[]>(this.URLS.projects);
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
