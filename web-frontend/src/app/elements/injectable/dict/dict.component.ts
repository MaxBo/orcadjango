import { Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";

@Component({
  selector: 'inj-dict',
  templateUrl: './dict.component.html',
  styleUrls: ['./dict.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class DictComponent extends BaseInjectableComponent implements OnInit {
  @Input() value!: Record<string, any>;
  @Input() keysEditable = false;
  keys: string[] = [];
  values: any[] = [];
  protected JSON = JSON;

  ngOnInit() {
    this.keys = Object.keys(this.value);
    this.values = Object.values(this.value);
  }

  onValueChanged(key: string, value: any, index: number) {
    this.keys[index] = key;
    this.values[index] = String(value);
    const dict = Object.fromEntries(this.keys.map((e, i) => [e, this.values[i]]));
    this.valueChanged.emit(dict);
  }
}
