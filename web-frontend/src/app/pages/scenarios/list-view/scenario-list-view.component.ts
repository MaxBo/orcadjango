import { Component } from '@angular/core';
import { ScenarioGridViewComponent } from "../grid-view/scenario-grid-view.component";

@Component({
  selector: 'app-scenario-list-view',
  templateUrl: './scenario-list-view.component.html',
  styleUrls: ['./scenario-list-view.component.scss', '../../projects/list-view/project-list-view.component.scss']
})
export class ScenarioListViewComponent extends ScenarioGridViewComponent{

}
