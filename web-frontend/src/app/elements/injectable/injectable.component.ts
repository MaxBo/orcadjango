import { Component, EventEmitter, Injectable, Input, OnInit, Output } from '@angular/core';
import { Inj, User } from "../../rest-api";

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
  protected _injectable?: Inj;
  @Input() height?: string;
  @Input()
  set injectable(injectable: Inj) {
    setTimeout(() => this._injectable = undefined);
    setTimeout(() => this._injectable = injectable);
    this._injectable = injectable;
    this.init();
  }

  ngOnInit(): void {
    this.init();
  }

  init(): void {
    this.multipleChoice = (!!this._injectable?.choices && this._injectable.multi) || false;
    if (!this._injectable?.multi)
      this.values = [this._injectable?.value];
    else {
      if (typeof(this._injectable.value) === 'string')
        this.values = this._injectable.value.split(',')
      else
        this.values = this._injectable.value || [];
    }
    if (this._injectable?.choices) {
      if (Array.isArray(this._injectable.choices)) {
        this.choiceValues = this._injectable.choices;
      }
      else {
        this.choiceValues = Object.keys(this._injectable.choices);
        this.choiceLabels = Object.values(this._injectable.choices);
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
