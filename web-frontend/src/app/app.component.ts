import { Component, Injectable } from '@angular/core';
import { UserSettingsService } from "./user-settings.service";
import { AuthService } from "./auth.service";
import { BehaviorSubject } from "rxjs";
import { Router } from "@angular/router";

@Injectable()
export abstract class PageComponent {
  isLoading$ = new BehaviorSubject<boolean>(false);
  private _isLoading = false;
  private loadCount = 0;

  setLoading(isLoading: boolean) {
    this.loadCount += isLoading? 1: -1;
    const iL = this.loadCount > 0;
    if (iL != this._isLoading){
      this._isLoading = iL;
      this.isLoading$.next(this._isLoading);
    }
  }
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'web-frontend';

  constructor(protected settings: UserSettingsService, protected auth: AuthService, protected router: Router) {
    this.auth.getCurrentUser().subscribe();
  }
}
