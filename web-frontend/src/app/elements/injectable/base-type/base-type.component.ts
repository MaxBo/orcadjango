import { Component, Input, OnInit } from '@angular/core';
import { BaseInputComponent } from "../injectable.component";

@Component({
  selector: 'base-type',
  templateUrl: './base-type.component.html',
  styleUrls: ['./base-type.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class BaseTypeComponent extends BaseInputComponent implements OnInit {
  @Input() value!: number | string | boolean;
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() step = 1;
  @Input() type?:  'str' | 'bool' | 'int' | 'float' | 'choice';

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
  }
}
