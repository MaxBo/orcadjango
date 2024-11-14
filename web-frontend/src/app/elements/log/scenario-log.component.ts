import { AfterViewInit, ChangeDetectorRef, Component, ElementRef, Input, OnDestroy, ViewChild } from '@angular/core';
import { RestService, ScenarioLogEntry } from "../../rest-api";
import { SettingsService } from "../../settings.service";
import { environment } from "../../../environments/environment";
import { Subscription } from "rxjs";
import { CookieService } from "ngx-cookie-service";

@Component({
  selector: 'app-scenario-log',
  templateUrl: './scenario-log.component.html',
  styleUrls: ['./scenario-log.component.scss']
})
export class ScenarioLogComponent implements OnDestroy, AfterViewInit {
  @Input() height: string = '200px';
  @Input() fetchOldLogs: boolean = true;
  @ViewChild('log') logEl!: ElementRef;
  // fetched old logs
  logs: ScenarioLogEntry[] = [];
  // visible log entries
  entries: ScenarioLogEntry[] = [];
  private subscriptions: Subscription[] = [];
  logLevel = 'INFO';

  constructor(private rest: RestService, private settings: SettingsService, private cdref: ChangeDetectorRef,
              protected cookies: CookieService) {
  }

  ngAfterViewInit(): void {
    this.logLevel = this.settings.logLevel$.value;
    this.settings.logLevel$.subscribe(logLevel => {
      this.changeLogLevel(logLevel);
    })
    this.subscriptions.push(this.settings.onScenarioLogMessage.subscribe(
      entry => {
        this.logs.push(entry);
        this.addLogLine(entry);
        this.scrollToBottom();
      }));
    this.subscriptions.push(this.settings.activeScenario$.subscribe( scenario => {
      this.entries = [];
      if (this.fetchOldLogs)
        this.fetchLogs();
    }));
  }

  changeLogLevel(level: string): void {
    this.logLevel = level;
    this.entries = [];
    this.logs.forEach(log => this.addLogLine(log));
    this.scrollToBottom(true);
  }

  fetchLogs() {
    if (!this.settings.activeScenario$.value)
      return;
    this.rest.getScenarioLogs(this.settings.activeScenario$.value, { level: 'DEBUG', nLast: environment.maxLogs }).subscribe(
      logs => {
        this.logs = logs;
        logs.forEach(log => this.addLogLine(log));
        this.scrollToBottom(true);
      });
  }

  addLogLine(entry: ScenarioLogEntry, options?: { intermediateDots?: boolean }): void {
    const lastEntry = this.entries[this.entries.length - 1];
    // then skip
    if (this.logLevel === 'INFO' && entry.level === 'DEBUG') {
      // show debug messages that are skipped in info level as a dotted progress indicator in log
      if (options?.intermediateDots) {
        if (lastEntry.level === 'INTER')
          lastEntry.message += '.';
        else
          this.addLogLine({
            message: '.',
            level: 'INTER'
          })
      }
      // do not add actual debug message
      return;
    }
    // remove eventual intermediate logs
    if (lastEntry?.level === 'INTER')
      this.entries.pop();
    if (!entry.message) return;
    if (entry.timestamp)
      // cut off milliseconds
      entry.timestamp = entry.timestamp.split(',')[0];
    this.entries.push(entry);
  }

  scrollToBottom(forced= true): void {
    // if not forced: scroll automatically to bottom if already close to bottom, do not if manually scrolled up
    if (forced || Math.abs(this.logEl.nativeElement.scrollHeight - this.logEl.nativeElement.scrollTop) < 500) {
      // scrollHeight is updated with delay > force change detection
      this.cdref.detectChanges();
      this.logEl.nativeElement.scrollTo(0, this.logEl.nativeElement.scrollHeight + 100);
    }
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}
