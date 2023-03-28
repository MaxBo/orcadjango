import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ProjectsComponent } from "./pages/projects/projects.component";


const routes: Routes = [
/*  {
    path: '',
    component: WelcomeComponent,
    canActivate: [AuthGuard],
    pathMatch: 'full'
  },*/
  {
    path: 'projects',
    component: ProjectsComponent,
    pathMatch: 'full'
  },
]

@NgModule({
  imports: [RouterModule.forRoot(routes, {onSameUrlNavigation: 'reload'})],
  exports: [RouterModule]
})
export class AppRoutingModule { }
