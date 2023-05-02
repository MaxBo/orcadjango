import { Component } from '@angular/core';
import { RestService, ScenarioStep, Step } from "../../rest-api";
import { CdkDragDrop, moveItemInArray } from "@angular/cdk/drag-drop";
import { UserSettingsService } from "../../user-settings.service";
import { sortBy } from "../injectables/injectables.component";

@Component({
  selector: 'app-steps',
  templateUrl: './steps.component.html',
  styleUrls: ['./steps.component.scss']
})
export class StepsComponent {
  availableSteps: Record<string, Step[]> = {};
  scenarioSteps: Step[] = [];

  constructor(private rest: RestService, private settings: UserSettingsService) {
    this.settings.module$.subscribe(module => {
      this.rest.getAvailableSteps(module).subscribe(steps => {
        this.availableSteps = {};
        steps.forEach(inj => {
          if (!this.availableSteps[inj.group])
            this.availableSteps[inj.group] = [];
          this.availableSteps[inj.group].push(inj);
        })
        Object.keys(this.availableSteps).forEach(group =>
          this.availableSteps[group] = sortBy(this.availableSteps[group], 'order')
        );
      });
    })
  }

  drop(event: CdkDragDrop<Step[]>) {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    }
    else
      this.addStep(event.item.data.name, event.currentIndex)
  }

  addStep(stepName: string, position: number) {
    const newStep: ScenarioStep = {
      id: 1,
      name: stepName,
      group: '',
      order: 1,
      description: '',
      required: [],
      scenario: 0
    }
    this.scenarioSteps.splice(position, 0, newStep);
  }
}
