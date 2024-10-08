import { EventEmitter, Injectable } from "@angular/core";
import { CookieService } from "ngx-cookie-service";
import { Avatar, Inj, Module, Project, RestService, Scenario, ScenarioLogEntry, SiteSettings, User } from "./rest-api";
import { BehaviorSubject } from "rxjs";
import { AuthService } from "./auth.service";
import { environment } from "../environments/environment";
import { Router } from "@angular/router";
import { MaterialCssVarsService } from "angular-material-css-vars";

@Injectable({ providedIn: 'root' })
export class SettingsService {
  activeProject$ = new BehaviorSubject<Project | undefined>(undefined);
  activeScenario$ = new BehaviorSubject<Scenario | undefined>(undefined);
  logLevel$ = new BehaviorSubject<string>('INFO');
  user$ = new BehaviorSubject<User | undefined>(undefined);
  module$ = new BehaviorSubject<Module | undefined>(undefined);
  moduleInjectables: Inj[] = [];
  users: User[] = [];
  avatars: Avatar[] = [];
  host: string = '';
  modules: Module[] = [];
  isLoading$ = new BehaviorSubject<boolean>(false);
  private scenarioLogSocket?: WebSocket;
  onScenarioLogMessage = new EventEmitter<ScenarioLogEntry>;
  siteSettings?: SiteSettings;
  onStepStatusChange = new EventEmitter<{
    step: string, success: boolean, finished: boolean, started: boolean, timestamp: string}>;
  runFinished = new EventEmitter<{success: boolean}>;
  private readonly wsURL: string;
  private retries = 0;

  constructor(private cookies: CookieService, private rest: RestService, private auth: AuthService,
              private router: Router, private materialCssVarsService: MaterialCssVarsService) {
    let logLevel = this.cookies.get('loglevel') || 'INFO';
    this.logLevel$.next(logLevel);
    this.activeScenario$.subscribe(scenario => {
      this.disconnect();
      this.connect();
    });
    this.host = environment.backend? environment.backend: window.location.origin;
    const strippedHost = environment.backend? environment.backend.replace('http://', ''): window.location.hostname;
    this.wsURL = `${(environment.production && strippedHost.indexOf('localhost') === -1)? 'wss:': 'ws:'}//${strippedHost}/ws/scenariolog/`;
    this.auth.user$.subscribe(user => {
      if (user) {
        this.isLoading$.next(true);
        this.rest.getUsers().subscribe(users => {
          this.users = users;
          this.rest.getAvatars().subscribe(avatars => {
            this.avatars = avatars;
            this.user$.next(user);
            this.rest.getModules().subscribe(modules => {
              this.modules = modules;
              const modName = this.cookies.get('module');
              const module = modules.find(mod => mod.name === modName) || modules.find(mod => mod.default);
              if (module)
                this.module$.next(module);
              const projectId = this.cookies.get('project');
              if (projectId) {
                this.rest.getProject(Number(projectId), { module: module }).subscribe(project => {
                  this.activeProject$.next(project);
                })
              }
              const scenarioId = this.cookies.get('scenario');
              if (scenarioId) {
                this.rest.getScenario(Number(scenarioId)).subscribe(scenario => {
                  this.activeScenario$.next(scenario);
                })
              }
              this.isLoading$.next(false);
            });
          });
        });
      }
      else {
        this.user$.next(undefined);
      }
    })
    this.module$.subscribe(module => {
      if (!module) {
        this.moduleInjectables = [];
        return;
      }
      this.rest.getInjectables(module.name).subscribe(injectables => this.moduleInjectables = injectables);
    })
  }

  load(): void {
    this.rest.getSiteSettings().subscribe(settings => {
      this.siteSettings = settings;
      this.setColor({ primary: settings.primary_color, secondary: settings.secondary_color })
    });
  }

  setColor(colors: {primary?: string, secondary?: string, warn?: string}) {
    if (colors.primary) this.materialCssVarsService.setPrimaryColor(colors.primary);
    if (colors.secondary) this.materialCssVarsService.setAccentColor(colors.secondary);
    if (colors.warn) this.materialCssVarsService.setWarnColor(colors.warn);
  }

  setActiveProject(project: Project | undefined){
    this.cookies.set('project', String(project?.id || ''));
    this.activeProject$.next(project);
    this.setActiveSenario(undefined);
  }

  setActiveSenario(scenario: Scenario | undefined){
    this.cookies.set('scenario', String(scenario?.id || ''));
    this.activeScenario$.next(scenario);
  }

  setModule(moduleName: string){
    this.cookies.set('module', moduleName);
    const module = this.modules.find(mod => mod.name === moduleName);
    this.setActiveProject(undefined);
    this.module$.next(module);
    this.router.navigateByUrl('/projects');
  }

  private disconnect(): void {
    if (!this.scenarioLogSocket) return;
    this.scenarioLogSocket.onclose = e => {};
    this.scenarioLogSocket.close();
    this.retries = 0;
  }

  private connect(): void {
    if (this.activeScenario$.value === undefined) return;
    if (this.retries > 10) return;
    this.scenarioLogSocket = new WebSocket(`${this.wsURL}${this.activeScenario$.value.id}/`);
    this.scenarioLogSocket.onopen = e => this.retries = 0;
    this.scenarioLogSocket.onmessage = e => {
      const logEntry = JSON.parse(e.data);
      if (logEntry.status){
        const status = logEntry.status;
        // step status update
        if (logEntry.status.step) {
          this.onStepStatusChange.emit({
            step: status.step,
            finished: status.finished,
            success: status.success,
            started: status.started,
            timestamp: logEntry.timestamp
          })
        }
        // scenario status update
        else if (this.activeScenario$.value) {
          const scenario = this.activeScenario$.value;
          if (!scenario.last_run) {
            scenario.last_run = {}
          }
          if (status.started) {
            scenario.last_run.started = logEntry.timestamp;
            scenario.is_running = true;
          }
          if (status.finished) {
            scenario.last_run.finished = logEntry.timestamp;
            scenario.is_running = false;
            this.runFinished.emit({success: status.success})
          }
          if (status.success !== undefined) {
            scenario.last_run.success = status.success;
          }
        }
      }
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

  setLogLevel(level: string): void {
    this.logLevel$.next(level);
    this.cookies.set('loglevel', level);
  }
}
