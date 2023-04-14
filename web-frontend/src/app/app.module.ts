import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {
  HTTP_INTERCEPTORS,
  HttpClientModule
} from '@angular/common/http';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { MatSidenavModule } from "@angular/material/sidenav";
import { MatToolbarModule } from "@angular/material/toolbar";
import { RouterOutlet } from "@angular/router";
import { ProjectsComponent } from './pages/projects/projects.component';
import { ProjectListViewComponent } from './pages/projects/list-view/project-list-view.component';
import { ProjectGridViewComponent } from './pages/projects/grid-view/project-grid-view.component';
import { LoginComponent } from './pages/login/login.component';
import { MatFormFieldModule } from "@angular/material/form-field";
import { ReactiveFormsModule } from "@angular/forms";
import { MatInputModule } from "@angular/material/input";
import { MatButtonModule } from "@angular/material/button";
import { WelcomeComponent } from './pages/welcome/welcome.component';
import { TokenInterceptor } from "./auth.service";
import { ScenariosComponent } from './pages/scenarios/scenarios.component';
import { MatIconModule } from "@angular/material/icon";
import { MatCardModule } from '@angular/material/card';
import { FlexLayoutModule } from "@angular/flex-layout";
import { ProjectEditDialogComponent } from './pages/projects/edit/project-edit.component';
import { MatDialogModule } from "@angular/material/dialog";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";
import { MatSelectModule } from "@angular/material/select";
import { ConfirmDialogComponent } from './elements/confirm-dialog/confirm-dialog.component';
import { ScenarioGridViewComponent } from './pages/scenarios/grid-view/scenario-grid-view.component';
import { ScenarioListViewComponent } from './pages/scenarios/list-view/scenario-list-view.component';
import { ScenarioEditDialogComponent } from './pages/scenarios/edit/scenario-edit.component';

@NgModule({
  declarations: [
    AppComponent,
    ProjectsComponent,
    ProjectListViewComponent,
    ProjectGridViewComponent,
    LoginComponent,
    WelcomeComponent,
    ScenariosComponent,
    ProjectEditDialogComponent,
    ConfirmDialogComponent,
    ScenarioGridViewComponent,
    ScenarioListViewComponent,
    ScenarioEditDialogComponent
  ],
    imports: [
        BrowserModule,
        AppRoutingModule,
        BrowserAnimationsModule,
        MatSidenavModule,
        MatToolbarModule,
        RouterOutlet,
        HttpClientModule,
        MatFormFieldModule,
        ReactiveFormsModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        FlexLayoutModule,
        MatDialogModule,
        MatProgressSpinnerModule,
        MatSelectModule
    ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
