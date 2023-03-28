import { Component, OnInit } from '@angular/core';
import { RestService } from "../../rest-api";

@Component({
  selector: 'app-projects',
  templateUrl: './projects.component.html',
  styleUrls: ['./projects.component.scss']
})
export class ProjectsComponent implements OnInit{
  constructor(private rest: RestService) {}

  ngOnInit() {
    this.rest.getProjects().subscribe(projects => console.log(projects));
  }
}
