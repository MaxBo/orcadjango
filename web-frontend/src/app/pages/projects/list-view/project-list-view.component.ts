import { Component } from '@angular/core';
import { ProjectGridViewComponent } from "../grid-view/project-grid-view.component";

@Component({
  selector: 'app-list-view',
  templateUrl: './project-list-view.component.html',
  styleUrls: ['./project-list-view.component.scss']
})
export class ProjectListViewComponent extends ProjectGridViewComponent {}
