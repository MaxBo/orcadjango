import { Component, Input, OnInit } from '@angular/core';
import { BaseInputComponent } from "../injectable.component";

@Component({
  selector: 'dict',
  templateUrl: './dict.component.html',
  styleUrls: ['./dict.component.scss'],
  outputs: ['valueChanged']
})
export class DictComponent extends BaseInputComponent implements OnInit {
  @Input() dict!: Record<string, any>;
  keys: string[] = [];
  values: any[] = [];

  ngOnInit() {
    this.keys = Object.keys(this.dict);
    this.values = Object.values(this.dict);
  }

  onValueChanged(key: string, value: any, index: number) {
    this.keys[index] = key;
    this.values[index] = String(value);
    const dict = Object.fromEntries(this.keys.map((e, i) => [e, this.values[i]]));
    this.valueChanged.emit(dict);
  }
}
