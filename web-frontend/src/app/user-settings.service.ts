import { Injectable } from "@angular/core";
import { CookieService } from "ngx-cookie-service";
import { Module, Project, RestService, Scenario, User } from "./rest-api";
import { BehaviorSubject } from "rxjs";
import { AuthService } from "./auth.service";

@Injectable({ providedIn: 'root' })
export class UserSettingsService {
  activeProject$ = new BehaviorSubject<Project | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
  user$ = new BehaviorSubject<User | undefined>(undefined);
  module$ = new BehaviorSubject<string>('');
  modules: Module[] = []

  constructor(private cookies: CookieService, private rest: RestService, private auth: AuthService) {
    this.auth.user$.subscribe(user => {
      if (user) {
        const projectId = this.cookies.get('project');
        if (projectId) {
          this.rest.getProject(Number(projectId)).subscribe(project => {
            this.activeProject$.next(project);
          })
        }
        const scenarioId = this.cookies.get('scenario');
        if (scenarioId) {
          this.rest.getScenario(Number(scenarioId)).subscribe(scenario => {
            this.activeScenario$.next(scenario);
          })
        }
        this.rest.getModules().subscribe(modules => {
          this.module$.next(this.cookies.get('module') || modules.find(mod => mod.default)?.path || '');
          this.modules = modules;
        });
      }
      this.user$.next(user);
    })
  }

  setActiveProject(project: Project | undefined){
    this.cookies.set('project', String(project?.id || ''));
    this.activeProject$.next(project);
  }

  setActiveSenario(scenario: Scenario | undefined){
    this.cookies.set('scenario', String(scenario?.id || ''));
    this.activeScenario$.next(scenario);
  }

  setModule(module: string){
    console.log(module);
    this.cookies.set('module', module);
    this.module$.next(module);
  }
}
