import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioGridViewComponent } from './scenario-grid-view.component';

describe('GridViewComponent', () => {
  let component: ScenarioGridViewComponent;
  let fixture: ComponentFixture<ScenarioGridViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioGridViewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ScenarioGridViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
