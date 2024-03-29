import { Component, OnInit } from '@angular/core';
import { AuthService } from "../../auth.service";
import { FormBuilder, FormGroup } from "@angular/forms";
import { ActivatedRoute, Router } from "@angular/router";
import { SettingsService } from "../../settings.service";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  next: string = '';
  constructor(private formBuilder: FormBuilder, protected auth: AuthService, protected settings: SettingsService,
              private router: Router,  private route: ActivatedRoute) {
    this.loginForm = this.formBuilder.group({
      username: '',
      password: ''
    });
  }
  ngOnInit() {
    this.route.queryParams.subscribe(params => {
        this.next = params['next'];
      }
    );
  }

  onSubmit() {
    let password = this.loginForm.value.password;
    let username = this.loginForm.value.username;
    this.auth.login({ username: username, password: password }).subscribe({
      next: value => {
        this.router.navigate([this.next || '/']);
      },
      error: error => {
        const msg = (error.status === 0)? $localize `Server does not answer`: $localize `User and password do not match`;
        this.loginForm.setErrors({ 'error': msg })
      }
    });
  }
}
