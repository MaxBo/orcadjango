import { Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";

interface Choice {
  name: string;
  description?: string;
  checked: boolean;
}

@Component({
  selector: 'multiple-choice',
  templateUrl: './multiple-choice.component.html',
  styleUrls: ['./multiple-choice.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class MultipleChoiceComponent extends BaseInjectableComponent implements OnInit {
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() values: any[] = [];
  @Input() showStringFilter = true;
  protected data: Choice[] = [];
  protected columns: string[] = [];
  protected checked: boolean[] = [];
  protected active: boolean[] = [];
  protected filterString = '';
  protected filterChecked = false;

  protected readonly Object = Object;

  ngOnInit() {
    this.checked = this.choices.map(c => this.values.indexOf(c) > -1);
    this.active = Array(this.choices.length).fill(true);
    this.data = this.choices.map((choice, i) => {return { name: choice, description: this.choiceLabels? this.choiceLabels[i] || '-': undefined, checked: this.values.indexOf(choice) > -1 }});
    this.columns = ['checked', 'name'];
    if (this.choiceLabels) this.columns.push('description');
  }

  onValueChanged(value: boolean, index: number){
    this.checked[index] = value;
    let values: any[] = [];
    this.checked.forEach((c, i) => {
      if (c) values.push(this.choices[i]);
    });
    if (this.filterChecked)
      this.filterEntries();
    this.valueChanged.emit(values);
  }

  filterEntries(): void {
    if (!this.filterString && !this.filterChecked)
      this.active = Array(this.choices.length).fill(true);
    this.active = this.choices.map((c, i) => (!this.filterChecked || this.checked[i]) && String(c).includes(this.filterString));
  }
}
