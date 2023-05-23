import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BaseTypeComponent } from './base-type.component';

describe('BaseInjectableComponent', () => {
  let component: BaseTypeComponent;
  let fixture: ComponentFixture<BaseTypeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BaseTypeComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(BaseTypeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
