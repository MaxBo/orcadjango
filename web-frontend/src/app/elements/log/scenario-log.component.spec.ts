import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioLogComponent } from './scenario-log.component';

describe('LogComponent', () => {
  let component: ScenarioLogComponent;
  let fixture: ComponentFixture<ScenarioLogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioLogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ScenarioLogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
