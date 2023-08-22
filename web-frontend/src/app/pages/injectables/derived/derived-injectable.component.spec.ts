import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DerivedInjectableDialogComponent } from './derived-injectable.component';

describe('DerivedInjectableComponent', () => {
  let component: DerivedInjectableDialogComponent;
  let fixture: ComponentFixture<DerivedInjectableDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DerivedInjectableDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DerivedInjectableDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
