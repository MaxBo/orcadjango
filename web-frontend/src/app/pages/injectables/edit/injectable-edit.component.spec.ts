import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InjectableEditDialogComponent } from './injectable-edit.component';

describe('InjectableEditComponent', () => {
  let component: InjectableEditDialogComponent;
  let fixture: ComponentFixture<InjectableEditDialogComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ InjectableEditDialogComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InjectableEditDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
