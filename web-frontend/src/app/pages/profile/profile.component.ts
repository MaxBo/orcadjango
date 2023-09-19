import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { SettingsService } from "../../settings.service";
import { Avatar, RestService, User } from "../../rest-api";
import { PageComponent } from "../../app.component";

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent extends PageComponent implements OnInit {
  accountForm!: FormGroup;
  passwordForm!: FormGroup;
  colorSelection: string = 'black';
  avatarSelection: number = -1;
  changePassword: boolean = false;
  showAccountPassword: boolean = false;
  showConfirmPassword: boolean = false;

  constructor(private formBuilder: FormBuilder, protected settings: SettingsService, private rest: RestService) {
    super();
  }

  ngOnInit() {
    this.subscriptions.push(this.settings.user$.subscribe(user => {
      this.fillForms(user)
    }));
  }

  fillForms(user: User | undefined) {
    this.accountForm = this.formBuilder.group({
      username: user?.username || '',
      firstName: user?.first_name || '',
      lastName: user?.last_name || ''
    });
    this.passwordForm = this.formBuilder.group({
      password: new FormControl({ value: '', disabled: !this.changePassword }),
      confirmPass: new FormControl({ value: '', disabled: !this.changePassword })
    });
    this.colorSelection = user?.profile.color || 'black';
    this.avatarSelection = user?.profile.avatar || -1;
  }

  onTogglePassChange(checked: boolean) {
    this.changePassword = checked;
    if (checked){
      this.passwordForm.controls['password'].enable();
      this.passwordForm.controls['confirmPass'].enable();
    }
    else {
      this.passwordForm.controls['password'].disable();
      this.passwordForm.controls['confirmPass'].disable();
    }
  }

  confirm() {
    const userId = this.settings.user$.value?.id;
    if (userId == undefined) return;
    this.accountForm.markAllAsTouched();
    if (this.accountForm.invalid) return;
    let data: any = {
      username: this.accountForm.value.username,
      first_name: this.accountForm.value.firstName,
      last_name: this.accountForm.value.lastName,
      profile: { color: this.colorSelection }
    }
    if (this.changePassword) {
      this.passwordForm.markAllAsTouched();
      if (this.passwordForm.invalid) return;
      let pass = this.passwordForm.value.password;
      if (pass != this.passwordForm.value.confirmPass) {
        alert('The passwords do not match!');
        return;
      }
      data.password = pass;
    }
    if (this.avatarSelection > -1)
      data.profile.avatar = this.avatarSelection
    this.rest.patchUser(userId, data).subscribe(user => {
      window.location.reload();
    })
  }

  getAvatarTooltip(avatar: Avatar) {
    let tooltip = avatar.name;
    if (avatar.users.length > 0) {
      tooltip += ` (used by: ${avatar.users.map(id => this.settings.getUser(id)?.username).join(', ')})`;
    }
    else
      tooltip += ' (not in use)'
    return tooltip;
  }
}
