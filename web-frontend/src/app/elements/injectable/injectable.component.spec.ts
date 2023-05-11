import { ComponentFixture, TestBed } from '@angular/core/testing';

import { InjectableComponent } from './injectable.component';

describe('InjectableComponent', () => {
  let component: InjectableComponent;
  let fixture: ComponentFixture<InjectableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ InjectableComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(InjectableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
