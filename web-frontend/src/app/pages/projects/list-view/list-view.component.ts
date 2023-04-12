import { Component, Input } from '@angular/core';
import { Project } from "../../../rest-api";

@Component({
  selector: 'app-list-view',
  templateUrl: './list-view.component.html',
  styleUrls: ['./list-view.component.scss']
})
export class ListViewComponent {
  @Input('projects') projects: Project[] = [];


}
