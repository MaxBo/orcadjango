import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Inj } from "../../rest-api";
/*
function deserialize(injectable: Inj): any[] {
  let values = [];

  switch (injectable.datatype) {
    case 'int':
      deserialized[0] = Math.round(Number(injectable.value));
      break;
    case 'float':
      deserialized = Number(injectable.value);
      break;
    default:
      deserialized = injectable.value;
  }
  return deserialized;
}*/

@Component({
  selector: 'injectable',
  templateUrl: './injectable.component.html',
  styleUrls: ['./injectable.component.scss']
})
export class InjectableComponent implements OnInit {
  @Input() injectable!: Inj;
  @Input() edit = false;
  @Output() valueChanged = new EventEmitter<string>();
  values: any[] = [];
  // in case of dict input
  valueKeys?: string[];
  injChoices?: Record<string, string>; //Record<string, [string, boolean]>
  choiceChecked: boolean[] = [];
  protected readonly Math = Math;

  ngOnInit(): void {
    if (this.injectable.datatype === 'dict') {
      this.valueKeys = Object.keys(this.injectable.value);
      this.values = Object.values(this.injectable.value);
    }
    else if (!this.injectable.multi)
      this.values = [this.injectable.value];
    else
      this.values = this.injectable.value || [];
    if (this.injectable.choices) {
      if (Array.isArray(this.injectable.choices)) {
        this.injChoices = Object.fromEntries(this.injectable.choices.map(c => [String(c), '']));
      }
      else
        this.injChoices = this.injectable.choices;
      if (this.injectable.multi) {
        this.choiceChecked = Object.keys(this.injChoices!).map(c => this.values.indexOf(c) > -1);
      }
    }
  }

  protected onValueChanged(event: any, options?: { index?: number }): void {
    console.log(event.target.value)
  }

}
