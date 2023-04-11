import { environment } from "../environments/environment";
import { Injectable } from "@angular/core";
import { HttpClient, HttpHeaders, HttpResponse } from "@angular/common/http";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";

export interface Project {
  id: number,
  name: string,
  description: string,
  module?: string
}

export interface User {
  id: number,
  username: string,
  first_name: string,
  last_name: string
}

export interface Session {
  is_authenticated: boolean,
  user?: User
}

@Injectable({
  providedIn: 'root'
})
/**
 * service for querying the backend API for specific resources (POST and GET)
 *
 */
export class RestService {
  private csrfToken?: string;
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

}
