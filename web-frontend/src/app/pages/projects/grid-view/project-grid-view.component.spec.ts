import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectGridViewComponent } from './project-grid-view.component';

describe('DashViewComponent', () => {
  let component: ProjectGridViewComponent;
  let fixture: ComponentFixture<ProjectGridViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ProjectGridViewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProjectGridViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
