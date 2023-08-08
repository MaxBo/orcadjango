import { Component, Input, OnInit } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";
import * as moment from 'moment';

@Component({
  selector: 'inj-date',
  templateUrl: './date.component.html',
  styleUrls: ['./date.component.scss'],
  inputs: ['edit'],
  outputs: ['valueChanged']
})
export class DateComponent extends BaseInjectableComponent implements OnInit {
  @Input() value!: string;
  @Input() inputFormat: string = 'YYYY-MM-DD';
  // ToDo: put date format in environment settings
  @Input() outputFormat: string = 'DD.MM.YYYY';
  protected date = new Date();

  ngOnInit(): void {
    this.date = new Date(this.value);
  }

  toRepr(): string {
    return moment(this.date).format(this.outputFormat);
  }

  onValueChanged(): void {
    this.valueChanged.emit(moment(this.date).format(this.inputFormat));
  }
}
