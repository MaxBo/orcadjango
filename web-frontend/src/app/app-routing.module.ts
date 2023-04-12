import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ProjectsComponent } from "./pages/projects/projects.component";
import { LoginComponent } from "./pages/login/login.component";
import { AuthGuard } from "./auth.service";
import { WelcomeComponent } from "./pages/welcome/welcome.component";
import { ScenariosComponent } from "./pages/scenarios/scenarios.component";


const routes: Routes = [
   {
    path: '',
    component: WelcomeComponent,
    canActivate: [AuthGuard],
    pathMatch: 'full'
  },
  {
    path: 'login',
    component: LoginComponent,
    pathMatch: 'full'
  },
  {
    path: 'projects',
    component: ProjectsComponent,
    canActivate: [AuthGuard],
    pathMatch: 'full'
  },
  {
    path: 'scenarios',
    component: ScenariosComponent,
    canActivate: [AuthGuard],
    pathMatch: 'full'
  },
]

@NgModule({
  imports: [RouterModule.forRoot(routes, { onSameUrlNavigation: 'reload' })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
