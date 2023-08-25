import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { SettingsService } from "../../settings.service";
import { RestService, User } from "../../rest-api";
import { PageComponent } from "../../app.component";

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent extends PageComponent implements OnInit {
  accountForm!: FormGroup;
  passwordForm!: FormGroup;
  imageSrc?: string;
  imageFile?: File;
  colorSelection: string = 'black';
  changePassword: boolean = false;
  showAccountPassword: boolean = false;
  showConfirmPassword: boolean = false;

  constructor(private formBuilder: FormBuilder, private settings: SettingsService, private rest: RestService) {
    super();
  }

  ngOnInit() {
    this.subscriptions.push(this.settings.user$.subscribe(user => {
      this.imageSrc = user?.profile.icon;
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

  onImageChange(files: FileList) {
    if (!files.length) return;
    this.imageFile = files[0];
    const reader = new FileReader();
    reader.readAsDataURL(this.imageFile);
    reader.onload = () => {
      this.imageSrc = reader.result as string;
      // this.myForm.patchValue({
      //   fileSource: reader.result
      // });
    }
  }

  confirm() {
    const userId = this.settings.user$.value?.id;
    if (userId == undefined) return;
    const formData = new FormData();
    this.accountForm.markAllAsTouched();
    if (this.accountForm.invalid) return;
    formData.append('username', this.accountForm.value.username);
    formData.append('first_name', this.accountForm.value.firstName);
    formData.append('last_name', this.accountForm.value.lastName);
    if (this.changePassword) {
      this.passwordForm.markAllAsTouched();
      if (this.passwordForm.invalid) return;
      let pass = this.passwordForm.value.password;
      if (pass != this.passwordForm.value.confirmPass) {
        alert('The passwords do not match!');
        return;
      }
      formData.append('password', pass);
    }
    formData.append('profile[color]', this.colorSelection);
    if (this.imageFile)
      formData.append('profile[icon]', this.imageFile);
    this.rest.patchUser(userId, formData).subscribe(user => {
      // this.settings.user$.next(user);
      window.location.reload();
    })
  }
}
