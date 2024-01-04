import { AfterViewInit, Component, Input, OnInit, ViewChild } from '@angular/core';
import { BaseInjectableComponent } from "../injectable.component";
import { MatTableDataSource } from "@angular/material/table";
import { MatSort } from "@angular/material/sort";

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
export class MultipleChoiceComponent extends BaseInjectableComponent implements OnInit, AfterViewInit {
  @Input() choices!: any[];
  @Input() choiceLabels?: string[];
  @Input() values: any[] = [];
  @Input() showStringFilter = true;
  @ViewChild(MatSort) sort!: MatSort;
  protected tableData!: MatTableDataSource<any>;
  protected columns: string[] = [];
  protected active: boolean[] = [];
  protected filterString = '';
  protected filterChecked = false;

  protected readonly Object = Object;

  ngOnInit() {
    this.active = Array(this.choices.length).fill(true);
    let tableData: Choice[] = this.choices.map((choice, i) => {return { name: choice, description: this.choiceLabels? this.choiceLabels[i] || '-': undefined, checked: this.values.indexOf(choice) > -1 }})
    this.tableData = new MatTableDataSource(tableData);
    this.columns = ['checked', 'name'];
    if (this.choiceLabels) this.columns.push('description');
    this.tableData.filterPredicate = (record, filter) => {
      if (this.filterChecked && !record.checked)
        return false;
      return (filter === '--override--') || String(record.name).includes(filter) || String(record.description).includes(filter);
    }
  }

  ngAfterViewInit() {
    this.tableData.sort = this.sort;
  }

  onValueChanged(value: boolean, choice: Choice){
    choice.checked = value;
    let values: any[] = [];
    this.tableData.data.forEach(d => {
      if (d.checked)
        values.push(d.name);
    })
    if (this.filterChecked)
      this.filterEntries();
    this.valueChanged.emit(values);
  }

  filterEntries(): void {
    // assign value '--override--' to force call of filterPredicate even when filter string is empty
    this.tableData.filter = this.filterString || '--override--';
  }
}
