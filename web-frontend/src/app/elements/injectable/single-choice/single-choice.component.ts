import { Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";

@Component({
  selector: 'single-choice',
  templateUrl: './single-choice.component.html',
  styleUrls: ['./single-choice.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class SingleChoiceComponent extends BaseInjectableComponent implements OnInit{
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() value: any;
  protected _value: any;

  protected readonly Object = Object;

  ngOnInit() {
    this._value = this.value;
  }

  onValueChanged(){
    this.valueChanged.emit(this._value);
  }
}
