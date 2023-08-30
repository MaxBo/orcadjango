import { Component, ElementRef, ViewChild } from '@angular/core';
import { ScenarioInjectable, ScenarioStep, Step } from "../../rest-api";
import { CdkDragDrop, CdkDropList, moveItemInArray } from "@angular/cdk/drag-drop";
import { InjectablesComponent, sortBy } from "../injectables/injectables.component";
import { BehaviorSubject, forkJoin, Observable, Subscription } from "rxjs";

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
  protected activeStepsCount = 0;
  stepsLoading$ = new BehaviorSubject<boolean>(false);
  protected logHeight = 130;

  @ViewChild('resizeHandle') resizeHandle!: ElementRef;
  @ViewChild('logContainer') logContainer!: ElementRef;
  @ViewChild('scenarioStepList') scenarioStepList!: CdkDropList;

  // constructor(private rest: RestService, private settings: UserSettingsService)
  override ngOnInit() {
    this.subscriptions.push(this.settings.activeScenario$.subscribe(scenario => {
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
            this.updateActiveStepsCount();
            this.scenarioSteps.forEach(s => this._assign_step_meta(s));
            this.connectWs();
            this.setLoading(false);
          })
        });
      });
    }));
  }

  updateActiveStepsCount(): void {
    this.activeStepsCount = this.scenarioSteps.filter(s => s.active).length;
  }

  drop(event: CdkDragDrop<any[]>) {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
      this._updateStepsOrder();
    }
    else {
      this.addStep(event.item.data.name, {
        position: event.currentIndex,
        description: event.item.data.description,
        title: event.item.data.title
      })
    }
  }

  _updateStepsOrder(): void {
    const observables: Observable<ScenarioStep>[] = [];
    this.stepsLoading$.next(true);
    this.scenarioStepList.data.forEach((step: ScenarioStep, i: number) => {
      observables.push(this.rest.patchScenarioStep(step, { order: i }))
    })
    forkJoin(observables).subscribe(() => {
      this.stepsLoading$.next(false);
    })
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
      this._updateStepsOrder();
    })
  }

  removeStep(step: ScenarioStep): void {
    this.rest.deleteScenarioStep(step).subscribe(() => {
      const idx = this.scenarioSteps.indexOf(step);
      this.scenarioSteps.splice(idx, 1);
      const nameIdx = this._scenStepNames.indexOf(step.name);
      this._scenStepNames.splice(nameIdx, 1);
    });
  }

  getInjectables(step: ScenarioStep): ScenarioInjectable[] {
    return this.injectables.filter(inj => step.injectables?.includes(inj.name));
  }

  toggleActive(active: boolean, step: ScenarioStep): void {
    this.stepsLoading$.next(true);
    this.rest.patchScenarioStep(step, { active: active }).subscribe(patched => {
      step.active = patched.active;
      this.updateActiveStepsCount();
      this.stepsLoading$.next(false);
    })
  }

  run(): void {
    const scenario = this.settings.activeScenario$.value;
    if (!scenario) return;
    this.rest.startRun(scenario).subscribe(() => {
      // backend does some status updates on steps when starting a run => update local steps
      this.rest.getScenarioSteps(scenario).subscribe(steps => {
        steps.forEach(updatedStep => {
          const step = this.scenarioSteps.find(s => s.name === updatedStep.name);
          if (step)
            Object.assign(step, updatedStep);
        })
        this.updateActiveStepsCount();
      })
    });
  }

  abort(): void {
    const scenario = this.settings.activeScenario$.value;
    if (!scenario) return;
    this.rest.abortRun(scenario).subscribe();
  }

  connectWs(): void {
    this.settings.onStepStatusChange.subscribe(status => {
      const step = this.scenarioSteps.find(step => step.name === status.step);
      if (!step) return;
      if (status.started) {
        step.started = status.timestamp;
        step.finished = undefined;
      }
      if (status.finished) {
        step.finished = status.timestamp;
      }
      if (status.success !== undefined) {
        step.success = status.success;
        if (step.success)
          step.active = false;
      }
    })
  }

  onResizeDrag(event: any): void {
    const dragRect = this.resizeHandle.nativeElement.getBoundingClientRect();
    const targetRect = this.logContainer.nativeElement.getBoundingClientRect();
    const diffY = dragRect.top - targetRect.top + dragRect.height;
    this.resizeHandle.nativeElement.style.transform  = `translate3d(0, ${this.logHeight-diffY-targetRect.height}px, 0)`;
    this.logContainer.nativeElement.style.height = `${this.logHeight-diffY}px`;
    // cancel drag if drag handle is pulled to the bottom of the page (otherwise it would go up again)
    if (targetRect.height < 15 && event.delta.y > 0) {
      document.dispatchEvent(new Event('mouseup'));
    }
  }

}
