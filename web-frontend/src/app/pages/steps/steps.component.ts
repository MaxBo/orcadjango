import { Component } from '@angular/core';
import { ScenarioInjectable, ScenarioStep, Step } from "../../rest-api";
import { CdkDragDrop, moveItemInArray } from "@angular/cdk/drag-drop";
import { InjectablesComponent, sortBy } from "../injectables/injectables.component";
import { BehaviorSubject, forkJoin, Observable } from "rxjs";

@Component({
  selector: 'app-steps',
  templateUrl: './steps.component.html',
  styleUrls: ['./steps.component.scss']
})
export class StepsComponent extends InjectablesComponent {
  protected availableSteps: Record<string, Step[]> = {};
  // aux array to remember order of groups of available steps
  protected stepGroups: string[] = [];
  protected scenarioSteps: ScenarioStep[] = [];
  protected _scenStepNames: string[] = [];
  stepsLoading$ = new BehaviorSubject<boolean>(false);

  // constructor(private rest: RestService, private settings: UserSettingsService)
  override ngOnInit() {
    this.settings.activeScenario$.subscribe(scenario => {
      this.availableSteps = {};
      this.scenarioSteps = [];
      if (!scenario) return;
      this.setLoading(true);
      this.rest.getScenarioInjectables(scenario).subscribe(injectables => {
        this.injectables = injectables;
        if (!this.settings.module$.value) return;
        this.rest.getAvailableSteps(this.settings.module$.value.name).subscribe(steps => {
          this.availableSteps = {};
          steps = sortBy(steps, 'group');
          steps.forEach(step => {
            // remove number in brackets from group name, that is just used to order the groups
            const group = (step.group || '').replace(/ *\([0-9\w]*\) */g, "");
            if (!this.stepGroups.includes(group)) {
              this.stepGroups.push(group);
              this.availableSteps[group] = [];
            }
            this.availableSteps[group].push(step);
          })
          Object.keys(this.availableSteps).forEach(group => {
              // this.availableSteps[group] = sortBy(this.availableSteps[group], 'name');
              this.availableSteps[group] = sortBy(this.availableSteps[group], 'order');
            }
          );
          this.rest.getScenarioSteps(scenario).subscribe(steps => {
            this.scenarioSteps = sortBy(steps, 'order');
            this._scenStepNames = steps.map(s => s.name);
            this.scenarioSteps.forEach(s => this._assign_step_meta(s));
            this.setLoading(false);
          })
        });
      });
    })
  }

  drop(event: CdkDragDrop<any[]>) {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
      const observables: Observable<ScenarioStep>[] = [];
      this.stepsLoading$.next(true);
      event.container.data.forEach((step, i) => {
        observables.push(this.rest.patchScenarioStep(step, { order: i }))
      })
      forkJoin(observables).subscribe(() => {
        this.stepsLoading$.next(false);
      })
    }
    else {
      this.addStep(event.item.data.name, {
        position: event.currentIndex,
        description: event.item.data.description,
        title: event.item.data.title
      })
    }
  }

  private _assign_step_meta(scenarioStep: ScenarioStep): void {
    const step = Object.values(this.availableSteps).flat().find(s => s.name === scenarioStep.name);
    if (step) {
      scenarioStep.title = step.title;
      scenarioStep.description = step.description;
      scenarioStep.group = step.group;
      scenarioStep.required = step.required;
      scenarioStep.injectables = step.injectables;
    }
  }

  addStep(stepName: string, options?:{ position?: number, description?: string, title?: string }) {
    this._scenStepNames.push(stepName);
    this.rest.addScenarioStep(stepName, options?.position || 1, this.settings.activeScenario$.value!).subscribe(created => {
      this._assign_step_meta(created);
      this.scenarioSteps.splice(options?.position || 0, 0, created);
    })
  }

  removeStep(step: ScenarioStep): void {
    this.rest.deleteScenarioStep(step).subscribe(() => {
      const idx = this.scenarioSteps.indexOf(step);
      this.scenarioSteps.splice(idx, 1);
    });
  }

  getInjectables(step: ScenarioStep): ScenarioInjectable[] {
    return this.injectables.filter(inj => step.injectables?.includes(inj.name));
  }

  toggleActive(active: boolean, step: ScenarioStep) {
    this.stepsLoading$.next(true);
    this.rest.patchScenarioStep(step, { active: active }).subscribe(patched => {
        step.active = patched.active;
      this.stepsLoading$.next(false);
      })
  }

  run() {
    const scenario = this.settings.activeScenario$.value;
    if (!scenario) return;
    this.rest.startRun(scenario).subscribe();
  }
}
