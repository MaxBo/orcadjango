import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioStatusPreviewComponent } from './scenario-status-preview.component';

describe('ScenarioStatusPreviewComponent', () => {
  let component: ScenarioStatusPreviewComponent;
  let fixture: ComponentFixture<ScenarioStatusPreviewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioStatusPreviewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ScenarioStatusPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
