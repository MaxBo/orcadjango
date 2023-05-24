import { Component, Input, OnInit } from '@angular/core';
import { BaseInputComponent } from "../injectable.component";

@Component({
  selector: 'multiple-choice',
  templateUrl: './multiple-choice.component.html',
  styleUrls: ['./multiple-choice.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class MultipleChoiceComponent extends BaseInputComponent implements OnInit {
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() values: any[] = [];
  protected checked: boolean[] = [];

  protected readonly Object = Object;

  ngOnInit() {
    this.checked = this.choices.map(c => this.values.indexOf(c) > -1);
  }

  onValueChanged(value: boolean, index: number){
    this.checked[index] = value;
    let values: any[] = [];
    this.checked.forEach((c, i) => {
      if (c) values.push(this.choices[i]);
    });
    this.valueChanged.emit(values);
  }
}
