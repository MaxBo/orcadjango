import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ScenarioListViewComponent } from './scenario-list-view.component';

describe('ListViewComponent', () => {
  let component: ScenarioListViewComponent;
  let fixture: ComponentFixture<ScenarioListViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ScenarioListViewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ScenarioListViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
