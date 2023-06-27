import { AfterViewInit, ChangeDetectorRef, Component, ElementRef, Input, OnDestroy, ViewChild } from '@angular/core';
import { RestService, ScenarioLogEntry } from "../../rest-api";
import { UserSettingsService } from "../../user-settings.service";
import { environment } from "../../../environments/environment";
import { Subscription } from "rxjs";

@Component({
  selector: 'app-scenario-log',
  templateUrl: './scenario-log.component.html',
  styleUrls: ['./scenario-log.component.scss']
})
export class ScenarioLogComponent implements OnDestroy, AfterViewInit {
  @Input() height: string = '200px';
  @Input() fetchOldLogs: boolean = true;
  @ViewChild('log') logEl!: ElementRef;
  entries: ScenarioLogEntry[] = [];
  private subs: Subscription[] = [];

  constructor(private rest: RestService, private settings: UserSettingsService, private cdref: ChangeDetectorRef) {
  }

  ngAfterViewInit(): void {
    this.subs.push(this.settings.onScenarioLogMessage.subscribe(
      entry => this.addLogEntry(entry)));
    this.subs.push(this.settings.activeScenario$.subscribe( scenario => {
      this.entries = [];
      if (this.fetchOldLogs)
        this.fetchLogs();
    }));
    if (this.fetchOldLogs)
      this.fetchLogs();
  }

  fetchLogs() {
    this.cdref.detectChanges();
    this.scrollToBottom(true);
  }

  addLogEntry(entry: ScenarioLogEntry, options?: { intermediateDots?: boolean }): void {
    const lastEntry = this.entries[this.entries.length - 1];
    // then skip
    if (environment.loglevel === 'INFO' && entry.level === 'DEBUG') {
      // show debug messages that are skipped in info level as a dotted progress indicator in log
      if (options?.intermediateDots) {
        if (lastEntry.level === 'INTER')
          lastEntry.message += '.';
        else
          this.addLogEntry({
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
    if (forced || Math.abs(this.logEl.nativeElement.scrollHeight - this.logEl.nativeElement.scrollTop) < 500)
      this.logEl.nativeElement.scrollTop = this.logEl.nativeElement.scrollHeight;
  }

  ngOnDestroy() {
    this.subs.forEach(sub => sub.unsubscribe());
  }
}
