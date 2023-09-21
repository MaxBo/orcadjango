import { ChangeDetectorRef, Component, Injectable, OnDestroy } from '@angular/core';
import { SettingsService } from "./settings.service";
import { AuthService } from "./auth.service";
import { BehaviorSubject, Subscription } from "rxjs";
import { Router } from "@angular/router";
import { User } from "./rest-api";

@Injectable()
export abstract class PageComponent implements OnDestroy {
  private _isLoading = false;
  isLoading$ = new BehaviorSubject<boolean>(false);
  private loadCount = 0;
  protected subscriptions: Subscription[] = [];

  setLoading(isLoading: boolean) {
    this.loadCount += isLoading? 1: -1;
    const iL = this.loadCount > 0;
    if (iL != this._isLoading){
      this._isLoading = iL;
      this.isLoading$.next(this._isLoading);
    }
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'web-frontend';
  protected user?: User;

  constructor(protected settings: SettingsService, protected auth: AuthService, protected router: Router, private cdRef: ChangeDetectorRef) {
    this.auth.getCurrentUser().subscribe();
  }
}
