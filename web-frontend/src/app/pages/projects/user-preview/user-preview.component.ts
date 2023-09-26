import { Component, Input } from '@angular/core';
import { Avatar, User } from "../../../rest-api";
import { SettingsService } from "../../../settings.service";

@Component({
  selector: 'app-user-preview',
  templateUrl: './user-preview.component.html',
  styleUrls: ['./user-preview.component.scss']
})
export class UserPreviewComponent {
  @Input()
  set user(user: User) {
    this._user = user;
    this.iconUrl = this.settings.avatars.find(a => a.id === user?.profile.avatar)?.image;
    this.color = user?.profile?.color;
    this.tooltip = user?.username || '';
    this.avatar = this.settings.avatars.find(a => a.id === user?.profile.avatar);
    if (user?.first_name) {
      this.initials = user?.first_name[0];
      this.tooltip += ` (${user?.first_name}`;
      if (user?.last_name) {
        this.initials += user?.last_name[0];
        this.tooltip += ` ${user?.last_name}`;
      }
      this.tooltip += ')';
    }
    else {
      this.initials = user?.username[0];
    }
  }

  protected _user?: User;
  protected avatar?: Avatar;
  protected tooltip = '';
  protected initials?: string;
  protected iconUrl?: string;
  protected color: string = 'black';
  @Input() size = 40;
  @Input() borderWidth = '2px';

  constructor(private settings: SettingsService) {}
}
