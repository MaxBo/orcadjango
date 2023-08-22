import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioEditDialogComponent } from './scenario-edit.component';

describe('EditComponent', () => {
  let component: ScenarioEditDialogComponent;
  let fixture: ComponentFixture<ScenarioEditDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioEditDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ScenarioEditDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
