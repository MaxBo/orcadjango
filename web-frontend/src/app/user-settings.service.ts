import { EventEmitter, Injectable } from "@angular/core";
import { CookieService } from "ngx-cookie-service";
import { Inj, Module, Project, RestService, Scenario, ScenarioLogEntry, User } from "./rest-api";
import { BehaviorSubject } from "rxjs";
import { AuthService } from "./auth.service";
import { environment } from "../environments/environment";

@Injectable({ providedIn: 'root' })
export class UserSettingsService {
  activeProject$ = new BehaviorSubject<Project | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
  user$ = new BehaviorSubject<User | undefined>(undefined);
  module$ = new BehaviorSubject<Module | undefined>(undefined);
  moduleInjectables: Inj[] = [];
  users: User[] = [];
  host: string = '';
  modules: Module[] = [];
  scenarioLogSocket?: WebSocket;
  onScenarioLogMessage = new EventEmitter<ScenarioLogEntry>;
  private readonly wsURL: string;
  private retries = 0;

  constructor(private cookies: CookieService, private rest: RestService, private auth: AuthService) {
    this.activeScenario$.subscribe(scenario => {
      this.disconnect();
      this.connect();
    });
    this.host = environment.backend? environment.backend: window.location.origin;
    const strippedHost = environment.backend? environment.backend.replace('http://', ''): window.location.hostname;
    this.wsURL = `${(environment.production && strippedHost.indexOf('localhost') === -1)? 'wss:': 'ws:'}//${strippedHost}/ws/scenariolog/`;
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
          this.modules = modules;
          const modName = this.cookies.get('module');
          const module = modules.find(mod => mod.name === modName) || modules.find(mod => mod.default);
          if (module)
            this.module$.next(module);
        });
        this.rest.getUsers().subscribe(users => {
          this.users = users;
        });
      }
      this.user$.next(user);
    })
    this.module$.subscribe(module => {
      if (!module) {
        this.moduleInjectables = [];
        return;
      }
      this.rest.getInjectables(module.name).subscribe(injectables => this.moduleInjectables = injectables);
    })
  }

  setActiveProject(project: Project | undefined){
    this.cookies.set('project', String(project?.id || ''));
    this.activeProject$.next(project);
    this.activeScenario$.next(undefined);
  }

  setActiveSenario(scenario: Scenario | undefined){
    this.cookies.set('scenario', String(scenario?.id || ''));
    this.activeScenario$.next(scenario);
  }

  setModule(moduleName: string){
    this.cookies.set('module', moduleName);
    const module = this.modules.find(mod => mod.name === moduleName);
    this.module$.next(module);
    if (this.activeProject$.value && this.activeProject$.value.module !== module?.path)
      this.activeProject$.next(undefined);
      this.activeScenario$.next(undefined);
  }

  disconnect(): void {
    if (!this.scenarioLogSocket) return;
    this.scenarioLogSocket.onclose = e => {};
    this.scenarioLogSocket.close();
    this.retries = 0;
  }

  connect(): void {
    if (this.activeScenario$.value === undefined) return;
    if (this.retries > 10) return;
    this.scenarioLogSocket = new WebSocket(`${this.wsURL}${this.activeScenario$.value.id}/`);
    this.scenarioLogSocket.onopen = e => this.retries = 0;
    this.scenarioLogSocket.onmessage = e => {
      console.log(e)
      const logEntry = JSON.parse(e.data);
      console.log(e.data)
      this.onScenarioLogMessage.emit(logEntry);
    }
    this.scenarioLogSocket.onclose = e => {
      this.retries += 1;
      this.connect();
    };
  }

  getUser(id: number | undefined): User | undefined {
    return this.users.find(user => user.id === id);
  }

  getUserName(userId: number | undefined): string {
    const user = this.getUser(userId);
    if (!user)
      return '-';
    let realName = '';
    if (user.first_name)
      realName += user.first_name + ' ';
    if (user.last_name)
      realName += user.last_name + ' ';
    return realName? `${realName}(${user.username})`: user.username;
  }
}
