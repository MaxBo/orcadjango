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
    session: `${ environment.apiPath }/session/`,
    login: `${ environment.apiPath }/login/`,
    logout: `${ environment.apiPath }/logout/`,
    csrf: `${ environment.apiPath }/csrf/`,
  }
  constructor(private http: HttpClient) { }

  setCsrf(token: string | undefined) {
    this.csrfToken = token;
  }
  //
  // private get<Type>(url: string, options?: any) {
  //   // const headers = new HttpHeaders().set('Content-Type', 'application/json; charset=utf-8');
  //   return this.http.get<Type>(url, options);
  // }

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

  getSession(): Observable<Session>{
    return this.http.get<Session>(this.URLS.session);
  }

  getCsrf(): Observable<HttpResponse<any>>{
    return this.http.get<HttpResponse<any>>(this.URLS.csrf, {observe: 'response'});
      // .pipe(map((res: any) => {
/*      console.log(res.headers.keys())
      return res.headers.get('X-Csrftoken')
    });*/
  }
}
