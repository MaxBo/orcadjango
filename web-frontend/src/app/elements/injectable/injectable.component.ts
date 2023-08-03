import { Component, EventEmitter, Injectable, Input, OnInit, Output } from '@angular/core';
import { Inj } from "../../rest-api";

@Injectable()
export abstract class BaseInjectableComponent {
  @Input() edit = false;
  @Output() valueChanged = new EventEmitter<any>();
}

@Component({
  selector: 'injectable',
  templateUrl: './injectable.component.html',
  styleUrls: ['./injectable.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class InjectableComponent extends BaseInjectableComponent implements OnInit {
  choiceValues?: any[];
  choiceLabels?: string[];
  multipleChoice: boolean = false;
  protected values: any[] = [];
  protected Object = Object;
  @Input() injectable!: Inj;

  ngOnInit(): void {
    this.multipleChoice = (!!this.injectable.choices && this.injectable.multi) || false;
    if (!this.injectable.multi)
      this.values = [this.injectable.value];
    else {
      if (typeof(this.injectable.value) === 'string')
        this.values = this.injectable.value.split(',')
      else
        this.values = this.injectable.value || [];
    }
    if (this.injectable.choices) {
      if (Array.isArray(this.injectable.choices)) {
        this.choiceValues = this.injectable.choices;
      }
      else {
        this.choiceValues = Object.keys(this.injectable.choices);
        this.choiceLabels = Object.values(this.injectable.choices);
      }
    }
  }

  listValueChanged(index: number, value: any): void {
    this.values[index] = value;
    this.valueChanged.emit(this.values);
  }

  appendListValue(value?: any): void {
    this.values.push(value);
    this.valueChanged.emit(this.values);
  }

  removeListValue(index: number): void {
    this.values.splice(index, 1);
    this.valueChanged.emit(this.values);
  }
}
