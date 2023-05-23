import { Component, Input } from '@angular/core';
import { BaseInputComponent } from "../injectable.component";

@Component({
  selector: 'dict',
  templateUrl: './dict.component.html',
  styleUrls: ['./dict.component.scss']
})
export class DictComponent extends BaseInputComponent {
  @Input() keys!: string[];
  @Input() values!: string[];

  onValueChanged(key: string, value: any, index: number) {
    this.values[index] = key;
    this.values[index] = String(value);
  }
}
