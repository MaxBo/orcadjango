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
import { InjectablesComponent } from './pages/injectables/injectables.component';
import { InjectableEditDialogComponent } from './pages/injectables/edit/injectable-edit.component';
import { FormsModule } from '@angular/forms';
import { MatMenuModule } from "@angular/material/menu";
import { StepsComponent } from './pages/steps/steps.component';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatExpansionModule } from "@angular/material/expansion";
import { MatSlideToggleModule } from "@angular/material/slide-toggle";
import { InjectableComponent } from './elements/injectable/injectable.component';
import { MatCheckboxModule } from "@angular/material/checkbox";
import { MultipleChoiceComponent } from './elements/injectable/multiple-choice/multiple-choice.component';
import { BaseTypeComponent } from './elements/injectable/base-type/base-type.component';
import { DictComponent } from './elements/injectable/dict/dict.component';
import { MatDividerModule } from "@angular/material/divider";
import { GeometryComponent } from './elements/injectable/geometry/geometry.component';
import { MatButtonToggleModule } from "@angular/material/button-toggle";
import { DerivedInjectableDialogComponent } from './pages/injectables/derived/derived-injectable.component';
import { ScenarioLogComponent } from './elements/log/scenario-log.component';
import { UserPreviewComponent } from './pages/projects/user-preview/user-preview.component';
import { ProfileComponent } from './pages/profile/profile.component';
import { ColorPickerModule } from "ngx-color-picker";
import { DateComponent } from './elements/injectable/date/date.component';
import { MatDatepickerModule } from "@angular/material/datepicker";
import { MatNativeDateModule } from '@angular/material/core';
import { DateAdapter, MAT_DATE_FORMATS, MAT_DATE_LOCALE } from '@angular/material/core';
import { MomentDateAdapter } from '@angular/material-moment-adapter';
import { MaterialCssVarsModule } from 'angular-material-css-vars';
import { ScenarioStatusPreviewComponent } from './pages/scenarios/scenario-status-preview/scenario-status-preview.component';
import { MatTooltipModule } from "@angular/material/tooltip";
import { MatRadioModule } from "@angular/material/radio";
import { VarDirective } from "./var.directive";
import { SimpleDialogComponent } from "./elements/simple-dialog/simple-dialog.component";
import { SingleChoiceComponent } from './elements/injectable/single-choice/single-choice.component';
import { MatTableModule } from "@angular/material/table";
import { MatSortModule } from "@angular/material/sort";

const DATE_FORMAT = {
  parse: {
    dateInput: 'DD.MM.YYYY',
  },
  display: {
    dateInput: 'DD.MM.YYYY',
    monthYearLabel: 'MMMM YYYY',
    dateA11yLabel: 'LL',
    monthYearA11yLabel: 'MMMM YYYY'
  }
};

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
    SimpleDialogComponent,
    ScenarioGridViewComponent,
    ScenarioListViewComponent,
    ScenarioEditDialogComponent,
    InjectablesComponent,
    InjectableEditDialogComponent,
    StepsComponent,
    InjectableComponent,
    MultipleChoiceComponent,
    BaseTypeComponent,
    DictComponent,
    GeometryComponent,
    DerivedInjectableDialogComponent,
    ScenarioLogComponent,
    UserPreviewComponent,
    ProfileComponent,
    DateComponent,
    ScenarioStatusPreviewComponent,
    VarDirective,
    SingleChoiceComponent
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
    MatSelectModule,
    FormsModule,
    MatMenuModule,
    DragDropModule,
    MatExpansionModule,
    MatSlideToggleModule,
    MatCheckboxModule,
    MatDividerModule,
    MatButtonToggleModule,
    ColorPickerModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MaterialCssVarsModule.forRoot({
      isAutoContrast: true
    }),
    MatTooltipModule,
    MatRadioModule,
    MatTableModule,
    MatSortModule
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: TokenInterceptor, multi: true },
    { provide: DateAdapter, useClass: MomentDateAdapter, deps: [MAT_DATE_LOCALE] },
    { provide: MAT_DATE_FORMATS, useValue: DATE_FORMAT }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
