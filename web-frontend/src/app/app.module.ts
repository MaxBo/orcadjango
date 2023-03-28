import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HttpClientXsrfModule } from '@angular/common/http';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatSidenavModule } from "@angular/material/sidenav";
import { MatToolbarModule } from "@angular/material/toolbar";
import { RouterOutlet } from "@angular/router";
import { ProjectsComponent } from './pages/projects/projects.component';
import { ListViewComponent } from './pages/projects/list-view/list-view.component';
import { DashViewComponent } from './pages/projects/dash-view/dash-view.component';

@NgModule({
  declarations: [
    AppComponent,
    ProjectsComponent,
    ListViewComponent,
    DashViewComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    MatSidenavModule,
    MatToolbarModule,
    RouterOutlet,
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'csrftoken',
      headerName: 'X-CSRFTOKEN',
    }),
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
