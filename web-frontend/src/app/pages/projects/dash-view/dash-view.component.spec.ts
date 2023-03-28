import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashViewComponent } from './dash-view.component';

describe('DashViewComponent', () => {
  let component: DashViewComponent;
  let fixture: ComponentFixture<DashViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DashViewComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DashViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
