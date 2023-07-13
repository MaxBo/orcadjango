import { Component, Input } from '@angular/core';
import { User } from "../../../rest-api";

@Component({
  selector: 'app-user-preview',
  templateUrl: './user-preview.component.html',
  styleUrls: ['./user-preview.component.scss']
})
export class UserPreviewComponent {
  @Input()
  set user(user: User) {
    this._user = user;
    this.iconUrl = user.profile.icon;
    this.color = user.profile.color;
    if (user.first_name) {
      this.initials = user.first_name[0];
      if (user.last_name) {
        this.initials += user.last_name[0];
      }
    }
    else {
      this.initials = user.username[0];
    }
  }

  protected _user?: User;
  protected initials?: string;
  protected iconUrl?: string;
  protected color: string = 'black';

  constructor() {}
}
