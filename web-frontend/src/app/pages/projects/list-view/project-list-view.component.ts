import { Component } from '@angular/core';
import { ProjectGridViewComponent } from "../grid-view/project-grid-view.component";

@Component({
  selector: 'app-project-list-view',
  templateUrl: './project-list-view.component.html',
  styleUrls: ['./project-list-view.component.scss']
})
export class ProjectListViewComponent extends ProjectGridViewComponent {
  getUserName(userId: number): string {
    const user = this.settings.users.find(user => user.id === userId);
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
