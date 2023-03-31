import { Component, OnInit } from '@angular/core';
import { AuthService } from "../../auth.service";
import { FormBuilder, FormGroup } from "@angular/forms";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})

export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  constructor(private formBuilder: FormBuilder, public auth: AuthService) {
    this.loginForm = this.formBuilder.group({
      username: '',
      password: ''
    });
  }
  ngOnInit() {
  }

  onSubmit() {
    let password = this.loginForm.value.password;
    let username = this.loginForm.value.username;
    this.auth.login(username, password);
  }
}
