import { Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";

@Component({
  selector: 'inj-base-type',
  templateUrl: './base-type.component.html',
  styleUrls: ['./base-type.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class BaseTypeComponent extends BaseInjectableComponent implements OnInit {
  @Input() value!: number | string | boolean;
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() step = 0.01;
  @Input() type?:  'str' | 'bool' | 'int' | 'float' | 'choice' | 'dataframe' | 'dataset';

  ngOnInit() {
    if (!this.type) {
      if (this.choices)
        this.type = 'choice'
      else switch (typeof this.value) {
        case 'number':
          this.type = (this.step <= 1)? 'float': 'int';
          break;
        case 'boolean':
          this.type = 'bool'
          break;
        default:
          this.type = 'str'
      }
    }
    // force integer as input if type is determined as int
    if (this.type === 'int') {
      this.value = Math.round(Number(this.value));
      this.step = Math.ceil(this.step);
    }
    // ToDo: make own injectable components for these types
    if (this.type === 'dataframe' || this.type === 'dataset')
      this.value = JSON.stringify(this.value);
  }
}
